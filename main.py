#!/usr/bin/env python3
"""
Encrypted LoRa Radio — CLI entry point.

Quick-start examples
────────────────────
# Simulate two nodes on the same machine (no hardware needed):
  NODE_ID=1 python main.py --driver sim --alias Alice --psk "my-secret"
  NODE_ID=2 python main.py --driver sim --alias Bob   --psk "my-secret"

# Real hardware (Raspberry Pi + SX1276 LoRa HAT, 915 MHz):
  NODE_ID=1 python main.py --driver sx127x --alias Alice --psk "my-secret" --freq 915

# Serial AT-command LoRa module (RYLR998 on /dev/ttyUSB0):
  NODE_ID=2 python main.py --driver serial --port /dev/ttyUSB0 --alias Bob --psk "my-secret"

# Generate a keypair and use ECDH (no PSK):
  python main.py --driver sim --alias Alice --keygen
  python main.py --driver sim --alias Alice  (loads ./keys/node-<id>.pem automatically)

Options
───────
  --driver    sx127x | serial | sim      (default: sim)
  --alias     human-readable node name
  --psk       pre-shared passphrase for symmetric encryption
  --psk-file  path to raw 32-byte PSK file (generated with --gen-psk)
  --keygen    generate X25519 keypair and save to keys/ then exit
  --gen-psk   generate a random PSK file and exit
  --freq      frequency in MHz (default 915)
  --sf        spreading factor 7-12 (default 12)
  --port      serial port (--driver serial)
  --relay     enable mesh relay (default: on)
  --no-relay  disable relay forwarding
  --log       log level: debug | info | warning (default: warning)
  --dst       default destination node ID (default: broadcast)
"""

import os
import sys
import time
import logging
import threading
import signal
import struct
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt

from config import (
    NODE_ID, NODE_ALIAS, KEYS_DIR, BROADCAST_ID,
    SX127xConfig, SerialLoRaConfig, SimulatorConfig, MeshConfig,
)
from crypto import KeyStore, NodeKeypair
from radio import make_radio
from mesh import MeshNode, Message


console = Console()


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--driver",   default="sim",     show_default=True,
              type=click.Choice(["sim", "sx127x", "serial"], case_sensitive=False),
              help="Radio driver to use.")
@click.option("--alias",    default=None,      help="Human-readable node name.")
@click.option("--node-id",  default=None,      type=int, help="Override NODE_ID.")
@click.option("--psk",      default=None,      envvar="LORA_PSK",
              help="Passphrase for pre-shared key encryption.")
@click.option("--psk-file", default=None,      type=click.Path(),
              help="Path to raw 32-byte PSK file.")
@click.option("--keygen",   is_flag=True,      help="Generate X25519 keypair and exit.")
@click.option("--gen-psk",  is_flag=True,      help="Generate random PSK file and exit.")
@click.option("--freq",     default=915.0,     show_default=True, type=float,
              help="Carrier frequency in MHz.")
@click.option("--sf",       default=12,        show_default=True,
              type=click.IntRange(7, 12),       help="Spreading factor (7–12).")
@click.option("--bw",       default=125,       show_default=True,
              type=click.Choice(["125", "250", "500"]),
              help="Bandwidth in kHz.")
@click.option("--power",    default=20,        show_default=True,
              type=click.IntRange(2, 22),       help="TX power in dBm.")
@click.option("--port",     default=None,      help="Serial port (--driver serial).")
@click.option("--relay/--no-relay", default=True, show_default=True,
              help="Enable/disable mesh relay forwarding.")
@click.option("--dst",      default=None,      type=str,
              help="Default destination node ID (hex or decimal). Default: broadcast.")
@click.option("--log",      default="warning", show_default=True,
              type=click.Choice(["debug", "info", "warning", "error"]),
              help="Log level.")
