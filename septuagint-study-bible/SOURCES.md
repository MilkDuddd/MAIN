# Sources & Licensing

All **scripture text** in this app is in the public domain or released under
CC0. The **commentary, book introductions, and word studies** (in
`data/commentary.js` and `data/lexicon.js`) are original editorial content
created for this project.

## Greek text — Brenton's Septuagint (Greek)

- **Source:** [`mrgreekgeek/Brenton-LXX-Latex-print-project`](https://github.com/mrgreekgeek/Brenton-LXX-Latex-print-project)
  — a print-ready (PDF) edition of Sir Lancelot C. L. Brenton's Septuagint.
- **File used:** `Brenton.tex` (cached at `tools/raw/Brenton.tex`).
- **Underlying text:** Brenton, *The Septuagint Version of the Old Testament*
  (1851) — **public domain**. The repository's code and `.tex` formatting are
  released **CC0-1.0**.

## English text — Updated Brenton English Septuagint

- **Source:** [`curran-gehring/modern-brenton-septuagint`](https://github.com/curran-gehring/modern-brenton-septuagint)
  → `data/source/verses_native.tsv` (cached at `tools/raw/eng_native.tsv`).
- **Underlying text:** the **Updated Brenton English Septuagint** by
  **Adam Boyd (2020)** — Brenton's 1851 English with vocabulary and accuracy
  updates against the Greek — released **CC0**. It is extracted directly from
  the USFM in **native LXX versification** (so Psalm 151, Greek Daniel, Greek
  Esther, 1 Esdras, the Prayer of Manasseh, and Rahlfs lettered verses are all
  present and align with the Greek).

## Coverage

52 books · 1,103 chapters · ~28,600 verses. **26,000+ verses have both Greek
and English**; the remainder are places where the two traditions genuinely
differ in versification (e.g. the Greek re-ordering of Proverbs, the two Greek
recensions of Tobit, the acrostic of Lamentations) — in those cases the app
shows whichever side is present.

## Rebuilding the data

The per-book data files under `data/books/` and `data/index.js` are generated
from the two cached raw files by:

```
node tools/build-data.mjs
```

The script parses the Greek `.tex` markup (`\biblebook{}`, `\ch{}`, `\vs{}`,
and `psalmhead` wrappers) and the English TSV, maps the 52 books by canonical
identity, merges them verse-by-verse, and prints a per-book verification table.

## A note on "Septuagint"

There is no single "the Septuagint." This edition follows Brenton's Greek and
the Rahlfs-style LXX canon/versification used by the Updated Brenton English.
Scholarly critical editions (Rahlfs–Hanhart; the Göttingen Septuagint) differ
in places. This app is a reading and study tool, not a critical edition.
