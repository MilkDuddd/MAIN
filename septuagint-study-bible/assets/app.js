/* ============================================================================
 * Septuagint Study Bible — app.js  (vanilla JS, no build, file:// compatible)
 *   Data is loaded via <script> injection so the app runs straight from disk.
 * ==========================================================================*/
(function () {
  "use strict";

  var IX = window.LXX_INDEX || { books: [], sections: [], stats: {} };
  var COM = window.LXX_COMMENTARY || { books: {}, passages: [] };
  var LEX = window.LXX_LEXICON || { words: {} };

  var byCode = {};
  IX.books.forEach(function (b) { byCode[b.code] = b; });

  /* ---------------------------------------------------------------- loader */
  var LXXData = window.LXXData = {
    _cache: {}, _pending: {},
    register: function (code, data) {
      this._cache[code] = data;
      var cbs = this._pending[code];
      if (cbs) { delete this._pending[code]; cbs.forEach(function (f) { f(data); }); }
    },
    load: function (code, cb) {
      if (this._cache[code]) return cb(this._cache[code]);
      var list = this._pending[code] = this._pending[code] || [];
      list.push(cb);
      if (list.length > 1) return;
      var s = document.createElement("script");
      s.src = "data/books/" + code + ".js";
      var self = this;
      s.onerror = function () { var p = self._pending[code]; delete self._pending[code]; (p || []).forEach(function (f) { f(null); }); };
      document.head.appendChild(s);
    },
    loadAll: function (progress, done) {
      var codes = IX.books.map(function (b) { return b.code; }), self = this, n = 0;
      (function next(i) {
        if (i >= codes.length) return done();
        self.load(codes[i], function () { n++; if (progress) progress(n, codes.length); next(i + 1); });
      })(0);
    }
  };

  /* --------------------------------------------------------------- storage */
  var SKEY = "lxx.settings.v1", NKEY = "lxx.notes.v1";
  var settings = load(SKEY, { theme: "auto", fontScale: 1, gkScale: 1, showVnum: true, viewMode: "parallel" });
  var notes = load(NKEY, {});
  function load(k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v && typeof v === "object" ? Object.assign({}, d, v) : d; } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function nkey(c, ch, v) { return c + " " + ch + ":" + v; }
  function getNote(c, ch, v) { return notes[nkey(c, ch, v)]; }
  function putNote(c, ch, v, obj) {
    var k = nkey(c, ch, v), cur = notes[k] || {};
    var next = Object.assign({}, cur, obj, { ts: Date.now() });
    if (!next.note && !next.color && !next.bookmark) delete notes[k]; else notes[k] = next;
    save(NKEY, notes);
  }

  /* --------------------------------------------------------------- helpers */
  var $ = function (s, r) { return (r || document).querySelector(s); };
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function norm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  var HL = ["yellow", "green", "blue", "pink", "orange"];

  var view = $("#view"), drawer = $("#drawer"), overlay = $("#overlay"), modal = $("#modal");

  /* -------------------------------------------------------------- settings */
  function applySettings() {
    var r = document.documentElement;
    r.dataset.theme = settings.theme;
    r.style.setProperty("--font-scale", settings.fontScale);
    r.style.setProperty("--gk-scale", settings.gkScale);
  }
  applySettings();

  /* ================================================================ ROUTER */
  var lastContentHash = "#/";
  function go(h) { if (location.hash === h) route(); else location.hash = h; }
  window.addEventListener("hashchange", route);

  function route() {
    closeDrawer(); closeModal();
    var h = location.hash.replace(/^#\/?/, "");
    var parts = h.split("/").filter(Boolean).map(decodeURIComponent);
    if (parts.length === 0) { lastContentHash = "#/"; return renderLibrary(); }
    var code = parts[0].toUpperCase();
    if (!byCode[code]) { lastContentHash = "#/"; return renderLibrary(); }
    var ch = Math.max(1, parseInt(parts[1], 10) || 1);
    var v = parts[2] ? parts[2] : null;
    lastContentHash = "#/" + code + "/" + ch;
    renderReader(code, ch, v);
  }

  /* =============================================================== LIBRARY */
  function renderLibrary() {
    var st = IX.stats || {};
    var frag = el("div");
    var hero = el("section", "hero");
    hero.innerHTML =
      '<h1>The Septuagint <span class="gk">Ἡ μετάφρασις τῶν Ἑβδομήκοντα</span></h1>' +
      '<p>' + esc(COM.about || "") + '</p>' +
      '<div class="stats"><span><b>' + (st.books || 0) + '</b> books</span>' +
      '<span><b>' + (st.verses || 0).toLocaleString() + '</b> verses</span>' +
      '<span><b>Greek + English</b> in parallel</span></div>';
    frag.appendChild(hero);

    // Key passages
    var kp = el("section", "keypassages");
    kp.appendChild(el("h2", null, "Key Passages for LXX Study"));
    var grid = el("div", "kp-grid");
    (COM.passages || []).forEach(function (p) {
      var b = byCode[p.code]; if (!b) return;
      var a = el("button", "kp-card");
      a.innerHTML = '<div class="ref">' + esc(b.en) + " " + p.ch + ":" + p.v + (p.vEnd && p.vEnd !== p.v ? "–" + p.vEnd : "") + '</div>' +
        '<div class="ttl">' + esc(p.title) + "</div>";
      a.onclick = function () { go("#/" + p.code + "/" + p.ch + "/" + p.v); };
      grid.appendChild(a);
    });
    kp.appendChild(grid);
    frag.appendChild(kp);

    // Sections of books
    (IX.sections || []).forEach(function (sec) {
      var books = IX.books.filter(function (b) { return b.section === sec.key; });
      if (!books.length) return;
      var s = el("section", "section");
      s.appendChild(el("h2", null, sec.label));
      var g = el("div", "book-grid");
      books.forEach(function (b) {
        var r = el("button", "book-row");
        r.innerHTML =
          '<span class="names"><span class="en">' + esc(b.en) + (b.deutero ? '<span class="badge">deutero</span>' : "") +
          '</span><br><span class="gk">' + esc(b.gk) + "</span></span>" +
          '<span class="meta">' + b.chapters + " ch</span>";
        r.onclick = function () { go("#/" + b.code + "/1"); };
        g.appendChild(r);
      });
      s.appendChild(g);
      frag.appendChild(s);
    });

    setView(frag);
    document.title = "Septuagint Study Bible";
  }

  /* ================================================================ READER */
  function passagesFor(code, ch) {
    return (COM.passages || []).filter(function (p) { return p.code === code && p.ch === ch; });
  }
  function passageAt(code, ch, v) {
    v = parseInt(v, 10);
    return (COM.passages || []).filter(function (p) {
      if (p.code !== code || p.ch !== ch) return false;
      var a = parseInt(p.v, 10), b = parseInt(p.vEnd || p.v, 10);
      return v >= a && v <= b;
    });
  }

  function renderReader(code, ch, focusV) {
    var b = byCode[code];
    setView(el("div", "empty", "Loading " + esc(b.en) + "…"));
    LXXData.load(code, function (data) {
      if (!data) return setView(el("div", "empty", "Could not load " + esc(b.en) + "."));
      ch = Math.min(Math.max(1, ch), data.chapters.length);
      var chap = data.chapters.find(function (c) { return c.n === ch; }) || data.chapters[0];
      var wrap = el("div");

      // crumbs
      var cr = el("div", "crumbs");
      cr.innerHTML = '<a href="#/">Library</a> › <a href="#/' + code + '/1">' + esc(b.en) + "</a> › Chapter " + chap.n;
      wrap.appendChild(cr);

      // head
      var head = el("div", "reader-head");
      head.innerHTML =
        '<h2 class="reader-title"><small>' + esc(b.section === "Deutero" ? "Anagignōskomena" : sectionName(b.section)) + '</small>' +
        esc(b.en) + ' <span class="gk">' + esc(b.gk) + "</span></h2>";
      var ctr = el("div", "reader-controls");

      var prev = el("button", "chip", "‹ Prev");
      prev.onclick = function () { gotoAdj(code, ch, -1); };
      var chapsel = el("select", "chapsel");
      data.chapters.forEach(function (c) { var o = el("option", null, "Chapter " + c.n); o.value = c.n; if (c.n === chap.n) o.selected = true; chapsel.appendChild(o); });
      chapsel.onchange = function () { go("#/" + code + "/" + chapsel.value); };
      var next = el("button", "chip", "Next ›");
      next.onclick = function () { gotoAdj(code, ch, 1); };

      var seg = el("div", "segmented");
      [["parallel", "Parallel"], ["gk", "Greek"], ["en", "English"]].forEach(function (m) {
        var c = el("button", "chip", m[1]);
        c.setAttribute("aria-pressed", settings.viewMode === m[0]);
        c.onclick = function () { settings.viewMode = m[0]; save(SKEY, settings); renderReader(code, ch, null); };
        seg.appendChild(c);
      });
      ctr.appendChild(prev); ctr.appendChild(chapsel); ctr.appendChild(next); ctr.appendChild(seg);
      head.appendChild(ctr);
      wrap.appendChild(head);

      // book intro (chapter 1) + chapter key passages
      var intro = COM.books[code];
      var kps = passagesFor(code, chap.n);
      if ((chap.n === 1 && intro) || kps.length) {
        var box = el("div", "chapter-intro");
        var htm = "";
        if (chap.n === 1 && intro) htm += '<span class="lead">' + esc(b.en) + ".</span> " + esc(intro.intro) + (intro.date ? ' <em class="muted">(' + esc(intro.date) + ")</em>" : "");
        if (kps.length) {
          htm += (htm ? "<br><br>" : "") + '<strong>In this chapter:</strong> ' +
            kps.map(function (p) { return '<a href="#/' + code + "/" + p.ch + "/" + p.v + '">' + esc(p.title) + "</a>"; }).join(" · ");
        }
        box.innerHTML = htm;
        wrap.appendChild(box);
      }

      // verses
      var mode = settings.viewMode;
      var vs = el("div", "verses " + (mode === "parallel" ? "parallel " : "") + "mode-" + mode + (settings.showVnum ? "" : " hide-vnum"));
      chap.verses.forEach(function (vv) {
        vs.appendChild(renderVerse(code, chap.n, vv));
      });
      vs.addEventListener("click", function (ev) {
        var star = ev.target.closest(".js-bm");
        if (star) { var vn = star.getAttribute("data-v"); var cur = getNote(code, chap.n, vn) || {}; putNote(code, chap.n, vn, { bookmark: !cur.bookmark }); decorateVerse(code, chap.n, vn); return; }
        var t = ev.target.closest(".vnum, .js-study");
        if (t) { openStudy(code, chap.n, t.getAttribute("data-v")); }
      });
      wrap.appendChild(vs);

      setView(wrap);
      document.title = b.en + " " + chap.n + " · Septuagint Study Bible";

      if (focusV) {
        var target = $('[data-vid="' + focusV + '"]', vs);
        if (target) { target.scrollIntoView({ block: "center" }); }
        openStudy(code, chap.n, focusV);
      } else { view.scrollIntoView ? window.scrollTo(0, 0) : null; }
    });
  }

  function renderVerse(code, ch, vv) {
    var n = getNote(code, ch, vv.v) || {};
    var cls = "verse" + (n.color ? " hl-" + n.color : "") + (n.note ? " has-note" : "");
    var d = el("div", cls);
    d.setAttribute("data-vid", vv.v);
    var hasCom = passageAt(code, ch, vv.v).length > 0;
    var marks = '<span class="marks">' +
      '<button class="js-bm ' + (n.bookmark ? "on" : "") + '" data-v="' + esc(vv.v) + '" title="Bookmark">' + (n.bookmark ? "★" : "☆") + "</button>" +
      '<button class="js-study" data-v="' + esc(vv.v) + '" title="Study this verse">' + (hasCom ? "◆" : "✎") + "</button></span>";
    var gkCol = '<div class="col gk-col"><span class="vnum" data-v="' + esc(vv.v) + '">' + esc(vv.v) + "</span>" +
      '<span class="gk-text">' + esc(vv.gk || "—") + "</span></div>";
    var enCol = '<div class="col en-col"><span class="vnum" data-v="' + esc(vv.v) + '">' + esc(vv.v) + "</span>" +
      '<span class="en-text">' + esc(vv.en || "—") + "</span>" + marks + "</div>";
    // in gk-only mode marks live on gk col
    if (settings.viewMode === "gk") {
      gkCol = '<div class="col gk-col"><span class="vnum" data-v="' + esc(vv.v) + '">' + esc(vv.v) + "</span>" +
        '<span class="gk-text">' + esc(vv.gk || "—") + "</span>" + marks + "</div>";
    }
    d.innerHTML = gkCol + enCol;
    return d;
  }
  function decorateVerse(code, ch, v) {
    var node = $('[data-vid="' + CSS.escape(String(v)) + '"]', view);
    if (!node) return;
    var vv = null, data = LXXData._cache[code];
    if (data) { var c = data.chapters.find(function (x) { return x.n === ch; }); if (c) vv = c.verses.find(function (x) { return x.v === String(v); }); }
    if (vv) { var fresh = renderVerse(code, ch, vv); node.replaceWith(fresh); }
  }

  function gotoAdj(code, ch, dir) {
    var b = byCode[code], data = LXXData._cache[code];
    var max = data ? data.chapters.length : b.chapters;
    var nc = ch + dir;
    if (nc >= 1 && nc <= max) return go("#/" + code + "/" + nc);
    // move book
    var order = b.order + dir;
    var nb = IX.books.find(function (x) { return x.order === order; });
    if (!nb) return;
    if (dir > 0) go("#/" + nb.code + "/1");
    else LXXData.load(nb.code, function (d) { go("#/" + nb.code + "/" + (d ? d.chapters.length : 1)); });
  }
  function sectionName(k) { var s = (IX.sections || []).find(function (x) { return x.key === k; }); return s ? s.label : k; }

  /* ============================================================ STUDY DRAWER */
  function openStudy(code, ch, v) {
    var b = byCode[code], data = LXXData._cache[code];
    var chap = data && data.chapters.find(function (c) { return c.n === ch; });
    var vv = chap && chap.verses.find(function (x) { return x.v === String(v); });
    if (!vv) return;
    var n = getNote(code, ch, v) || {};

    var body = el("div", "body");
    // quote
    var q = el("div", "verse-quote");
    q.innerHTML = (vv.gk ? '<div class="gk-text">' + esc(vv.gk) + "</div>" : "") +
      (vv.en ? '<div class="en-text">' + esc(vv.en) + "</div>" : "");
    body.appendChild(q);

    // commentary
    var pass = passageAt(code, ch, v);
    var words = {};
    if (pass.length) {
      body.appendChild(el("h4", null, "Commentary"));
      pass.forEach(function (p) {
        var nb = el("div", "note-block commentary");
        var htm = '<div class="ttl">' + esc(p.title) + "</div>" + "<div>" + esc(p.body) + "</div>";
        if (p.mt) htm += '<div class="diff"><span class="tag mt">LXX ↔ Hebrew</span>' + esc(p.mt) + "</div>";
        if (p.nt) htm += '<div class="diff"><span class="tag nt">NT use</span>' + esc(p.nt) + "</div>";
        nb.innerHTML = htm;
        body.appendChild(nb);
        (p.words || []).forEach(function (w) { if (LEX.words[w]) words[w] = LEX.words[w]; });
      });
    }
    // book intro link
    if (COM.books[code]) {
      var ib = el("div", "note-block commentary");
      ib.innerHTML = '<div class="ttl">About ' + esc(b.en) + "</div><div>" + esc(COM.books[code].intro) + "</div>";
      if (!pass.length) { body.appendChild(el("h4", null, "Book Introduction")); }
      body.appendChild(ib);
    }
    // word studies
    var wkeys = Object.keys(words);
    if (wkeys.length) {
      body.appendChild(el("h4", null, "Word Studies"));
      wkeys.forEach(function (w) {
        var d = words[w], wd = el("div", "worddef");
        wd.innerHTML = '<span class="gk">' + esc(d.gk) + '</span> <em class="muted">' + esc(d.tr) + "</em> — <strong>" + esc(d.gloss) + "</strong><div>" + esc(d.note) + "</div>";
        body.appendChild(wd);
      });
    }

    // highlight
    body.appendChild(el("h4", null, "Highlight"));
    var hlrow = el("div", "hlrow");
    var none = el("div", "swatch none" + (!n.color ? " sel" : "")); none.title = "No highlight";
    none.onclick = function () { putNote(code, ch, v, { color: null }); decorateVerse(code, ch, v); refresh(); };
    hlrow.appendChild(none);
    HL.forEach(function (c) {
      var s = el("div", "swatch" + (n.color === c ? " sel" : ""));
      s.style.background = "var(--hl-" + c + ")";
      s.onclick = function () { putNote(code, ch, v, { color: c }); decorateVerse(code, ch, v); refresh(); };
      hlrow.appendChild(s);
    });
    body.appendChild(hlrow);

    // personal note
    body.appendChild(el("h4", null, "My Note"));
    var ta = el("textarea"); ta.id = "noteInput"; ta.placeholder = "Write your study note for " + b.en + " " + ch + ":" + v + "…"; ta.value = n.note || "";
    body.appendChild(ta);
    var actions = el("div", "row-actions");
    var savb = el("button", "btn", "Save note");
    savb.onclick = function () { putNote(code, ch, v, { note: ta.value.trim() }); decorateVerse(code, ch, v); flash(savb, "Saved ✓"); };
    var bmb = el("button", "btn ghost", (n.bookmark ? "★ Bookmarked" : "☆ Bookmark"));
    bmb.onclick = function () { var cur = getNote(code, ch, v) || {}; putNote(code, ch, v, { bookmark: !cur.bookmark }); decorateVerse(code, ch, v); refresh(); };
    actions.appendChild(savb); actions.appendChild(bmb);
    body.appendChild(actions);

    function refresh() { openStudy(code, ch, v); }

    var head = el("header");
    head.innerHTML = '<span class="ref">' + esc(b.en) + " " + ch + ":" + v + "</span>";
    var x = el("button", "close", "×"); x.onclick = closeDrawer; head.appendChild(x);

    drawer.innerHTML = "";
    drawer.appendChild(head); drawer.appendChild(body);
    drawer.hidden = false; overlay.hidden = false;
  }
  function flash(btn, msg) { var t = btn.textContent; btn.textContent = msg; setTimeout(function () { btn.textContent = t; }, 1200); }
  function closeDrawer() { drawer.hidden = true; if (modal.hidden) overlay.hidden = true; }
  overlay.onclick = function () { closeDrawer(); closeModal(); };

  /* ================================================================ SEARCH */
  var searchTimer, searching = false;
  var input = $("#globalSearch");
  input.addEventListener("input", function () {
    clearTimeout(searchTimer);
    var q = input.value.trim();
    if (q.length < 2) { if (!q) route(); return; }
    searchTimer = setTimeout(function () { doSearch(q); }, 220);
  });
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") { clearTimeout(searchTimer); if (input.value.trim().length >= 2) doSearch(input.value.trim()); } });

  function doSearch(q) {
    var loaded = IX.books.every(function (b) { return LXXData._cache[b.code]; });
    if (!loaded) {
      var wrap = el("div");
      wrap.appendChild(el("h2", "keypassages", "Preparing search…"));
      var bar = el("div", "loadbar"); var i = el("i"); bar.appendChild(i); wrap.appendChild(bar);
      var lbl = el("div", "muted", "Loading the full text once…"); wrap.appendChild(lbl);
      setView(wrap);
      LXXData.loadAll(function (n, t) { i.style.width = (100 * n / t) + "%"; lbl.textContent = "Loading books… " + n + "/" + t; },
        function () { renderSearch(q); });
    } else renderSearch(q);
  }

  function renderSearch(q) {
    var nq = norm(q);
    var scripture = [], commentary = [], cap = 400;
    // commentary + intros
    (COM.passages || []).forEach(function (p) {
      if (norm(p.title + " " + p.body + " " + (p.mt || "") + " " + (p.nt || "")).indexOf(nq) >= 0)
        commentary.push({ code: p.code, ch: p.ch, v: p.v, title: p.title, snip: p.body });
    });
    Object.keys(COM.books).forEach(function (code) {
      var t = COM.books[code].intro;
      if (norm(t).indexOf(nq) >= 0) commentary.push({ code: code, ch: 1, v: "1", title: "Introduction to " + byCode[code].en, snip: t });
    });
    // scripture
    outer:
    for (var bi = 0; bi < IX.books.length; bi++) {
      var code = IX.books[bi].code, data = LXXData._cache[code]; if (!data) continue;
      for (var ci = 0; ci < data.chapters.length; ci++) {
        var chap = data.chapters[ci];
        for (var vi = 0; vi < chap.verses.length; vi++) {
          var vv = chap.verses[vi];
          var hitEn = vv.en && norm(vv.en).indexOf(nq) >= 0;
          var hitGk = vv.gk && norm(vv.gk).indexOf(nq) >= 0;
          if (hitEn || hitGk) {
            scripture.push({ code: code, ch: chap.n, v: vv.v, en: vv.en, gk: vv.gk, hitEn: hitEn, hitGk: hitGk });
            if (scripture.length >= cap) break outer;
          }
        }
      }
    }

    var wrap = el("div");
    var cr = el("div", "crumbs"); cr.innerHTML = '<a href="#/">Library</a> › Search'; wrap.appendChild(cr);
    var h = el("section", "keypassages");
    h.appendChild(el("h2", null, 'Results for “' + esc(q) + '” — ' + scripture.length + (scripture.length >= cap ? "+" : "") + " scripture · " + commentary.length + " commentary"));
    wrap.appendChild(h);

    if (commentary.length) {
      var cs = el("section", "section"); cs.appendChild(el("h2", null, "Commentary & Introductions"));
      commentary.slice(0, 40).forEach(function (r) {
        var a = el("a", "sr-item"); a.href = "#/" + r.code + "/" + r.ch + "/" + r.v;
        a.innerHTML = '<div class="ref">' + esc(byCode[r.code].en) + " " + r.ch + ":" + r.v + " — " + esc(r.title) + '</div><div class="snip">' + snippet(esc(r.snip), q) + "</div>";
        cs.appendChild(a);
      });
      wrap.appendChild(cs);
    }
    var ss = el("section", "section"); ss.appendChild(el("h2", null, "Scripture"));
    if (!scripture.length) ss.appendChild(el("div", "empty", "No verses matched."));
    scripture.slice(0, 200).forEach(function (r) {
      var a = el("a", "sr-item"); a.href = "#/" + r.code + "/" + r.ch + "/" + r.v;
      var snip = r.hitEn ? '<span>' + snippet(esc(r.en), q) + "</span>" : '<span class="gk">' + snippet(esc(r.gk), q) + "</span>";
      a.innerHTML = '<div class="ref">' + esc(byCode[r.code].en) + " " + r.ch + ":" + r.v + '</div><div class="snip">' + snip + "</div>";
      ss.appendChild(a);
    });
    wrap.appendChild(ss);
    setView(wrap);
    document.title = "Search: " + q;
  }
  function snippet(escaped, q) {
    // escaped is already HTML-escaped; do a diacritic/case-insensitive locate on a normalized copy
    var plain = escaped, np = norm(plain), nq = norm(q);
    var i = np.indexOf(nq);
    if (i < 0) return plain.length > 160 ? plain.slice(0, 160) + "…" : plain;
    var start = Math.max(0, i - 60), end = Math.min(plain.length, i + nq.length + 90);
    var pre = (start > 0 ? "…" : "") + plain.slice(start, i);
    var mid = plain.slice(i, i + q.length);
    var post = plain.slice(i + q.length, end) + (end < plain.length ? "…" : "");
    return pre + "<mark>" + mid + "</mark>" + post;
  }

  /* =============================================================== MY STUDY */
  $("#myStudyBtn").onclick = renderMyStudy;
  function renderMyStudy() {
    var keys = Object.keys(notes);
    var card = el("div", "card");
    var htm = '<button class="close-x" data-close>×</button><h3>✦ My Study</h3>';
    if (!keys.length) htm += '<div class="empty">No notes yet. Open any verse and use the study panel to add notes, highlights, and bookmarks.</div>';
    htm += '<div class="row-actions" style="margin-bottom:14px"><button class="btn" data-export>⬇ Export JSON</button><button class="btn ghost" data-import>⬆ Import</button><input type="file" accept="application/json" id="importFile" hidden></div>';
    card.innerHTML = htm;

    keys.sort().forEach(function (k) {
      var n = notes[k];
      var m = k.match(/^(\S+) (\d+):(.+)$/); if (!m) return;
      var code = m[1], ch = m[2], v = m[3], b = byCode[code]; if (!b) return;
      var it = el("div", "mystudy-item");
      it.innerHTML = '<div><a href="#/' + code + "/" + ch + "/" + v + '" data-goto><span class="ref">' + esc(b.en) + " " + ch + ":" + v + "</span></a>" +
        (n.bookmark ? " ★" : "") + (n.color ? '<span class="dot" style="background:var(--hl-' + n.color + ')"></span>' : "") + "</div>" +
        (n.note ? '<div class="note">' + esc(n.note) + "</div>" : "");
      card.appendChild(it);
    });
    openModal(card);
    card.addEventListener("click", function (e) {
      if (e.target.closest("[data-goto]")) { closeModal(); }
      if (e.target.closest("[data-export]")) exportNotes();
      if (e.target.closest("[data-import]")) $("#importFile", card).click();
    });
    $("#importFile", card).addEventListener("change", importNotes);
  }
  function exportNotes() {
    var blob = new Blob([JSON.stringify(notes, null, 2)], { type: "application/json" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = "septuagint-study-notes.json"; a.click(); URL.revokeObjectURL(a.href);
  }
  function importNotes(e) {
    var f = e.target.files[0]; if (!f) return;
    var rd = new FileReader();
    rd.onload = function () {
      try { var obj = JSON.parse(rd.result); if (obj && typeof obj === "object") { Object.assign(notes, obj); save(NKEY, notes); renderMyStudy(); } }
      catch (err) { alert("Could not read that file."); }
    };
    rd.readAsText(f);
  }

  /* =============================================================== SETTINGS */
  $("#settingsBtn").onclick = renderSettings;
  function renderSettings() {
    var card = el("div", "card");
    card.innerHTML =
      '<button class="close-x" data-close>×</button><h3>⚙ Settings</h3>' +
      row("Theme", '<select id="setTheme">' + opt(["auto", "light", "sepia", "dark"], settings.theme) + "</select>") +
      row("Text size", seg("setFont", [["0.9", "S"], ["1", "M"], ["1.15", "L"], ["1.3", "XL"]], String(settings.fontScale))) +
      row("Greek size", seg("setGk", [["0.9", "S"], ["1", "M"], ["1.15", "L"], ["1.3", "XL"]], String(settings.gkScale))) +
      row("Verse numbers", '<label class="switch"><input type="checkbox" id="setVnum" ' + (settings.showVnum ? "checked" : "") + "> show</label>") +
      row("Default view", '<select id="setView">' + opt2([["parallel", "Parallel"], ["gk", "Greek only"], ["en", "English only"]], settings.viewMode) + "</select>") +
      '<div class="setting"><span class="lbl">Sources & license<small>All scripture text is public domain / CC0.</small></span><a href="#" data-about>About</a></div>' +
      '<div class="row-actions" style="margin-top:14px"><button class="btn" data-close>Done</button><button class="btn ghost" data-reset>Reset settings</button></div>';
    openModal(card);
    $("#setTheme", card).onchange = function () { settings.theme = this.value; commit(); };
    $("#setVnum", card).onchange = function () { settings.showVnum = this.checked; commit(true); };
    $("#setView", card).onchange = function () { settings.viewMode = this.value; commit(true); };
    card.querySelectorAll("[data-seg]").forEach(function (btn) {
      btn.onclick = function () {
        var grp = btn.getAttribute("data-seg"), val = btn.getAttribute("data-val");
        card.querySelectorAll('[data-seg="' + grp + '"]').forEach(function (x) { x.setAttribute("aria-pressed", x === btn); });
        if (grp === "setFont") settings.fontScale = parseFloat(val);
        if (grp === "setGk") settings.gkScale = parseFloat(val);
        commit();
      };
    });
    card.addEventListener("click", function (e) {
      if (e.target.closest("[data-reset]")) { settings = { theme: "auto", fontScale: 1, gkScale: 1, showVnum: true, viewMode: "parallel" }; save(SKEY, settings); applySettings(); closeModal(); route(); }
      if (e.target.closest("[data-about]")) { e.preventDefault(); renderAbout(); }
    });
    function commit(rerender) { save(SKEY, settings); applySettings(); if (rerender) { var h = lastContentHash; closeModal(); if (location.hash === h) route(); } }
  }
  function renderAbout() {
    var card = el("div", "card");
    card.innerHTML = '<button class="close-x" data-close>×</button><h3>About & Sources</h3>' +
      '<p>' + esc(COM.about) + "</p>" +
      "<h4>Texts (public domain / CC0)</h4><ul>" +
      "<li><strong>Greek LXX</strong> — Brenton's Septuagint, from the CC0/public-domain <em>Brenton-LXX-Latex</em> print project.</li>" +
      "<li><strong>English</strong> — the <em>Updated Brenton English Septuagint</em> (Adam Boyd, 2020, released CC0), in native LXX versification.</li>" +
      "<li>Commentary, introductions, and word studies are original editorial content.</li></ul>" +
      '<div class="row-actions"><button class="btn" data-close>Close</button></div>';
    openModal(card);
  }
  function row(label, control) { return '<div class="setting"><span class="lbl">' + label + "</span><span>" + control + "</span></div>"; }
  function opt(list, sel) { return list.map(function (x) { return '<option value="' + x + '"' + (x === sel ? " selected" : "") + ">" + x.charAt(0).toUpperCase() + x.slice(1) + "</option>"; }).join(""); }
  function opt2(list, sel) { return list.map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === sel ? " selected" : "") + ">" + x[1] + "</option>"; }).join(""); }
  function seg(grp, list, sel) { return '<span class="segmented">' + list.map(function (x) { return '<button class="chip" data-seg="' + grp + '" data-val="' + x[0] + '" aria-pressed="' + (x[0] === sel) + '">' + x[1] + "</button>"; }).join("") + "</span>"; }

  /* ---------------------------------------------------------------- modal */
  function openModal(card) { modal.innerHTML = ""; modal.appendChild(card); modal.hidden = false; overlay.hidden = false; modal.addEventListener("click", modalClick); }
  function modalClick(e) { if (e.target === modal || e.target.closest("[data-close]")) closeModal(); }
  function closeModal() { modal.hidden = true; modal.innerHTML = ""; if (drawer.hidden) overlay.hidden = true; }

  /* ------------------------------------------------------------- view util */
  function setView(node) { view.innerHTML = ""; view.appendChild(node); }

  /* ---------------------------------------------------------------- keys */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeDrawer(); closeModal(); }
    if (e.key === "/" && document.activeElement !== input) { e.preventDefault(); input.focus(); }
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (typing) return;
    var m = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
    if (m.length && byCode[(m[0] || "").toUpperCase()] && drawer.hidden && modal.hidden) {
      if (e.key === "ArrowRight") gotoAdj(m[0].toUpperCase(), parseInt(m[1], 10) || 1, 1);
      if (e.key === "ArrowLeft") gotoAdj(m[0].toUpperCase(), parseInt(m[1], 10) || 1, -1);
    }
  });
  $("#homeBtn").onclick = function () { input.value = ""; go("#/"); };

  /* ---------------------------------------------------------------- start */
  route();
})();
