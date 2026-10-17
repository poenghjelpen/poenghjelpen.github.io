/* Poenghjelpen – søk, kalkulator, filter og «Kommer du inn?»-sjekk. Ingen sporing. */
(function () {
  "use strict";
  var BASE = document.documentElement.getAttribute("data-base") || "/";
  var LAGRET = "ph-poeng";

  function $(s, el) { return (el || document).querySelector(s); }
  function $$(s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); }
  function tall(x) {
    return Number(x).toLocaleString("nb-NO", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
  }
  function lesTall(s) {
    if (s === null || s === undefined) return NaN;
    s = String(s).trim().replace(",", ".");
    return s === "" ? NaN : Number(s);
  }
  function norm(s) { return String(s).toLowerCase(); }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function grenseTekst(g) {
    if (g === null || g === undefined) return "–";
    if (g < 0) return "ikke oppgitt";
    if (g === 0) return "alle kvalifiserte";
    return tall(g);
  }
  function lagre(obj) { try { localStorage.setItem(LAGRET, JSON.stringify(obj)); } catch (e) {} }
  function hent() { try { return JSON.parse(localStorage.getItem(LAGRET) || "null"); } catch (e) { return null; } }

  /* ---------- Mørk modus ---------- */
  var temaKnapp = $("#tema");
  if (temaKnapp) {
    temaKnapp.addEventListener("click", function () {
      var root = document.documentElement;
      var mork = root.getAttribute("data-theme") === "dark" ||
        (!root.getAttribute("data-theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
      var ny = mork ? "light" : "dark";
      root.setAttribute("data-theme", ny);
      try { localStorage.setItem("ph-tema", ny); } catch (e) {}
    });
  }

  /* ---------- Studieindeks (lastes først når den trengs) ---------- */
  // rad: [kode, navn, lærested, sted, fagområde, grenseFørstegang, grenseOrdinær, url, særskilt]
  var indeks = null, venter = null;
  function hentIndeks() {
    if (indeks) return Promise.resolve(indeks);
    if (!venter) {
      venter = fetch(BASE + "assets/studier.json").then(function (r) { return r.json(); }).then(function (d) {
        indeks = d.map(function (r) {
          return { kode: r[0], navn: r[1], lared: r[2], sted: r[3], fag: r[4], f: r[5], o: r[6],
                   url: BASE + r[7], saer: r[8] === 1,
                   sok: norm(r[0] + " " + r[1] + " " + r[2] + " " + r[3] + " " + r[4] + " " + (r[9] || "")) };
        });
        return indeks;
      });
    }
    return venter;
  }

  function studieLi(s, ekstra) {
    return '<li><a href="' + esc(s.url) + '">' + esc(s.navn) + "</a>" +
      '<span class="meta">' + esc(s.lared) + ", " + esc(s.sted) + "</span>" +
      '<span class="grenser">Førstegang: ' + grenseTekst(s.f) + " · Ordinær: " + grenseTekst(s.o) + "</span>" +
      (ekstra || "") + "</li>";
  }

  /* ---------- Søk på forsiden ---------- */
  var sok = $("#sok");
  if (sok) {
    var sokListe = $("#sok-treff");
    var kjorSok = function () {
      var q = norm(sok.value).trim();
      if (q.length < 2) { sokListe.innerHTML = ""; return; }
      hentIndeks().then(function (d) {
        var ord = q.split(/\s+/);
        var treff = d.filter(function (s) { return ord.every(function (o) { return s.sok.indexOf(o) !== -1; }); });
        sokListe.innerHTML = treff.length
          ? treff.slice(0, 25).map(function (s) { return studieLi(s); }).join("") +
            (treff.length > 25 ? '<li class="mer">' + treff.length + ' treff – <a href="' + BASE + "alle-studier/?q=" +
              encodeURIComponent(sok.value) + '">se alle</a></li>' : "")
          : '<li class="mer">Ingen treff. Prøv et annet ord, for eksempel «sykepleie» eller «Bergen».</li>';
      });
    };
    sok.addEventListener("input", kjorSok);
    sok.addEventListener("focus", hentIndeks);
  }

  /* ---------- Filter på «Alle studier» ---------- */
  var filter = $("#filter");
  if (filter) {
    var rader = $$("#alle tbody tr");
    var teller = $("#antall");
    var fq = $("#f-sok"), fl = $("#f-lared"), ff = $("#f-fag");
    var params = new URLSearchParams(location.search);
    if (params.get("q")) fq.value = params.get("q");
    var oppdater = function () {
      var ord = norm(fq.value).trim().split(/\s+/).filter(Boolean);
      var l = fl.value, f = ff.value, n = 0;
      rader.forEach(function (tr) {
        var vis = (!l || tr.getAttribute("data-l") === l) && (!f || tr.getAttribute("data-f") === f) &&
          ord.every(function (o) { return tr.getAttribute("data-s").indexOf(o) !== -1; });
        tr.hidden = !vis;
        if (vis) n++;
      });
      teller.textContent = n;
    };
    [fq, fl, ff].forEach(function (el) { el.addEventListener("input", oppdater); });
    oppdater();
  }

  /* ---------- «Kommer du inn?» på studiesidene ---------- */
  var sjekk = $("#sjekk");
  if (sjekk) {
    var gF = lesTall(sjekk.getAttribute("data-f")), gO = lesTall(sjekk.getAttribute("data-o"));
    if (isNaN(gF)) gF = null;
    if (isNaN(gO)) gO = null;
    var inSkole = $("#s-skole", sjekk), inKonk = $("#s-konk", sjekk), ut = $("#s-ut");
    var lagra = hent();
    if (lagra) {
      inSkole.value = String(lagra.skolepoeng).replace(".", ",");
      inKonk.value = String(lagra.konkurransepoeng).replace(".", ",");
    }
    var tekst = function (kvote, poeng, g, poengNavn) {
      if (isNaN(poeng)) return "";
      var r = Poeng.kommerInn(poeng, g);
      if (r === "ukjent") return "<li><b>" + kvote + ":</b> Grensen er ikke oppgitt, så vi kan ikke si noe sikkert.</li>";
      if (r === "alle") return '<li class="ok"><b>' + kvote + ":</b> Ja – alle kvalifiserte kom inn i fjor.</li>";
      if (r === "ja") return '<li class="ok"><b>' + kvote + ":</b> Ja! Med " + tall(poeng) + " " + poengNavn +
        " er du " + tall(poeng - g) + " poeng over fjorårets grense.</li>";
      return '<li class="nei"><b>' + kvote + ":</b> Ikke med fjorårets grense. Du mangler " + tall(g - poeng) + " poeng.</li>";
    };
    var kjorSjekk = function (e) {
      if (e) e.preventDefault();
      var s = lesTall(inSkole.value), k = lesTall(inKonk.value);
      if (isNaN(s) && isNaN(k)) { ut.innerHTML = '<p class="muted">Skriv inn minst én poengsum.</p>'; return; }
      ut.innerHTML = "<ul>" + tekst("Førstegangskvoten", s, gF, "skolepoeng") +
        tekst("Ordinær kvote", isNaN(k) ? s : k, gO, "konkurransepoeng") + "</ul>" +
        '<p class="muted small">Husk at grensene endrer seg fra år til år, og at du også må oppfylle opptakskravene.</p>';
    };
    sjekk.addEventListener("submit", kjorSjekk);
    if (lagra) kjorSjekk();
  }

  /* ---------- Poengkalkulatoren ---------- */
  var kalk = $("#kalk");
  if (kalk) {
    var res = $("#resultat");
    var visAntall = 30;
    var siste = null;

    var lesSkjema = function () {
      var v = function (n) { var el = kalk.elements[n]; return el ? el.value : ""; };
      var antall = {};
      for (var k = 2; k <= 6; k++) antall[k] = lesTall(v("k" + k)) || 0;
      var snitt = lesTall(v("snitt"));
      var fraKarakterer = Poeng.snittFraKarakterer(antall);
      if (isNaN(snitt)) snitt = fraKarakterer;
      return {
        aar: Number(v("aar")), fodt: Number(v("fodt")), snitt: snitt, fraKarakterer: fraKarakterer,
        fgv: kalk.elements.fgv.checked,
        realfag: $$('input[name="realfag"]:checked', kalk).map(function (el) { return el.value; }),
        sprak: $$('select[name="sprak"]', kalk).map(function (el) { return Number(el.value); }),
        folkehogskole: kalk.elements.fhs.checked, militaer: kalk.elements.mil.checked,
        hoyereUtd: Number(v("hu"))
      };
    };

    var linje = function (navn, verdi, klasse) {
      return '<tr class="' + (klasse || "") + '"><th scope="row">' + navn + "</th><td>" + tall(verdi) + "</td></tr>";
    };

    var visTreff = function () {
      if (!siste) return;
      var p = siste;
      hentIndeks().then(function (d) {
        var fagValg = $("#treff-fag"), q = norm($("#treff-sok").value).trim();
        var inn = [], nesten = [];
        d.forEach(function (s) {
          if (s.saer) return;
          if (fagValg.value && s.fag !== fagValg.value) return;
          if (q && s.sok.indexOf(q) === -1) return;
          var viaF = p.forstegang && s.f !== null && s.f >= 0 && p.skolepoeng >= s.f;
          var viaO = s.o !== null && s.o >= 0 && p.konkurransepoeng >= s.o;
          if (viaF || viaO) {
            var topp = Math.max(viaF ? s.f : 0, viaO ? s.o : 0);
            inn.push({ s: s, via: viaF && !viaO ? "førstegangskvoten" : (viaO && !viaF ? "ordinær kvote" : "begge kvoter"), topp: topp });
          } else {
            var gap = Infinity;
            if (p.forstegang && s.f > 0) gap = Math.min(gap, s.f - p.skolepoeng);
            if (s.o > 0) gap = Math.min(gap, s.o - p.konkurransepoeng);
            if (gap > 0 && gap <= 3) nesten.push({ s: s, gap: gap });
          }
        });
        inn.sort(function (a, b) { return b.topp - a.topp || a.s.navn.localeCompare(b.s.navn, "nb"); });
        nesten.sort(function (a, b) { return a.gap - b.gap; });
        $("#treff-antall").textContent = inn.length;
        $("#treff-liste").innerHTML = inn.slice(0, visAntall).map(function (t) {
          return studieLi(t.s, '<span class="via">Inn via ' + t.via + "</span>");
        }).join("") || '<li class="mer">Ingen studier matcher. Prøv å fjerne filteret.</li>';
        $("#treff-mer").hidden = inn.length <= visAntall;
        $("#nesten-liste").innerHTML = nesten.slice(0, 15).map(function (t) {
          return studieLi(t.s, '<span class="via nei">Mangler ' + tall(t.gap) + " poeng</span>");
        }).join("") || '<li class="mer">Ingen studier i denne gruppen.</li>';
      });
    };

    var kjorKalk = function () {
      var inp = lesSkjema();
      $("#snitt-ut").textContent = inp.fraKarakterer ? "Snitt fra karakterene: " + inp.fraKarakterer.toFixed(2).replace(".", ",") : "";
      if (!inp.snitt || isNaN(inp.snitt) || inp.snitt < 2 || inp.snitt > 6) {
        res.hidden = true; siste = null; return;
      }
      var p = Poeng.beregn(inp);
      siste = p;
      lagre({ skolepoeng: p.skolepoeng, konkurransepoeng: p.konkurransepoeng });
      res.hidden = false;
      $("#poengtabell").innerHTML =
        linje("Karakterpoeng (snitt × 10)", p.karakterpoeng) +
        linje("Realfagspoeng", p.realfagspoeng) +
        linje("Språkpoeng", p.sprakpoeng) +
        (p.ekstraKappet ? '<tr><td colspan="2" class="small muted">Du kan få maks 4 realfags- og språkpoeng til sammen, så bare ' +
          tall(p.ekstraBrukt) + " teller.</td></tr>" : "") +
        linje("Skolepoeng", p.skolepoeng, "sum") +
        linje("Alderspoeng", p.alderspoeng) +
        linje("Tilleggspoeng", p.tilleggspoeng) +
        linje("Konkurransepoeng", p.konkurransepoeng, "sum");
      $("#kvoteinfo").innerHTML = p.forstegang
        ? "Du konkurrerer i <b>førstegangskvoten</b> med " + tall(p.skolepoeng) + " skolepoeng og i <b>ordinær kvote</b> med " +
          tall(p.konkurransepoeng) + " konkurransepoeng. Du får tilbud i den kvoten du kommer best ut i."
        : "Du konkurrerer bare i <b>ordinær kvote</b> med " + tall(p.konkurransepoeng) + " konkurransepoeng" +
          (kalk.elements.fgv.checked ? " (du er over aldersgrensen på " + p.aldersgrense + " år for førstegangskvoten)." : ".");
      $("#regelinfo").textContent = p.nyeRegler
        ? "Beregnet med de nye reglene fra 2028 (forenklet). Grensene under er fra 2026, da de gamle reglene gjaldt, så sammenligningen er bare en pekepinn."
        : "Beregnet med reglene for opptaket i " + inp.aar + ".";
      visTreff();
    };

    kalk.addEventListener("input", kjorKalk);
    kalk.addEventListener("submit", function (e) { e.preventDefault(); kjorKalk(); });
    $("#treff-sok").addEventListener("input", visTreff);
    $("#treff-fag").addEventListener("input", visTreff);
    $("#treff-mer").addEventListener("click", function () { visAntall += 30; visTreff(); });
    kjorKalk();
  }
})();
