/* Poengberegning etter reglene til Samordna opptak.
   Kilde: samordnaopptak.no/universitet-og-hogskole/poengberegning/ (lest oktober 2026).
   Opptak 2027: dagens regler. Opptak 2028: ny opptaksforskrift (forenklet modell). */
(function (root) {
  "use strict";

  // fag: [gruppe, poeng]. Fag i samme gruppe overlapper og gir maks 1,5 poeng til sammen.
  var REALFAG = {
    S1: ["mat", 0.5], S2: ["mat", 0.5], R1: ["mat", 0.5], R2: ["mat", 1],
    FY1: ["fy", 0.5], FY2: ["fy", 1],
    KJ1: ["kj", 0.5], KJ2: ["kj", 0.5],
    BI1: ["bi", 0.5], BI2: ["bi", 0.5],
    GEO1: ["geo", 0.5], GEO2: ["geo", 0.5],
    IT1: ["it", 0.5], IT2: ["it", 0.5],
    TOF1: ["tof", 0.5], TOF2: ["tof", 0.5],
    NAT: ["nat", 0.5]
  };

  function r2(x) { return Math.round(x * 100 + 1e-9) / 100; }

  function snittFraKarakterer(antall) {
    // antall: {2: n, 3: n, ...}
    var sum = 0, n = 0;
    for (var k = 2; k <= 6; k++) {
      var c = Number(antall[k]) || 0;
      sum += c * k; n += c;
    }
    return n ? sum / n : null;
  }

  /* inp = {aar, fodt, snitt, fgv (bool), realfag: ["R2", ...], sprak: [0.5, 1, ...],
            folkehogskole, militaer (bool), hoyereUtd (0|1|2)} */
  function beregn(inp) {
    var nye = inp.aar >= 2028;
    var alder = inp.aar - inp.fodt;

    var karakterpoeng = r2(inp.snitt * 10);

    var grupper = {};
    (inp.realfag || []).forEach(function (f) {
      var d = REALFAG[f];
      if (!d || (nye && f === "NAT")) return;
      grupper[d[0]] = (grupper[d[0]] || 0) + d[1];
    });
    var realfag = 0;
    Object.keys(grupper).forEach(function (g) { realfag += Math.min(1.5, grupper[g]); });

    var sprak = 0;
    (inp.sprak || []).forEach(function (p) { sprak += Math.min(1.5, Number(p) || 0); });

    if (nye) {
      realfag = Math.min(2, realfag / 2); // poengene halveres, maks 2
      sprak = 0;                          // språkpoeng fjernes
    }
    var ekstraMaks = 4;
    var ekstra = Math.min(ekstraMaks, realfag + sprak);

    var alderspoeng = 0;
    if (!nye && alder >= 20) alderspoeng = Math.min(8, (alder - 19) * 2);

    var tillegg;
    if (nye) {
      tillegg = inp.militaer ? 1 : 0;
    } else {
      tillegg = Math.min(2, (inp.folkehogskole ? 2 : 0) + (inp.militaer ? 2 : 0) + (Number(inp.hoyereUtd) || 0));
    }

    var skolepoeng = r2(karakterpoeng + ekstra);
    var aldersgrense = nye ? 23 : 21;
    return {
      nyeRegler: nye,
      karakterpoeng: karakterpoeng,
      realfagspoeng: r2(realfag),
      sprakpoeng: r2(sprak),
      ekstraBrukt: r2(ekstra),
      ekstraKappet: realfag + sprak > ekstraMaks,
      skolepoeng: skolepoeng,
      alderspoeng: alderspoeng,
      tilleggspoeng: tillegg,
      konkurransepoeng: r2(skolepoeng + alderspoeng + tillegg),
      aldersgrense: aldersgrense,
      forstegang: !!inp.fgv && alder <= aldersgrense
    };
  }

  // Sammenligner poeng med en grense. 0 = alle kvalifiserte, -1/null = ukjent.
  function kommerInn(poeng, grense) {
    if (grense === null || grense === undefined || grense < 0) return "ukjent";
    if (grense === 0) return "alle";
    return poeng >= grense ? "ja" : "nei";
  }

  // Har du matematikk R1 (eller R2), eller både S1 og S2?
  function harMatteKrav(realfag) {
    var r = realfag || [];
    return r.indexOf("R1") !== -1 || r.indexOf("R2") !== -1 || (r.indexOf("S1") !== -1 && r.indexOf("S2") !== -1);
  }

  /* Private høyskoler med eget opptak: oppfyller du minimumskravet?
     st = {m: {alle} | {forste, ordinar} | {}, ingen: 0/1, fag: 0/1}
     p  = {skolepoeng, konkurransepoeng, fgv (har førstegangsvitnemål), matte (R1 eller S1+S2)} */
  function privatStatus(st, p) {
    var m = st.m || {}, poeng, mangler = null;
    if (m.alle !== undefined) {
      // Med førstegangsvitnemål gjelder skolepoeng, ellers konkurransepoeng
      var verdi = p.fgv ? p.skolepoeng : p.konkurransepoeng;
      poeng = verdi >= m.alle ? "ja" : "nei";
      if (poeng === "nei") mangler = r2(m.alle - verdi);
    } else if (m.forste !== undefined) {
      var viaF = p.fgv && p.skolepoeng >= m.forste, viaO = p.konkurransepoeng >= m.ordinar;
      poeng = viaF || viaO ? "ja" : "nei";
      if (poeng === "nei") mangler = r2(Math.min(p.fgv ? m.forste - p.skolepoeng : Infinity, m.ordinar - p.konkurransepoeng));
    } else {
      poeng = st.ingen ? "ingen" : "ukjent";
    }
    var fag = st.fag ? (p.matte ? "ja" : "nei") : "ingen";
    var samlet = (poeng === "nei" || fag === "nei") ? "nei" : (poeng === "ukjent" ? "ukjent" : "ja");
    return { poeng: poeng, fag: fag, samlet: samlet, mangler: mangler };
  }

  var api = { beregn: beregn, kommerInn: kommerInn, snittFraKarakterer: snittFraKarakterer, REALFAG: REALFAG,
              harMatteKrav: harMatteKrav, privatStatus: privatStatus };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Poeng = api;
})(this);
