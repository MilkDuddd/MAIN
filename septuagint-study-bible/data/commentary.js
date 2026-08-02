/* ============================================================================
 * commentary.js — Original study apparatus for the LXX Study Bible.
 *
 *   LXX_COMMENTARY.books[CODE]      → { intro, date, note }  (all 52 books)
 *   LXX_COMMENTARY.passages[]       → verse-range notes with:
 *        code, ch, v, vEnd?, title, body, mt?  (LXX↔MT difference),
 *        nt? (New-Testament reception), words? ([lexicon ids])
 *
 * All prose here is original editorial content, clearly separated from the
 * public-domain scripture text (see SOURCES.md). Scholarship follows standard
 * Septuagint reference works (Jobes & Silva, Rahlfs–Hanhart, NETS, Swete).
 * ==========================================================================*/
window.LXX_COMMENTARY = {
  about:
    "The Septuagint (LXX) is the ancient Greek translation of the Hebrew " +
    "Scriptures, begun in Alexandria in the 3rd century BC with the Torah and " +
    "completed over the following two centuries. It was the Bible of the " +
    "Greek-speaking Jewish diaspora and of the earliest Church: the large " +
    "majority of Old-Testament quotations in the New Testament follow its " +
    "wording rather than the Hebrew. Studying it reveals how Israel's " +
    "Scriptures were read in the Hellenistic world and how the vocabulary of " +
    "the New Testament was formed.",

  books: {
    GEN: { date: "Torah translated c. 3rd c. BC", intro:
      "Γένεσις (‘origin’) takes its name from the Greek word that opens its " +
      "genealogies. As part of the Pentateuch it is the oldest and most " +
      "carefully rendered stratum of the LXX, and its vocabulary — κόσμος, " +
      "διαθήκη, εὐλογία — set the pattern for later translators. The NT quotes " +
      "Genesis in LXX form repeatedly (e.g. Rom 4; Gal 3; Heb 11)." },
    EXO: { date: "3rd–2nd c. BC", intro:
      "Ἔξοδος (‘the way out’) narrates the deliverance from Egypt and the " +
      "giving of the Law. The Greek supplies the divine self-designation ἐγώ " +
      "εἰμι ὁ Ὤν (‘I am THE BEING’, 3:14), a philosophically charged rendering " +
      "that shaped Jewish and Christian doctrine of God." },
    LEV: { date: "2nd c. BC", intro:
      "Λευϊτικόν concerns the priestly and sacrificial system. Its Greek " +
      "cultic vocabulary — ἱλαστήριον (mercy-seat), ὁλοκαύτωμα (whole burnt " +
      "offering), ἁγιάζω — becomes the technical language the NT uses to " +
      "interpret the death of Christ (esp. Hebrews)." },
    NUM: { date: "2nd c. BC", intro:
      "Ἀριθμοί (‘numbers’) is named for the censuses of Israel in the " +
      "wilderness. The Greek preserves Balaam's oracles, including the " +
      "‘star out of Jacob’ (24:17) read messianically in early Judaism." },
    DEU: { date: "2nd c. BC", intro:
      "Δευτερονόμιον (‘second law’) is Moses' covenant renewal. It is among " +
      "the most-quoted books in the NT; Jesus answers the temptation from its " +
      "Greek text (Mt 4 / Deut 6–8), and the Shema (6:4-5) is cited in LXX form." },

    JOS: { date: "2nd c. BC", intro:
      "Named Ἰησοῦς Ναυῆ — ‘Jesus (Joshua) son of Nun’. The Greek Joshua is " +
      "somewhat shorter than the Masoretic Text, an early witness to a " +
      "different Hebrew edition of the book." },
    JDG: { date: "2nd c. BC", intro:
      "Κριταί survives in two markedly different Greek forms (represented by " +
      "codices A and B), making it a classic case study in LXX textual " +
      "history and recensional development." },
    RUT: { date: "2nd–1st c. BC", intro:
      "Ῥούθ, the Moabite ancestress of David, belongs to the later ‘kaige’ " +
      "layer of the LXX, which revised the Greek toward a more literal " +
      "correspondence with the Hebrew." },
    "1SA": { date: "‘kaige’ sections 1st c. BC", intro:
      "1 Kingdoms (Βασιλειῶν Αʹ) = Hebrew 1 Samuel. The LXX of Samuel–Kings " +
      "often agrees with the Hebrew of the Dead Sea Scrolls (4QSam) against " +
      "the later Masoretic Text, and is invaluable for reconstructing the " +
      "oldest text." },
    "2SA": { date: "‘kaige’ recension", intro:
      "2 Kingdoms (Βασιλειῶν Βʹ) = 2 Samuel. Portions fall in the ‘kaige’ " +
      "section, a revision aligning the Greek with a proto-Masoretic Hebrew." },
    "1KI": { date: "mixed layers", intro:
      "3 Kingdoms (Βασιλειῶν Γʹ) = 1 Kings. The Greek differs substantially in " +
      "arrangement (notably the Solomon and Jeroboam narratives), reflecting a " +
      "distinct Hebrew edition." },
    "2KI": { date: "‘kaige’ recension", intro:
      "4 Kingdoms (Βασιλειῶν Δʹ) = 2 Kings, largely in the literal ‘kaige’ " +
      "style. The fourfold ‘Kingdoms’ title is the LXX's own way of unifying " +
      "Samuel–Kings." },
    "1CH": { date: "2nd–1st c. BC", intro:
      "Παραλειπομένων Αʹ — ‘things left over/omitted’, the LXX name for " +
      "Chronicles as a supplement to Samuel–Kings. 1 Chronicles covers the " +
      "genealogies and David's reign." },
    "2CH": { date: "2nd–1st c. BC", intro:
      "Παραλειπομένων Βʹ continues through Solomon, the temple, and the fall " +
      "of Judah; the Greek closes with Cyrus' decree of return." },
    EZR: { date: "1st c. BC", intro:
      "In LXX order this is Esdras B (Ἔσδρας Βʹ), corresponding to Hebrew " +
      "Ezra–Nehemiah as a single work. It is distinct from the apocryphal " +
      "1 Esdras (Esdras A), which retells much of the same history in freer " +
      "Greek." },
    ESG: { date: "colophon dates it c. 114 BC", intro:
      "The Greek Esther is a quarter longer than the Hebrew, with six major " +
      "‘Additions’ (A–F) supplying the dreams of Mordecai, royal edicts, and " +
      "the prayers of Mordecai and Esther. Unlike the Hebrew, Greek Esther " +
      "names God explicitly and is overtly a book of prayer." },

    JOB: { date: "1st c. BC", intro:
      "The Old Greek Job is about one-sixth shorter than the Hebrew; the gaps " +
      "were later filled from Theodotion (marked with asterisks in Origen's " +
      "Hexapla). The Greek softens some of Job's harshest speeches and adds a " +
      "closing note on his genealogy and resurrection hope." },
    PSA: { date: "2nd c. BC", intro:
      "Ψαλμοί, the Church's prayer book. The LXX numbering runs one behind the " +
      "Hebrew for most of the Psalter (LXX Ps 22 = Heb Ps 23) because it joins " +
      "Hebrew Pss 9–10 and 114–115 and splits 116 and 147. It also includes " +
      "the supernumerary Psalm 151. The NT quotes the Psalms in Greek more " +
      "than any other book." },
    PRO: { date: "2nd c. BC", intro:
      "Παροιμίαι is a free, expansive translation that reorders the collections " +
      "of chapters 24–31 and adds proverbs with no Hebrew counterpart — the " +
      "reason the Greek and Masoretic verse-numbering diverge here." },
    ECC: { date: "1st–2nd c. AD", intro:
      "Ἐκκλησιαστής (‘the assembler/preacher’) is rendered in an extremely " +
      "literal, word-for-word style associated with Aquila's school, useful " +
      "for seeing how the Hebrew was construed word by word." },
    SNG: { date: "1st c. AD", intro:
      "ἎΙσμα ᾈσμάτων, the ‘Song of Songs’, is likewise a very literal Greek " +
      "rendering; both Jewish and Christian readers interpreted it allegorically " +
      "of God's love for his people." },

    ISA: { date: "c. 140 BC (Alexandria)", intro:
      "The Greek Isaiah is a comparatively free, interpretive translation that " +
      "often actualises the prophecies for the translator's own Hellenistic " +
      "age. It supplies several readings central to the NT — most famously ἡ " +
      "παρθένος (‘the virgin’, 7:14) and the ‘Servant’ of chapter 53." },
    JER: { date: "2nd c. BC", intro:
      "The Greek Jeremiah is about one-eighth shorter than the Masoretic Text " +
      "and arranges the oracles against the nations differently. The Dead Sea " +
      "Scrolls confirm that the LXX reflects a genuinely older and shorter " +
      "Hebrew edition of the book." },
    LAM: { date: "1st c. BC–AD", intro:
      "Θρῆνοι (‘dirges’) mourns the fall of Jerusalem in acrostic poems; the " +
      "Greek preserves the Hebrew alphabetic structure by prefixing the letter " +
      "names to each stanza." },
    EZK: { date: "2nd c. BC", intro:
      "Ἰεζεκιήλ is transmitted in a relatively literal Greek; papyrus 967 " +
      "preserves an older chapter order and is a key witness to the book's " +
      "textual development." },
    DAG: { date: "Old Greek 2nd c. BC; ‘Theodotion’ later", intro:
      "The Church's Daniel is unusual: the Old Greek was so free that it was " +
      "replaced in most manuscripts by the ‘Theodotion’ version. Greek Daniel " +
      "includes the Prayer of Azariah and Song of the Three (in ch. 3), and " +
      "the stories of Susanna and Bel are transmitted with it." },

    HOS: { date: "2nd c. BC", intro:
      "Hosea opens the Greek ‘Book of the Twelve’, transmitted as a single " +
      "scroll. Its Greek is quoted in the NT (e.g. ‘Out of Egypt I called my " +
      "son’, Hos 11:1; ‘I desire mercy’, 6:6)." },
    JOL: { date: "2nd c. BC", intro:
      "Ἰωήλ's promise that God will ‘pour out my Spirit on all flesh’ (3:1-2 " +
      "LXX) is cited from the Greek by Peter at Pentecost (Acts 2)." },
    AMO: { date: "2nd c. BC", intro:
      "The Greek Amos supplies the form of 9:11-12 (‘the tent of David… that " +
      "the rest of men may seek the Lord’) quoted by James at the Jerusalem " +
      "Council (Acts 15) — a reading that differs from the Hebrew." },
    OBA: { date: "2nd c. BC", intro:
      "Ἀβδιού, the shortest book of the Twelve, pronounces judgment on Edom." },
    JON: { date: "2nd c. BC", intro:
      "Ἰωνᾶς, the reluctant prophet sent to Nineveh. Jesus makes ‘the sign of " +
      "Jonah’ — three days in the sea-monster (κῆτος, 2:1) — a type of his own " +
      "burial and resurrection (Mt 12:40)." },
    MIC: { date: "2nd c. BC", intro:
      "Μιχαίας foretells the ruler to come from Bethlehem (5:1 LXX), cited at " +
      "Matthew 2." },
    NAM: { date: "2nd c. BC", intro:
      "Ναούμ proclaims the fall of Nineveh, a counterpoint to Jonah." },
    HAB: { date: "2nd c. BC", intro:
      "Ἀμβακούμ's ‘the righteous shall live by my faith’ (2:4 LXX) is the text " +
      "Paul builds upon in Romans and Galatians. Chapter 3 is a psalm with " +
      "musical notation." },
    ZEP: { date: "2nd c. BC", intro:
      "Σοφονίας announces ‘the day of the Lord’ and the gathering of the " +
      "nations to call on the name of the Lord (3:9-10)." },
    HAG: { date: "2nd c. BC", intro:
      "Ἀγγαῖος urges the rebuilding of the temple; Hebrews 12 cites its promise " +
      "that God will ‘shake’ heaven and earth (2:6)." },
    ZEC: { date: "2nd c. BC", intro:
      "Ζαχαρίας' visions of the coming king ‘lowly and riding on a donkey’ " +
      "(9:9) and the pierced one (12:10) are applied to Christ in the Gospels." },
    MAL: { date: "2nd c. BC", intro:
      "Μαλαχίας closes the Twelve with the promise of the messenger who " +
      "prepares the Lord's way (3:1) and ‘Elijah’ (4:5-6), quoted of John the " +
      "Baptist." },

    "1ES": { date: "2nd c. BC", intro:
      "Esdras A (1 Esdras) retells 2 Chronicles 35 – Nehemiah 8 in polished, " +
      "independent Greek, and adds the famous ‘Contest of the Three " +
      "Bodyguards’ (chs. 3–4) on the theme ‘Truth is greatest and prevails’. " +
      "It is not in the Hebrew canon." },
    TOB: { date: "c. 2nd c. BC", intro:
      "Τωβίτ is a diaspora tale of piety, almsgiving, and the angel Raphael. " +
      "It survives in two Greek recensions of differing length (best preserved " +
      "in codices B/A vs. Sinaiticus), which is why its versification varies. " +
      "Aramaic and Hebrew fragments were found at Qumran." },
    JDT: { date: "2nd c. BC", intro:
      "Ἰουδίθ tells how a devout widow saves her city by killing the general " +
      "Holofernes — a story of trust in God against overwhelming power." },
    WIS: { date: "1st c. BC (Alexandria)", intro:
      "Σοφία Σαλωμῶνος was composed in Greek (not translated) by a Hellenistic " +
      "Jew. Its portrait of the persecuted ‘righteous one’ who calls God his " +
      "father (ch. 2) and its teaching on immortality and Wisdom (ch. 7) deeply " +
      "influenced NT Christology (cf. Heb 1; John 1)." },
    SIR: { date: "grandson's Greek c. 132 BC", intro:
      "Σοφία Σιράχ (Ecclesiasticus) was written in Hebrew by Jesus ben Sira " +
      "(c. 180 BC) and translated by his grandson, whose Prologue is the " +
      "earliest description of the Hebrew Scriptures as ‘the Law, the Prophets, " +
      "and the others’. A major witness to Second-Temple wisdom and to " +
      "personified Wisdom (ch. 24)." },
    BAR: { date: "2nd c. BC", intro:
      "Βαρούχ, ascribed to Jeremiah's scribe, gathers a confession of exile, a " +
      "hymn to Wisdom-as-Torah (3:9–4:4), and words of consolation to " +
      "Jerusalem." },
    LJE: { date: "2nd c. BC", intro:
      "The Epistle of Jeremiah is a satirical tract against idolatry, often " +
      "printed as Baruch chapter 6." },
    SUS: { date: "2nd c. BC", intro:
      "Σουσάννα, an Addition to Daniel, tells how the young Daniel exposes two " +
      "corrupt elders and vindicates a falsely accused woman — a celebrated " +
      "story of true judgment." },
    BEL: { date: "2nd c. BC", intro:
      "‘Bel and the Dragon’, an Addition to Daniel, ridicules idol-worship: " +
      "Daniel unmasks the priests of Bel and destroys the dragon." },
    "1MA": { date: "late 2nd c. BC", intro:
      "1 Maccabees is a sober historical account of the Maccabean revolt " +
      "against Seleucid persecution (167–134 BC) and the rededication of the " +
      "temple (Hanukkah). Translated from a lost Hebrew original." },
    "2MA": { date: "late 2nd c. BC", intro:
      "2 Maccabees, composed in Greek, covers a shorter period in a more " +
      "theological, ‘pathetic’ style. It contains key texts on martyrdom, " +
      "resurrection of the body (ch. 7), and prayer for the dead (12:44-45)." },
    "3MA": { date: "1st c. BC", intro:
      "3 Maccabees recounts the deliverance of Egyptian Jews under Ptolemy IV — " +
      "despite its name it does not concern the Maccabees. A story of God's " +
      "rescue of the persecuted." },
    "4MA": { date: "1st c. AD", intro:
      "4 Maccabees is a philosophical homily arguing that ‘devout reason is " +
      "master of the passions’, illustrated by the martyrs of 2 Maccabees 6–7. " +
      "It blends Stoic ethics with Jewish faith and shaped Christian ideals of " +
      "martyrdom." },
    MAN: { date: "2nd c. BC – 1st c. AD", intro:
      "The Prayer of Manasseh is a brief, moving penitential prayer placed on " +
      "the lips of Judah's most wicked king (2 Chr 33). In LXX manuscripts it " +
      "appears among the Odes appended to the Psalter." },
  },

  passages: [
    { code: "GEN", ch: 1, v: 1, vEnd: 5, title: "In the beginning God made the heaven and the earth",
      body: "The Greek ἐν ἀρχῇ ἐποίησεν ὁ Θεός stands behind John 1:1 (ἐν ἀρχῇ ἦν ὁ λόγος). The LXX renders the formless earth as ἀόρατος καὶ ἀκατασκεύαστος — ‘invisible and unformed’ — vocabulary later echoed in Hellenistic-Jewish and Christian cosmology. God's creative word (‘let there be light, and there was light’) becomes the paradigm of creation by the spoken λόγος.",
      nt: "John 1:1-3; 2 Cor 4:6; Heb 11:3.", words: ["logos", "theos"] },

    { code: "EXO", ch: 3, v: 14, title: "ἐγώ εἰμι ὁ Ὤν — I AM THE BEING",
      body: "For the Hebrew ’ehyeh ’ăšer ’ehyeh (‘I am who I am’), the LXX chooses the participle of ‘to be’: ἐγώ εἰμι ὁ Ὤν, ‘I am THE ONE WHO IS / THE BEING’. This move — reading the divine name in the language of being — became foundational for Jewish (Philo) and Christian theology of God as self-existent.",
      mt: "Hebrew: ‘I AM WHO I AM’ (a verb of becoming/being). LXX interprets with the philosophical participle ὁ Ὤν, ‘the One who is’.",
      nt: "Jesus' absolute ‘I am’ (ἐγώ εἰμι) sayings in John (8:58) echo this Greek self-designation.", words: ["ho_on", "ego_eimi", "kyrios"] },

    { code: "LEV", ch: 16, v: 14, vEnd: 15, title: "The mercy-seat (ἱλαστήριον)",
      body: "The LXX renders the golden cover of the ark as ἱλαστήριον, ‘place/means of atonement’. This is the word Paul uses of Christ in Romans 3:25 and Hebrews 9:5 uses of the mercy-seat itself — a direct bridge from the Day of Atonement ritual to the NT interpretation of the cross.",
      nt: "Rom 3:25; Heb 9:5; 1 John 2:2 (ἱλασμός).", words: ["hilasterion", "hagiazo"] },

    { code: "DEU", ch: 6, v: 4, vEnd: 5, title: "The Shema — Hear, O Israel",
      body: "‘Ἄκουε Ἰσραήλ· Κύριος ὁ Θεὸς ἡμῶν Κύριος εἷς ἐστι.’ The LXX supplies the exact words Jesus quotes as the greatest commandment, and its threefold ‘heart, soul, strength’ (with ‘mind’, διάνοια) underlies the Gospel citations.",
      nt: "Mk 12:29-30; Mt 22:37; Lk 10:27.", words: ["kyrios", "agape"] },

    { code: "PSA", ch: 21, v: 1, vEnd: 19, title: "Psalm 21 LXX (=Ps 22): the suffering righteous one",
      body: "This is the passion psalm par excellence. The LXX numbers it Psalm 21 (one behind the Hebrew). Verse 19, ‘they parted my garments among themselves, and cast lots for my clothing’, is quoted verbatim in the Gospels. Note v. 17 LXX ὤρυξαν χεῖράς μου καὶ πόδας — ‘they dug/pierced my hands and feet’ — a reading that differs sharply from the received Hebrew.",
      mt: "MT of v. 16 reads ‘like a lion my hands and feet’; the LXX (with some Hebrew witnesses from Qumran/Nahal Hever) reads a verb, ‘they pierced/dug’.",
      nt: "Mt 27:35,46; Jn 19:24; Heb 2:12 (quoting v. 22).", words: ["kyrios"] },

    { code: "PSA", ch: 22, v: 1, vEnd: 6, title: "Psalm 22 LXX (=Ps 23): The Lord shepherds me",
      body: "Κύριος ποιμαίνει με — ‘the Lord shepherds me’ (LXX numbering, Hebrew Ps 23). The Greek ποιμαίνω supplies the shepherd imagery Jesus takes up in John 10 and that the NT applies to him as ὁ ποιμὴν ὁ καλός. This psalm is the classic illustration of the one-behind LXX Psalm numbering.",
      nt: "Jn 10:11; Heb 13:20; 1 Pet 2:25; Rev 7:17.", words: ["kyrios", "poimaino"] },

    { code: "PSA", ch: 109, v: 1, vEnd: 4, title: "Psalm 109 LXX (=Ps 110): The Lord said to my Lord",
      body: "εἶπεν ὁ Κύριος τῷ Κυρίῳ μου — the most-cited OT verse in the NT. Its Greek, with two ‘Lords’, frames the debate about the Messiah's identity, and v. 4 (‘a priest for ever after the order of Melchizedek’) is the backbone of Hebrews 5–7.",
      nt: "Mt 22:44; Acts 2:34-35; 1 Cor 15:25; Heb 1:13; 5:6; 7:17.", words: ["kyrios", "christos"] },

    { code: "ISA", ch: 7, v: 14, title: "Behold, the virgin shall conceive (ἡ παρθένος)",
      body: "The single most consequential LXX reading. The translators render Hebrew ‘almah (‘young woman’) with the specific Greek παρθένος, ‘virgin’, and read the definite article — ‘THE virgin’. Matthew quotes this Greek form directly as fulfilled in the virginal conception of Jesus.",
      mt: "Hebrew ‘almah denotes a young woman of marriageable age; the LXX's choice of παρθένος makes the virginity explicit.",
      nt: "Mt 1:23 (Ἰδοὺ ἡ παρθένος… καλέσουσι τὸ ὄνομα αὐτοῦ Ἐμμανουήλ).", words: ["parthenos", "emmanouel"] },

    { code: "ISA", ch: 9, v: 6, title: "A child is born — ‘Messenger of Great Counsel’",
      body: "The Greek Isaiah handles the throne-names very differently from the Hebrew, calling the child ‘Messenger of Great Counsel’ (μεγάλης βουλῆς ἄγγελος) and stressing that he brings peace and prosperity to rulers. A vivid example of the Greek translator's interpretive freedom.",
      mt: "Hebrew lists the titles ‘Wonderful Counselor, Mighty God, Everlasting Father, Prince of Peace’; the Old Greek reformulates them into a single title plus a promise of peace." },

    { code: "ISA", ch: 53, v: 1, vEnd: 12, title: "The Suffering Servant",
      body: "The fourth Servant Song, read by the earliest Christians as a prophecy of the atoning death of Jesus. The Greek supplies phrases the NT quotes directly — ‘he was led as a sheep to the slaughter’ (v. 7, Acts 8:32) and ‘he bore the sins of many’ (v. 12). The LXX intensifies the vicarious note: ‘he bears our sins and is pained for us’ (v. 4).",
      mt: "The Greek and Hebrew broadly agree here, but the LXX heightens several expressions of substitution and healing (e.g. v. 5, ‘by his bruise we were healed’).",
      nt: "Acts 8:32-33; Mt 8:17; 1 Pet 2:22-25; Rom 4:25.", words: ["pais", "hamartia"] },

    { code: "JON", ch: 1, v: 17, vEnd: 17, title: "The great sea-monster (κῆτος)",
      body: "The LXX renders the ‘great fish’ as κῆτος μέγα, ‘a great sea-monster’. This is the exact word on Jesus' lips in Matthew 12:40, where Jonah's three days ‘in the belly of the κῆτος’ become the sign of the Son of Man's three days in the heart of the earth.",
      nt: "Mt 12:40 (ἐν τῇ κοιλίᾳ τοῦ κήτους).", words: ["ketos"] },

    { code: "JON", ch: 2, v: 1, vEnd: 9, title: "Jonah's prayer from the deep",
      body: "From ‘the belly of Hades’ (ἐξ κοιλίας ᾅδου, v. 2 LXX) Jonah cries out and is heard. The Greek ᾅδης renders Hebrew Sheol and supplies the NT word for the realm of the dead; the psalm-like prayer models deliverance from death.",
      words: ["hades"] },

    { code: "WIS", ch: 2, v: 12, vEnd: 20, title: "The righteous one who calls God his father",
      body: "The ungodly plot against ‘the righteous one’ (ὁ δίκαιος) precisely because he ‘professes to have knowledge of God, and calls himself a child of the Lord… and boasts that God is his father’ (vv. 13,16). ‘Let us condemn him to a shameful death… for if the righteous man is God's son, He will help him’ (vv. 18,20). The Gospel passion narratives echo this language closely (cf. Mt 27:43).",
      nt: "Mt 27:41-43; cf. Jn 19:7.", words: ["dikaiosyne"] },

    { code: "SIR", ch: 24, v: 1, vEnd: 12, title: "Wisdom's self-praise (‘I came forth from the mouth of the Most High’)",
      body: "Personified Wisdom describes her procession from God and her dwelling in Israel/Zion. This chapter, with Proverbs 8 and Wisdom 7, forms the background to the NT presentation of Christ as the pre-existent Word and Wisdom who ‘tabernacled among us’ (John 1:14).",
      nt: "Jn 1:1-14; Col 1:15-17.", words: ["sophia", "logos"] },

    { code: "DAG", ch: 7, v: 13, vEnd: 14, title: "One like a son of man",
      body: "In Greek Daniel, ‘one like a son of man’ comes with the clouds of heaven and receives everlasting dominion. The ‘Theodotion’ wording (ὡς υἱὸς ἀνθρώπου) underlies Jesus' favorite self-designation and the throne visions of Revelation.",
      nt: "Mt 26:64; Mk 14:62; Rev 1:7,13.", words: ["hyios_anthropou"] },
  ],
};