def main(
    driver, alias, node_id, psk, psk_file, keygen, gen_psk,
    freq, sf, bw, power, port, relay, dst, log,
):
    logging.basicConfig(
        level=getattr(logging, log.upper()),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    effective_node_id = node_id or NODE_ID
    effective_alias   = alias or NODE_ALIAS

    keys_dir = Path(KEYS_DIR)
    keys_dir.mkdir(parents=True, exist_ok=True)

    # ── One-shot operations ────────────────────────────────

    if gen_psk:
        ks = KeyStore()
        path = keys_dir / "psk.key"
        key = ks.generate_psk_file(str(path))
        console.print(f"[green]PSK written to {path}[/green]")
        console.print(f"[dim]Key (hex): {key.hex()}[/dim]")
        return

    if keygen:
        kp = NodeKeypair.generate()
        path = keys_dir / f"node-{effective_node_id}.pem"
        kp.save(str(path))
        console.print(f"[green]Keypair written to {path}[/green]")
        console.print(f"[dim]Public key: {kp.public_bytes.hex()}[/dim]")
        return

    # ── Key store setup ────────────────────────────────────

    if psk_file:
        keystore = KeyStore.from_key_file(psk_file)
        enc_mode = f"PSK (file: {psk_file})"
    elif psk:
        keystore = KeyStore.from_passphrase(psk)
        enc_mode = "PSK (passphrase)"
    else:
        keystore = KeyStore()
        enc_mode = "ECDH (session keys)"

    # Load saved session keys (ECDH mode)
    sessions_path = str(keys_dir / f"sessions-{effective_node_id}.json")
    keystore.load_sessions(sessions_path)

    # Load keypair if present
    keypair_path = keys_dir / f"node-{effective_node_id}.pem"
    keypair: Optional[NodeKeypair] = None
    if keypair_path.exists():
        try:
            keypair = NodeKeypair.load(str(keypair_path))
            enc_mode += " + identity keypair"
        except Exception as e:
            console.print(f"[yellow]Warning: could not load keypair: {e}[/yellow]")

    # In ECDH-only mode with no keypair, warn the user
    if not psk and not psk_file and keypair is None:
        console.print(
            "[yellow]No PSK or keypair found. "
            "Run with --psk or --keygen first for encryption.[/yellow]"
        )

    # ── Default destination ────────────────────────────────

    default_dst = BROADCAST_ID
    if dst:
        try:
            default_dst = int(dst, 0)   # accepts 0x1A or decimal
        except ValueError:
            console.print(f"[red]Invalid --dst: {dst!r}[/red]")
            sys.exit(1)

    # ── Radio driver ───────────────────────────────────────

    if driver == "sx127x":
        radio_cfg = SX127xConfig(
            frequency=freq * 1e6,
            spreading_factor=sf,
            bandwidth=int(bw) * 1000,
            tx_power=power,
        )
        radio = make_radio("sx127x", config=radio_cfg)
    elif driver == "serial":
        radio_cfg = SerialLoRaConfig(
            port=port or SerialLoRaConfig().port,
            frequency_mhz=freq,
            spreading_factor=sf,
            bandwidth_khz=int(bw),
            tx_power_dbm=power,
        )
        radio = make_radio("serial", config=radio_cfg)
    else:
        sim_cfg = SimulatorConfig()
        radio = make_radio("sim", config=sim_cfg, node_id=effective_node_id)

    mesh_cfg = MeshConfig(relay=relay)

    # ── Start node ─────────────────────────────────────────

    node = MeshNode(
        radio=radio,
        keystore=keystore,
        keypair=keypair,
        node_id=effective_node_id,
        alias=effective_alias,
        config=mesh_cfg,
    )

    with radio:
        node.start()
        _chat_ui(node, effective_node_id, effective_alias, enc_mode, default_dst)
        node.stop()

    # Save sessions on clean exit
    try:
        keystore.save_sessions(sessions_path)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────
# Chat UI
# ──────────────────────────────────────────────────────────

def _chat_ui(
    node: MeshNode,
    node_id: int,
    alias: str,
    enc_mode: str,
    default_dst: int,
) -> None:
    """
    Simple interactive chat interface.

    Commands:
      /peers          list known peers
      /ping [id]      send a ping
      /quit or /exit  exit
      /help           show commands
      Anything else is sent as a message.
    """
    _print_banner(node_id, alias, enc_mode, default_dst)

    # Background thread to print incoming messages
    stop_event = threading.Event()

    def _recv_loop():
        while not stop_event.is_set():
            msg = node.recv_message(timeout=0.5)
            if msg:
                _print_message(msg)

    recv_thread = threading.Thread(target=_recv_loop, daemon=True)
    recv_thread.start()

    # Handle Ctrl+C
    def _sigint(sig, frame):
        stop_event.set()
        console.print("\n[yellow]Exiting...[/yellow]")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    dst = default_dst

    while True:
        try:
            line = input(f"\033[32m[{alias}]\033[0m ")
        except (EOFError, KeyboardInterrupt):
            break

        line = line.strip()
        if not line:
            continue

        # Commands
        if line.startswith("/"):
            parts = line.split()
            cmd   = parts[0].lower()

            if cmd in ("/quit", "/exit", "/q"):
                break

            elif cmd == "/help":
                console.print(
                    "[bold]Commands:[/bold]\n"
                    "  /peers            — list known peers\n"
                    "  /ping [node_id]   — ping a node\n"
                    "  /dst <node_id>    — change default destination\n"
                    "  /broadcast        — send to all (default)\n"
                    "  /quit             — exit\n"
                )

            elif cmd == "/peers":
                peers = node.peers()
                if not peers:
                    console.print("[dim]No peers seen yet.[/dim]")
                else:
                    for p in peers:
                        age = int(time.time() - p.last_seen)
                        console.print(
                            f"  [cyan]{p.node_id:#010x}[/cyan] "
                            f"alias=[bold]{p.alias or '?'}[/bold] "
                            f"RSSI={p.rssi} SNR={p.snr} "
                            f"last={age}s ago"
                        )

            elif cmd == "/ping":
                target = BROADCAST_ID
                if len(parts) > 1:
                    try:
                        target = int(parts[1], 0)
                    except ValueError:
                        console.print(f"[red]Invalid node ID: {parts[1]}[/red]")
                        continue
                node.ping(target)
                console.print(f"[dim]→ ping sent to {target:#010x}[/dim]")

            elif cmd == "/dst":
                if len(parts) < 2:
                    console.print(f"[dim]Current destination: {dst:#010x}[/dim]")
                else:
                    try:
                        dst = int(parts[1], 0)
                        console.print(f"[dim]Destination set to {dst:#010x}[/dim]")
                    except ValueError:
                        console.print(f"[red]Invalid node ID: {parts[1]}[/red]")

            elif cmd == "/broadcast":
                dst = BROADCAST_ID
                console.print("[dim]Destination set to broadcast[/dim]")

            else:
                console.print(f"[red]Unknown command: {cmd}. Type /help.[/red]")

        else:
            # Send message
            try:
                node.send_message(line, dst_id=dst)
                dst_str = "broadcast" if dst == BROADCAST_ID else f"{dst:#010x}"
                console.print(f"[dim]→ sent to {dst_str}[/dim]")
            except RuntimeError as e:
                console.print(f"[red]{e}[/red]")
            except Exception as e:
                console.print(f"[red]Send failed: {e}[/red]")

    stop_event.set()
    recv_thread.join(timeout=1.0)


# ──────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────

def _print_banner(node_id: int, alias: str, enc_mode: str, dst: int) -> None:
    dst_str = "broadcast" if dst == BROADCAST_ID else f"{dst:#010x}"
    console.print(Panel(
        f"[bold cyan]Encrypted LoRa Radio[/bold cyan]\n"
        f"Node ID : [yellow]{node_id:#010x}[/yellow]  alias=[bold]{alias}[/bold]\n"
        f"Encrypt : [green]{enc_mode}[/green]\n"
        f"Default → {dst_str}\n\n"
        f"Type a message and press Enter to send.\n"
        f"Type [bold]/help[/bold] for commands.",
        title="[bold]LoRa Mesh[/bold]",
        border_style="cyan",
    ))


def _print_message(msg: Message) -> None:
    ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
    src = f"{msg.alias or f'node-{msg.src_id:#010x}'}"
    dst = "(broadcast)" if msg.dst_id == BROADCAST_ID else f"→ {msg.dst_id:#010x}"
    sig = f"RSSI={msg.rssi} SNR={msg.snr}" if msg.rssi is not None else ""
    console.print(
        f"\n[dim]{ts}[/dim] [bold cyan]{src}[/bold cyan] [dim]{dst} {sig}[/dim]\n"
        f"  {msg.text}"
    )


if __name__ == "__main__":
    main()
