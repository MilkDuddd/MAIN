#!/usr/bin/env node
/*
 * build-data.mjs — Parse the two cached public-domain LXX sources into the
 * app's per-book data files.
 *
 *   Greek   : tools/raw/Brenton.tex        (\biblebook{} \ch{} \vs{})
 *   English : tools/raw/eng_native.tsv     (BOOK<TAB>CHAP<TAB>VERSE<TAB>TEXT)
 *
 * Output:
 *   data/index.js            window.LXX_INDEX = {...}
 *   data/books/<CODE>.js     LXXData.register("<CODE>", {...})
 *
 * Re-runnable, Node stdlib only. See SOURCES.md for provenance/licensing.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const RAW = join(__dirname, "raw");

/* ----------------------------------------------------------------------------
 * Canonical book table — Greek source order (1..52) → metadata.
 * `code` matches the English USFM 3-letter code in the TSV.
 * `section` drives the library grouping; `order` is source/reading order.
 * `deutero` flags books outside the Hebrew canon (Anagignoskomena).
 * -------------------------------------------------------------------------- */
const BOOKS = [
  { code: "GEN", en: "Genesis",            gk: "Γένεσις",              tr: "Genesis",         section: "Law" },
  { code: "EXO", en: "Exodus",             gk: "Ἔξοδος",               tr: "Exodos",          section: "Law" },
  { code: "LEV", en: "Leviticus",          gk: "Λευϊτικόν",            tr: "Leuitikon",       section: "Law" },
  { code: "NUM", en: "Numbers",            gk: "Ἀριθμοί",              tr: "Arithmoi",        section: "Law" },
  { code: "DEU", en: "Deuteronomy",        gk: "Δευτερονόμιον",        tr: "Deuteronomion",   section: "Law" },
  { code: "JOS", en: "Joshua (Nauē)",      gk: "Ἰησοῦς Ναυῆ",          tr: "Iēsous Nauē",     section: "History" },
  { code: "JDG", en: "Judges",             gk: "Κριταί",               tr: "Kritai",          section: "History" },
  { code: "RUT", en: "Ruth",               gk: "Ῥούθ",                 tr: "Rhouth",          section: "History" },
  { code: "1SA", en: "1 Kingdoms (1 Samuel)", gk: "Βασιλειῶν Αʹ",      tr: "Basileiōn A",     section: "History" },
  { code: "2SA", en: "2 Kingdoms (2 Samuel)", gk: "Βασιλειῶν Βʹ",      tr: "Basileiōn B",     section: "History" },
  { code: "1KI", en: "3 Kingdoms (1 Kings)",  gk: "Βασιλειῶν Γʹ",      tr: "Basileiōn G",     section: "History" },
  { code: "2KI", en: "4 Kingdoms (2 Kings)",  gk: "Βασιλειῶν Δʹ",      tr: "Basileiōn D",     section: "History" },
  { code: "1CH", en: "1 Chronicles",       gk: "Παραλειπομένων Αʹ",    tr: "Paraleipomenōn A", section: "History" },
  { code: "2CH", en: "2 Chronicles",       gk: "Παραλειπομένων Βʹ",    tr: "Paraleipomenōn B", section: "History" },
  { code: "EZR", en: "2 Esdras (Ezra–Nehemiah)", gk: "Ἔσδρας Βʹ",      tr: "Esdras B",        section: "History" },
  { code: "ESG", en: "Esther (Greek)",     gk: "Ἐσθήρ",                tr: "Esthēr",          section: "History" },
  { code: "JOB", en: "Job",                gk: "Ἰώβ",                  tr: "Iōb",             section: "Wisdom" },
  { code: "PSA", en: "Psalms",             gk: "Ψαλμοί",               tr: "Psalmoi",         section: "Wisdom" },
  { code: "PRO", en: "Proverbs",           gk: "Παροιμίαι",            tr: "Paroimiai",       section: "Wisdom" },
  { code: "ECC", en: "Ecclesiastes",       gk: "Ἐκκλησιαστής",         tr: "Ekklēsiastēs",    section: "Wisdom" },
  { code: "SNG", en: "Song of Songs",      gk: "ἎΙσμα",                 tr: "Asma",            section: "Wisdom" },
  { code: "ISA", en: "Isaiah",             gk: "Ἠσαΐας",               tr: "Ēsaias",          section: "Prophets" },
  { code: "JER", en: "Jeremiah",           gk: "Ἰερεμίας",             tr: "Ieremias",        section: "Prophets" },
  { code: "LAM", en: "Lamentations",       gk: "Θρῆνοι",               tr: "Thrēnoi",         section: "Prophets" },
  { code: "EZK", en: "Ezekiel",            gk: "Ἰεζεκιήλ",             tr: "Iezekiēl",        section: "Prophets" },
  { code: "DAG", en: "Daniel (Greek)",     gk: "Δανιήλ",               tr: "Daniēl",          section: "Prophets" },
  { code: "HOS", en: "Hosea",              gk: "Ὡσηέ",                 tr: "Hōsēe",           section: "Prophets" },
  { code: "JOL", en: "Joel",               gk: "Ἰωήλ",                 tr: "Iōēl",            section: "Prophets" },
  { code: "AMO", en: "Amos",               gk: "Ἀμώς",                 tr: "Amōs",            section: "Prophets" },
  { code: "OBA", en: "Obadiah",            gk: "Ἀβδιού",               tr: "Abdiou",          section: "Prophets" },
  { code: "JON", en: "Jonah",              gk: "Ἰωνᾶς",                tr: "Iōnas",           section: "Prophets" },
  { code: "MIC", en: "Micah",              gk: "Μιχαίας",              tr: "Michaias",        section: "Prophets" },
  { code: "NAM", en: "Nahum",              gk: "Ναούμ",                tr: "Naoum",           section: "Prophets" },
  { code: "HAB", en: "Habakkuk",           gk: "Ἀμβακούμ",             tr: "Ambakoum",        section: "Prophets" },
  { code: "ZEP", en: "Zephaniah",          gk: "Σοφονίας",             tr: "Sophonias",       section: "Prophets" },
  { code: "HAG", en: "Haggai",             gk: "Ἀγγαῖος",              tr: "Angaios",         section: "Prophets" },
  { code: "ZEC", en: "Zechariah",          gk: "Ζαχαρίας",             tr: "Zacharias",       section: "Prophets" },
  { code: "MAL", en: "Malachi",            gk: "Μαλαχίας",             tr: "Malachias",       section: "Prophets" },
  { code: "1ES", en: "1 Esdras (Esdras A)", gk: "Ἔσδρας Αʹ",           tr: "Esdras A",        section: "Deutero", deutero: true },
  { code: "TOB", en: "Tobit",              gk: "Τωβίτ",                tr: "Tōbit",           section: "Deutero", deutero: true },
  { code: "JDT", en: "Judith",             gk: "Ἰουδίθ",               tr: "Ioudith",         section: "Deutero", deutero: true },
  { code: "WIS", en: "Wisdom of Solomon",  gk: "Σοφία Σαλωμῶνος",      tr: "Sophia Salomōnos", section: "Deutero", deutero: true },
  { code: "SIR", en: "Sirach (Ecclesiasticus)", gk: "Σοφία Σιράχ",     tr: "Sophia Sirach",   section: "Deutero", deutero: true },
  { code: "BAR", en: "Baruch",             gk: "Βαρούχ",               tr: "Barouch",         section: "Deutero", deutero: true },
  { code: "LJE", en: "Epistle of Jeremiah", gk: "Ἐπιστολὴ Ἰερεμίου",   tr: "Epistolē Ieremiou", section: "Deutero", deutero: true },
  { code: "SUS", en: "Susanna",            gk: "Σουσάννα",             tr: "Sousanna",        section: "Deutero", deutero: true },
  { code: "BEL", en: "Bel and the Dragon", gk: "Βὴλ καὶ Δράκων",       tr: "Bēl kai Drakōn",  section: "Deutero", deutero: true },
  { code: "1MA", en: "1 Maccabees",        gk: "Μακκαβαίων Αʹ",        tr: "Makkabaiōn A",    section: "Deutero", deutero: true },
  { code: "2MA", en: "2 Maccabees",        gk: "Μακκαβαίων Βʹ",        tr: "Makkabaiōn B",    section: "Deutero", deutero: true },
  { code: "3MA", en: "3 Maccabees",        gk: "Μακκαβαίων Γʹ",        tr: "Makkabaiōn G",    section: "Deutero", deutero: true },
  { code: "4MA", en: "4 Maccabees",        gk: "Μακκαβαίων Δʹ",        tr: "Makkabaiōn D",    section: "Deutero", deutero: true },
  { code: "MAN", en: "Prayer of Manasseh", gk: "Προσευχὴ Μανασσῆ",     tr: "Proseuchē Manassē", section: "Deutero", deutero: true },
];

