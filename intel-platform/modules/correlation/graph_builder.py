"""Entity relationship graph builder using networkx."""

import json
from typing import Optional

from core import database
from models.correlation import GraphData

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False

# Relationship type → display color
_REL_COLORS = {
    "controls":         "#e74c3c",  # red
    "donates_to":       "#f39c12",  # orange
    "sits_on_board_of": "#3498db",  # blue
    "sanctioned_by":    "#9b59b6",  # purple
    "mentioned_with":   "#95a5a6",  # gray
    "owns":             "#e67e22",  # dark orange
    "subsidiary_of":    "#2ecc71",  # green
    "affiliated_with":  "#1abc9c",  # teal
}


def build_graph(entity_ids: Optional[list[str]] = None, depth: int = 2) -> GraphData:
    """
    Build a relationship graph.
    If entity_ids is given, build a subgraph around those entities up to `depth` hops.
    Otherwise builds the full graph (may be large).
    """
    # Fetch all or filtered entities
    if entity_ids:
        placeholders = ",".join("?" * len(entity_ids))
        entities_rows = database.execute(
            f"SELECT * FROM entities WHERE entity_id IN ({placeholders})",
            tuple(entity_ids),
        )
    else:
        entities_rows = database.execute("SELECT * FROM entities LIMIT 500")

    # Fetch relationships
    if entity_ids:
        placeholders = ",".join("?" * len(entity_ids))
        rel_rows = database.execute(
            f"SELECT * FROM relationships WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
            tuple(entity_ids) * 2,
        )
    else:
        rel_rows = database.execute("SELECT * FROM relationships LIMIT 2000")

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()

    for row in entities_rows:
        node_id = row["entity_id"]
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({
                "id": node_id,
                "label": row["canonical_name"],
                "type": row["entity_type"],
                "modules": json.loads(row["source_modules"] or "[]"),
            })

    for row in rel_rows:
        src, tgt = row["source_id"], row["target_id"]
        # Add any missing nodes
        for nid in (src, tgt):
            if nid not in seen_nodes:
                seen_nodes.add(nid)
                # Look up name
                nr = database.execute("SELECT * FROM entities WHERE entity_id=?", (nid,))
                label = nr[0]["canonical_name"] if nr else nid
                etype = nr[0]["entity_type"] if nr else "unknown"
                nodes.append({"id": nid, "label": label, "type": etype, "modules": []})

        edges.append({
            "source": src,
            "target": tgt,
            "type": row["rel_type"],
            "weight": row["confidence"],
            "color": _REL_COLORS.get(row["rel_type"], "#7f8c8d"),
        })

    return GraphData(nodes=nodes, edges=edges)


def get_networkx_graph() -> Optional[object]:
    """Return a networkx DiGraph of all entity relationships (if networkx available)."""
    if not _HAS_NX:
        return None
    gd = build_graph()
    G = nx.DiGraph()
    for node in gd.nodes:
        G.add_node(node["id"], label=node["label"], entity_type=node["type"])
    for edge in gd.edges:
        G.add_edge(edge["source"], edge["target"], rel_type=edge["type"], weight=edge["weight"])
    return G


def shortest_path(source_name: str, target_name: str) -> list[str]:
    """Find shortest relationship path between two entities."""
    if not _HAS_NX:
        return ["networkx not installed"]
    from modules.correlation.entity_resolver import fuzzy_search_entities
    src_entities = fuzzy_search_entities(source_name)
    tgt_entities = fuzzy_search_entities(target_name)
    if not src_entities or not tgt_entities:
        return []

    G = get_networkx_graph()
    src_id = src_entities[0].entity_id
    tgt_id = tgt_entities[0].entity_id
    try:
        import networkx as nx
        path_ids = nx.shortest_path(G, src_id, tgt_id)
        # Convert ids to names
        names = []
        for pid in path_ids:
            rows = database.execute("SELECT canonical_name FROM entities WHERE entity_id=?", (pid,))
            names.append(rows[0]["canonical_name"] if rows else pid)
        return names
    except Exception:
        return []
