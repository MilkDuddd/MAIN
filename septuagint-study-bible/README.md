# Septuagint Study Bible

A study Bible built around the **Septuagint (LXX)** — the ancient Greek Old
Testament — with the **complete Greek text and a parallel English translation**,
original **commentary**, Greek **word studies**, and your own **notes,
highlights, and bookmarks**.

It is a single, dependency-free web app. There is nothing to install and no
server to run: **just open `index.html` in a browser.**

<p align="center"><em>“Ἡ μετάφρασις τῶν Ἑβδομήκοντα” — the translation of the Seventy.</em></p>

## What's inside

- **The whole LXX** — 52 books, ~28,600 verses, including all the
  deuterocanonical / *anagignōskomena* books (Tobit, Judith, Wisdom, Sirach,
  Baruch, the Epistle of Jeremiah, Susanna, Bel and the Dragon, 1–4 Maccabees,
  1 Esdras, the Prayer of Manasseh) and the LXX's own versification
  (Psalm 151, Greek Daniel, Greek Esther, the one-behind Psalm numbering, …).
- **Parallel Greek + English**, with one click to switch to Greek-only or
  English-only reading.
- **Study drawer on every verse:** commentary on the key passages, explicit
  **LXX ↔ Hebrew (Masoretic)** difference notes, **New-Testament usage** of the
  Greek, linked **Greek word studies**, and a place for your own note.
- **Personal study, saved locally:** notes, five highlight colors, and
  bookmarks — all stored in your browser (`localStorage`) with **JSON
  export/import** so you can back them up or move them between machines.
- **Full-text search** across the Greek, the English, and the commentary
  (diacritic- and case-insensitive).
- **Reader comforts:** light / sepia / dark themes, adjustable text and Greek
  sizes, keyboard navigation (`←`/`→` chapters, `/` search, `Esc` close),
  deep-linkable references (`#/ISA/7/14`), and a mobile-friendly layout.

## Run it

```
# simplest — just open the file
open septuagint-study-bible/index.html        # macOS
xdg-open septuagint-study-bible/index.html     # Linux
# or double-click index.html
```

The app injects each book's data file on demand, which works directly from
`file://`. If your browser is configured to block local file scripts, serve the
folder instead:

```
cd septuagint-study-bible
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Key passages for LXX study

The home page links straight to the passages where the Septuagint matters most:
Genesis 1; Exodus 3:14 (*ἐγώ εἰμι ὁ Ὤν*, "I AM THE BEING"); the mercy-seat
(*ἱλαστήριον*, Lev 16); the Shema (Deut 6); the passion and shepherd psalms
(LXX Ps 21 / 22 / 109 = Heb 22 / 23 / 110); Isaiah 7:14 (*ἡ παρθένος*, "the
virgin"), 9:6, and 53; Jonah and the *κῆτος*; the persecuted righteous one of
Wisdom 2; the self-praise of Wisdom in Sirach 24; and the "son of man" of
Greek Daniel 7.

## Project layout

```
index.html                 App shell
assets/styles.css          Theme-aware, responsive styles
assets/app.js              Reader, study drawer, notes, search, settings
data/index.js              Book metadata (52 books, sections, counts)
data/books/<CODE>.js       Per-book Greek+English text (loaded on demand)
data/commentary.js         Book introductions + passage commentary
data/lexicon.js            Greek word studies
tools/build-data.mjs       Re-runnable parser that generates data/ from tools/raw/
tools/raw/                 Cached public-domain source texts
SOURCES.md                 Provenance and licensing (all text is PD / CC0)
```

## Rebuilding / extending the text

The `data/` files are generated from the two cached sources:

```
node tools/build-data.mjs
```

To swap in a different LXX edition, replace the files in `tools/raw/`, adjust
the parser in `tools/build-data.mjs`, and re-run. See **[SOURCES.md](SOURCES.md)**.

## Sources & license

- **Greek** — Brenton's Septuagint (1851), public domain (via the CC0
  Brenton-LXX-LaTeX print project).
- **English** — Updated Brenton English Septuagint (Adam Boyd, 2020), CC0.
- **Commentary, introductions, and word studies** — original content for this
  project.

Full details and links in **[SOURCES.md](SOURCES.md)**.