const SECTION_LABELS = {
  Law:      "The Law (Pentateuch)",
  History:  "History",
  Wisdom:   "Wisdom & Poetry",
  Prophets: "Prophets",
  Deutero:  "Deuterocanonical (Anagignōskomena)",
};
const SECTION_ORDER = ["Law", "History", "Wisdom", "Prophets", "Deutero"];

/* ----------------------------------------------------------------------------
 * Greek parser: split on \biblebook{}, walk lines within each book.
 * -------------------------------------------------------------------------- */
function cleanGreek(s) {
  return s
    .replace(/\\(?:underline|textit|textbf|emph)\{([^}]*)\}/g, "$1") // keep inner text
    .replace(/\\[a-zA-Z]+\*?(\{[^}]*\})?/g, " ")                     // drop other macros
    .replace(/[{}]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseGreek() {
  const tex = readFileSync(join(RAW, "Brenton.tex"), "utf8");
  const parts = tex.split(/\\biblebook\{([^}]*)\}/); // [pre, name, body, name, body, ...]
  const booksByOrder = [];
  for (let i = 1; i < parts.length; i += 2) {
    // Psalms (and a few poetic chapters) wrap the chapter marker + title in
    //   \begin{psalmhead}{\ch{N} <title>} ... \end{psalmhead}
    // Unwrap so \ch{N} starts a line and the title becomes verse 1. The trailing
    // argument brace lands on the \ch line and is stripped by cleanGreek().
    const body = (parts[i + 1] || "")
      .replace(/\\begin\{psalmhead\}\{/g, "\n")
      .replace(/\\end\{psalmhead\}/g, "\n");
    const chapters = new Map(); // chapNum -> Map(verseKey -> text)
    let curCh = null, curV = null, buf = [];
    const flush = () => {
      if (curCh == null || curV == null) return;
      const text = cleanGreek(buf.join(" "));
      if (text) chapters.get(curCh).set(curV, text);
      buf = [];
    };
    for (const rawLine of body.split("\n")) {
      const line = rawLine.trimEnd();
      const t = line.trim();
      if (!t) continue; // paragraph break
      let m;
      if ((m = t.match(/^\\ch\{(\d+)\}\s?(.*)$/))) {
        flush();
        curCh = Number(m[1]);
        if (!chapters.has(curCh)) chapters.set(curCh, new Map());
        curV = "1";
        buf = m[2] ? [m[2]] : [];
      } else if ((m = t.match(/^\\vs\{([0-9]+[a-zA-Z]?)\}(.*)$/))) {
        flush();
        curV = m[1];
        buf = m[2] ? [m[2]] : [];
      } else if (/^\\(begin|end|def|pagestyle|vfill|setlength|fontsize|selectfont|parindent|input|maketitle|tableofcontents|title|author|date|newpage|clearpage|columnbreak)\b/.test(t)) {
        // structural macro line — ignore
      } else {
        buf.push(t); // continuation of current verse
      }
    }
    flush();
    booksByOrder.push(chapters);
  }
  return booksByOrder; // index-aligned with BOOKS
}

/* ----------------------------------------------------------------------------
 * English parser: TSV BOOK\tCHAP\tVERSE\tTEXT
 * -------------------------------------------------------------------------- */
function parseEnglish() {
  const tsv = readFileSync(join(RAW, "eng_native.tsv"), "utf8");
  const byCode = new Map(); // code -> Map(chap -> Map(verseKey -> text))
  for (const line of tsv.split("\n")) {
    if (!line) continue;
    const p = line.split("\t");
    if (p.length < 4) continue;
    const [code, ch, v] = p;
    const text = p.slice(3).join("\t").trim();
    if (!text) continue;
    if (!byCode.has(code)) byCode.set(code, new Map());
    const chMap = byCode.get(code);
    const cn = Number(ch);
    if (!chMap.has(cn)) chMap.set(cn, new Map());
    chMap.get(cn).set(String(v), text);
  }
  return byCode;
}

/* ----------------------------------------------------------------------------
 * Verse-key ordering: numeric first, then lettered suffix (17, 17a, 17b...).
 * -------------------------------------------------------------------------- */
function verseSortKey(v) {
  const m = String(v).match(/^(\d+)([a-zA-Z]*)$/);
  if (!m) return [Number.MAX_SAFE_INTEGER, String(v)];
  return [Number(m[1]), m[2] || ""];
}
function cmpVerse(a, b) {
  const [an, as] = verseSortKey(a), [bn, bs] = verseSortKey(b);
  return an - bn || (as < bs ? -1 : as > bs ? 1 : 0);
}

/* ----------------------------------------------------------------------------
 * Merge + emit.
 * -------------------------------------------------------------------------- */
function main() {
  const greek = parseGreek();
  const english = parseEnglish();

  if (greek.length !== BOOKS.length) {
    throw new Error(`Greek book count ${greek.length} != table ${BOOKS.length}`);
  }

  mkdirSync(join(ROOT, "data", "books"), { recursive: true });

  const indexBooks = [];
  const report = [];
  let totalVerses = 0, totalWithBoth = 0;

  BOOKS.forEach((meta, i) => {
    const gkChs = greek[i];
    const enChs = english.get(meta.code) || new Map();
    if (!english.has(meta.code)) {
      console.warn(`  ! No English found for ${meta.code} (${meta.en})`);
    }

    const allChapNums = new Set([...gkChs.keys(), ...enChs.keys()]);
    const chapNumsSorted = [...allChapNums].sort((a, b) => a - b);
    const chapters = [];
    let gkV = 0, enV = 0, bothV = 0;

    for (const cn of chapNumsSorted) {
      const gv = gkChs.get(cn) || new Map();
      const ev = enChs.get(cn) || new Map();
      const vkeys = [...new Set([...gv.keys(), ...ev.keys()])].sort(cmpVerse);
      const verses = vkeys.map((v) => {
        const gk = gv.get(v) || "";
        const en = ev.get(v) || "";
        if (gk) gkV++;
        if (en) enV++;
        if (gk && en) bothV++;
        return { v, gk, en };
      });
      chapters.push({ n: cn, verses });
    }

    const nVerses = chapters.reduce((s, c) => s + c.verses.length, 0);
    totalVerses += nVerses;
    totalWithBoth += bothV;

    // index entry
    indexBooks.push({
      code: meta.code, en: meta.en, gk: meta.gk, tr: meta.tr,
      section: meta.section, order: i + 1, chapters: chapters.length,
      deutero: !!meta.deutero,
    });

    // per-book data file
    const payload = { code: meta.code, chapters };
    const js = `/* ${meta.en} — ${meta.gk}. Text: public domain (see SOURCES.md). Auto-generated. */\n`
      + `LXXData.register(${JSON.stringify(meta.code)}, ${JSON.stringify(payload)});\n`;
    writeFileSync(join(ROOT, "data", "books", `${meta.code}.js`), js);

    report.push({ code: meta.code, ch: chapters.length, v: nVerses, gk: gkV, en: enV, both: bothV });
  });

  // index.js
  const index = {
    generated: new Date().toISOString(),
    sections: SECTION_ORDER.map((k) => ({ key: k, label: SECTION_LABELS[k] })),
    books: indexBooks,
    stats: { books: indexBooks.length, verses: totalVerses, versesWithBoth: totalWithBoth },
  };
  const indexJs = `/* Auto-generated by tools/build-data.mjs — do not edit by hand. */\n`
    + `window.LXX_INDEX = ${JSON.stringify(index)};\n`;
  writeFileSync(join(ROOT, "data", "index.js"), indexJs);

  // ---- report + assertions ----
  console.log("\n  code  ch   verses    gk    en   both");
  console.log("  ----  ---  -------  ----  ----  ----");
  for (const r of report) {
    const flag = Math.abs(r.gk - r.en) > 25 ? "  <= gk/en delta" : "";
    console.log(`  ${r.code.padEnd(4)}  ${String(r.ch).padStart(3)}  ${String(r.v).padStart(7)}  ${String(r.gk).padStart(4)}  ${String(r.en).padStart(4)}  ${String(r.both).padStart(4)}${flag}`);
  }
  console.log(`\n  Books: ${index.stats.books}   Total verse slots: ${index.stats.verses}   With both gk+en: ${index.stats.versesWithBoth}`);

  const assert = (cond, msg) => { if (!cond) { console.error("ASSERTION FAILED: " + msg); process.exitCode = 1; } };
  assert(index.stats.books === 52, "expected 52 books");
  assert(report.every((r) => r.gk > 0), "every book has Greek verses");
  assert(report.every((r) => r.en > 0), "every book has English verses");
  const gen = report.find((r) => r.code === "GEN");
  assert(gen && gen.ch === 50, "Genesis has 50 chapters");
  const psa = report.find((r) => r.code === "PSA");
  assert(psa && psa.ch === 151, "Psalms has 151 chapters (LXX incl. Ps 151)");
  console.log(index.stats.books === 52 && report.every(r => r.gk && r.en) ? "\n  ✓ build OK\n" : "\n  ✗ build had failures\n");
}

main();
