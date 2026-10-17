"""Bygger Poenghjelpen som en statisk nettside i mappen site/.

Bruk:  python3 build.py
Dataene leses fra data/poenggrenser.json (lages av fetch_data.py).
"""

# ======================================================================
# ENDRE DENNE: nettadressen der siden skal ligge. Må slutte med «/».
# GitHub Pages: https://BRUKERNAVN.github.io/REPONAVN/
SITE_URL = "https://poenghjelpen.github.io/"
# ======================================================================

import hashlib
import html
import json
import re
import shutil
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE_NAVN = "Poenghjelpen"
BASE = urlparse(SITE_URL).path or "/"
if not BASE.endswith("/"):
    BASE += "/"
I_DAG = date.today().isoformat()

LAERESTEDER = {
    "AHO": ("AHO", "Arkitektur- og designhøgskolen i Oslo"),
    "AHS": ("Ansgar", "Ansgar høyskole"),
    "DMMH": ("DMMH", "Dronning Mauds Minne Høgskole"),
    "FIH": ("Fjellhaug", "Fjellhaug Internasjonale Høgskole"),
    "HIM": ("HiMolde", "Høgskolen i Molde"),
    "HIØ": ("HiØ", "Høgskolen i Østfold"),
    "HVL": ("HVL", "Høgskulen på Vestlandet"),
    "HVO": ("HVO", "Høgskulen i Volda"),
    "INN": ("INN", "Universitetet i Innlandet"),
    "LDH": ("LDH", "Lovisenberg diakonale høgskole"),
    "MF": ("MF", "MF vitenskapelig høyskole"),
    "NHH": ("NHH", "Norges Handelshøyskole"),
    "NIH": ("NIH", "Norges idrettshøgskole"),
    "NLA": ("NLA", "NLA Høgskolen"),
    "NMBU": ("NMBU", "Norges miljø- og biovitenskapelige universitet"),
    "NORD": ("Nord", "Nord universitet"),
    "NTNU": ("NTNU", "Norges teknisk-naturvitenskapelige universitet"),
    "OSLOMET": ("OsloMet", "OsloMet – storbyuniversitetet"),
    "PHS": ("PHS", "Politihøgskolen"),
    "SA/SH": ("Sámi allaskuvla", "Sámi allaskuvla / Samisk høgskole"),
    "UIA": ("UiA", "Universitetet i Agder"),
    "UIB": ("UiB", "Universitetet i Bergen"),
    "UIO": ("UiO", "Universitetet i Oslo"),
    "UIS": ("UiS", "Universitetet i Stavanger"),
    "UIT": ("UiT", "UiT Norges arktiske universitet"),
    "USN": ("USN", "Universitetet i Sørøst-Norge"),
    "VID": ("VID", "VID vitenskapelige høgskole"),
}

FAGOMRADER = {
    "ESTETISK": "Estetiske fag, kunst og musikk",
    "HELSEFAG - ANNET": "Helsefag (andre)",
    "HELSEFAG - AUDIO": "Audiologi",
    "HELSEFAG - BARNEVER": "Barnevern",
    "HELSEFAG - BIOING": "Bioingeniør",
    "HELSEFAG - ERGO": "Ergoterapi",
    "HELSEFAG - ERNÆRING": "Ernæring",
    "HELSEFAG - FARMASI": "Farmasi",
    "HELSEFAG - FYSIO": "Fysioterapi",
    "HELSEFAG - MEDISIN": "Medisin",
    "HELSEFAG - ODONT": "Odontologi og tannhelse",
    "HELSEFAG - ORTOPEDI": "Ortopediingeniør",
    "HELSEFAG - RADIO": "Radiografi",
    "HELSEFAG - RESEPTAR": "Reseptar",
    "HELSEFAG - SOSIONOM": "Sosionom",
    "HELSEFAG - SYKEPL": "Sykepleie",
    "HELSEFAG - VERNEPL": "Vernepleie",
    "HELSEFAG - VETERIN": "Veterinær",
    "HISTORIE": "Historie, religion og filosofi",
    "IDRETT": "Idrett",
    "INFOTEKN": "Informasjonsteknologi",
    "JUS": "Jus",
    "LANDOGHAVBRUK": "Landbruk og havbruk",
    "LÆRER - ANNET": "Lærerutdanning (andre)",
    "LÆRER - BHGLÆRER": "Barnehagelærer",
    "LÆRER - GLU1-7": "Grunnskolelærer 1–7",
    "LÆRER - GLU5-10": "Grunnskolelærer 5–10",
    "LÆRER - LEKTOR 8-13": "Lektor 8–13",
    "LÆRER - LUPE1-13": "Praktiske og estetiske fag 1–13 (lærer)",
    "LÆRER - YFAGLÆRER": "Yrkesfaglærer",
    "MEDIEFAG": "Medier og kommunikasjon",
    "PEDFAG": "Pedagogikk",
    "REALFAG": "Realfag",
    "REISELIV": "Reiseliv",
    "SAMFUNN": "Samfunnsfag",
    "SPRÅK": "Språk og litteratur",
    "TEKNO - ANNET": "Teknologi (andre)",
    "TEKNO - ARKITEKT": "Arkitektur",
    "TEKNO - INGENIØR": "Ingeniør",
    "TEKNO - MARITIM": "Maritime fag",
    "TEKNO - SIVING": "Sivilingeniør",
    "ØKADM": "Økonomi og administrasjon",
}
FAGGRUPPER = {"HELSEFAG": "Helse og sosial", "LÆRER": "Lærer og pedagogikk",
              "TEKNO": "Teknologi og arkitektur"}

REALFAG_VALG = [("S1", "Matematikk S1"), ("S2", "Matematikk S2"), ("R1", "Matematikk R1"), ("R2", "Matematikk R2"),
                ("FY1", "Fysikk 1"), ("FY2", "Fysikk 2"), ("KJ1", "Kjemi 1"), ("KJ2", "Kjemi 2"),
                ("BI1", "Biologi 1"), ("BI2", "Biologi 2"), ("GEO1", "Geofag 1"), ("GEO2", "Geofag 2"),
                ("IT1", "Informasjonsteknologi 1"), ("IT2", "Informasjonsteknologi 2"),
                ("TOF1", "Teknologi og forskningslære 1"), ("TOF2", "Teknologi og forskningslære 2"),
                ("NAT", "Vg3 naturbruk")]


# ---------------------------------------------------------------- hjelpere
def e(s):
    return html.escape(str(s), quote=True)


def slug(s):
    s = s.lower()
    for a, b in (("æ", "ae"), ("ø", "o"), ("å", "a"), ("á", "a"), ("é", "e"), ("ü", "u"), ("ö", "o"), ("ä", "a")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def tall(x):
    """47.3 -> «47,3», 45.0 -> «45,0», 142.97 -> «142,97»."""
    s = f"{x:.2f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s.replace(".", ",")


def desimal(x):
    """Karaktersnitt med to desimaler og komma: 4.125 -> «4,13»."""
    return f"{x:.2f}".replace(".", ",")


def grense(g):
    if g is None:
        return "–"
    if g < 0:
        return "Ikke oppgitt"
    if g == 0:
        return "Alle kvalifiserte"
    return tall(g)


def har_tall(g):
    return g is not None and g > 0


def url(path):
    return BASE + path


def velg(kode, alternativer):
    """Velger en tekstvariant stabilt ut fra studiekoden, så tekstene varierer mellom sidene."""
    h = int(hashlib.md5(kode.encode()).hexdigest(), 16)
    return alternativer[h % len(alternativer)]


# ---------------------------------------------------------------- data
def last_data():
    d = json.loads((ROOT / "data" / "poenggrenser.json").read_text(encoding="utf-8"))
    studier = []
    for s in d["studier"]:
        s = dict(s)
        s["saerskilt"] = s["studienavn"].endswith("*") or any(
            v is not None and v > 90 for r in ("hoved", "supplering") for v in s[r].values())
        s["navn"] = s["studienavn"].rstrip("*").strip()
        kort, langt = LAERESTEDER.get(s["laerested"], (s["laerested"], s["laerested"]))
        s["lkort"], s["llangt"] = kort, langt
        s["fagnavn"] = FAGOMRADER.get(s["fagomrade"], s["fagomrade"].capitalize())
        s["url"] = f"studium/{slug(s['navn'])}-{slug(kort)}-{slug(s['studiested'])}-{s['studiekode']}/"
        s["f"], s["o"] = s["hoved"]["forste"], s["hoved"]["ordinar"]
        studier.append(s)
    teller = defaultdict(int)
    for s in studier:
        teller[(s["navn"], s["lkort"], s["studiested"])] += 1
    for s in studier:
        # Noen studier har samme navn og sted (f.eks. bachelor og årsstudium) – da skiller studiekoden dem
        s["dup"] = teller[(s["navn"], s["lkort"], s["studiested"])] > 1
    return d, studier


def lared_url(kode):
    return f"larested/{slug(kode)}/"


def fag_url(fag):
    return f"fagomrade/{slug(FAGOMRADER.get(fag, fag))}/"


# ---------------------------------------------------------------- layout
SIDER = []  # for sitemap


def side(path, tittel, beskrivelse, innhold, ekstra_head="", skript=(), i_sitemap=True):
    canonical = SITE_URL + path.removesuffix("index.html")
    if i_sitemap:
        SIDER.append(canonical)
    js = "".join(f'<script src="{url("assets/" + s)}" defer></script>' for s in skript)
    dok = f"""<!doctype html>
<html lang="nb" data-base="{e(BASE)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(tittel)}</title>
<meta name="description" content="{e(beskrivelse)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(tittel)}">
<meta property="og:description" content="{e(beskrivelse)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="nb_NO">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%232453d6'/%3E%3Ctext x='16' y='22' font-size='16' text-anchor='middle' fill='white' font-family='Arial' font-weight='700'%3EP%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{url('assets/style.css')}">
<script>try{{var t=localStorage.getItem("ph-tema");if(t)document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
{ekstra_head}
</head>
<body>
<header class="topp"><div class="wrap">
<a class="logo" href="{url('')}">Poeng<span>hjelpen</span></a>
<nav aria-label="Hovedmeny">
<a href="{url('')}#kalkulator">Kalkulator</a>
<a href="{url('alle-studier/')}">Alle studier</a>
<a class="valgfri" href="{url('om/')}">Om</a>
<button id="tema" type="button" aria-label="Bytt mellom lys og mørk modus" title="Lys/mørk modus">◐</button>
</nav>
</div></header>
<main class="wrap">
{innhold}
</main>
<footer class="bunn"><div class="wrap">
<nav aria-label="Bunnmeny">
<a href="{url('')}">Forside</a>
<a href="{url('alle-studier/')}">Alle studier</a>
<a href="{url('om/')}">Om Poenghjelpen</a>
<a href="{url('personvern/')}">Personvern</a>
</nav>
<p>Poenggrensene kommer fra <a href="https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/poenggrenser.html" rel="noopener">Samordna opptak</a>.
Poenghjelpen er en uavhengig, gratis tjeneste og er ikke tilknyttet Samordna opptak. Sjekk alltid opptakskravene hos lærestedet.</p>
</div></footer>
<script src="{url('assets/poeng.js')}" defer></script>
<script src="{url('assets/app.js')}" defer></script>
{js}
</body>
</html>
"""
    fil = OUT / path if path.endswith(".html") else OUT / path / "index.html"
    fil.parent.mkdir(parents=True, exist_ok=True)
    fil.write_text(dok, encoding="utf-8")


def sti(*ledd):
    deler = [f'<a href="{url("")}">Forside</a>']
    for tekst, lenke in ledd:
        deler.append(f'<a href="{url(lenke)}">{e(tekst)}</a>' if lenke else e(tekst))
    return f'<nav class="sti" aria-label="Brødsmuler">{" › ".join(deler)}</nav>'


def studietabell(studier, vis_lared=True, vis_fag=False):
    rader = []
    for s in studier:
        sted = f'<a href="{url(lared_url(s["laerested"]))}">{e(s["lkort"])}</a>, {e(s["studiested"])}' if vis_lared else e(s["studiested"])
        fag = f'<td><a href="{url(fag_url(s["fagomrade"]))}">{e(s["fagnavn"])}</a></td>' if vis_fag else ""
        rader.append(f'<tr><td><a href="{url(s["url"])}">{e(s["navn"])}</a></td><td>{sted}</td>{fag}'
                     f'<td class="n">{grense(s["f"])}</td><td class="n">{grense(s["o"])}</td></tr>')
    fag_th = "<th>Fagområde</th>" if vis_fag else ""
    sted_th = "Lærested og sted" if vis_lared else "Studiested"
    return (f'<div class="tabell-wrap"><table class="data"><thead><tr><th>Studium</th><th>{sted_th}</th>{fag_th}'
            f'<th class="n">Førstegang</th><th class="n">Ordinær</th></tr></thead><tbody>{"".join(rader)}</tbody></table></div>')


def faq_html(sporsmal):
    deler = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in sporsmal)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in sporsmal]}
    return (f'<section class="faq"><h2>Vanlige spørsmål</h2>{deler}</section>',
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


# ---------------------------------------------------------------- tekstgenerering
class Statistikk:
    def __init__(self, studier):
        self.alle_o = sorted(s["o"] for s in studier if har_tall(s["o"]) and not s["saerskilt"])
        per_fag = defaultdict(list)
        self.samme_navn = defaultdict(list)
        for s in studier:
            if har_tall(s["o"]) and not s["saerskilt"]:
                per_fag[s["fagomrade"]].append(s["o"])
            self.samme_navn[slug(s["navn"])].append(s)
        self.fag_median = {f: statistics.median(v) for f, v in per_fag.items()}

    def persentil(self, o):
        return round(100 * sum(1 for x in self.alle_o if x < o) / len(self.alle_o))


def forklaring(s, st, ar):
    f, o = s["f"], s["o"]
    fs, os_ = s["supplering"]["forste"], s["supplering"]["ordinar"]
    navn, sted, lk = s["navn"], s["studiested"], s["lkort"]
    avsnitt = []

    if s["saerskilt"]:
        avsnitt.append(f"{e(navn)} ved {e(s['llangt'])} rangerer søkerne på en egen måte, blant annet med opptaksprøve. "
                       "Derfor er tallene på en annen skala enn vanlige poenggrenser, og de kan ikke sammenlignes direkte med "
                       "skolepoengene dine. Les om opptaket hos lærestedet.")

    # 1. Hovedtall
    if har_tall(f) and har_tall(o):
        start = velg(s["studiekode"], [
            f"I hovedopptaket {ar} trengte du minst {tall(f)} skolepoeng for å få tilbud på {e(navn)} ({e(lk)}, {e(sted)}) i førstegangskvoten, og {tall(o)} konkurransepoeng i ordinær kvote.",
            f"Poenggrensen for {e(navn)} ved {e(lk)} i {e(sted)} endte på {tall(f)} i førstegangskvoten og {tall(o)} i ordinær kvote i hovedopptaket {ar}.",
            f"Den siste som fikk tilbud om plass på {e(navn)} i {e(sted)} i {ar}, hadde {tall(f)} poeng i førstegangskvoten og {tall(o)} poeng i ordinær kvote.",
        ])
        avsnitt.append(start)
    elif f == 0 and o == 0:
        avsnitt.append(f"I hovedopptaket {ar} fikk alle kvalifiserte søkere tilbud på {e(navn)} ved {e(lk)} i {e(sted)}. "
                       "Det betyr at du kom inn så lenge du oppfylte opptakskravene – poengsummen din spilte ingen rolle.")
    else:
        biter = []
        for kvote, g, poeng in (("førstegangskvoten", f, "skolepoeng"), ("ordinær kvote", o, "konkurransepoeng")):
            if har_tall(g):
                biter.append(f"i {kvote} var grensen {tall(g)} {poeng}")
            elif g == 0:
                biter.append(f"i {kvote} kom alle kvalifiserte søkere inn")
            elif g is not None and g < 0:
                biter.append(f"i {kvote} er grensen ikke oppgitt")
        if biter:
            avsnitt.append(f"For {e(navn)} ved {e(lk)} i {e(sted)} gjaldt dette i hovedopptaket {ar}: " + ", og ".join(biter) + ".")

    # 2. Sammenligning
    if har_tall(o) and not s["saerskilt"]:
        p = st.persentil(o)
        med = st.fag_median.get(s["fagomrade"])
        tekst = f"Grensen i ordinær kvote er høyere enn {p} % av alle studiene i oversikten vår"
        if med and abs(o - med) >= 0.5:
            retning = "over" if o > med else "under"
            tekst += f", og {tall(abs(o - med))} poeng {retning} medianen for {e(s['fagnavn'].lower())} ({tall(med)})"
        avsnitt.append(tekst + ". " + (
            "Det er altså et av de mest ettertraktede studiene." if p >= 90 else
            "Konkurransen er hard, men ikke blant de aller tøffeste." if p >= 70 else
            "Det er et middels konkurranseutsatt studium." if p >= 35 else
            "Det er relativt lett å komme inn sammenlignet med andre studier."))

    # 3. Hva betyr det i karaktersnitt?
    if har_tall(f) and not s["saerskilt"] and f <= 70:
        snitt0 = f / 10
        snitt4 = max(0, (f - 4) / 10)
        tekst = f"Uten realfags- eller språkpoeng tilsvarer {tall(f)} skolepoeng et karaktersnitt på {desimal(snitt0)}"
        if snitt0 > 6:
            tekst = f"{tall(f)} skolepoeng er mer enn du kan få med bare karakterer (maks 60), så du trenger realfags- eller språkpoeng"
        tekst += f". Med fire ekstra poeng (maksimum) holder det med snitt {desimal(snitt4)}."
        avsnitt.append(tekst)

    # 4. Forskjell mellom kvotene
    if har_tall(f) and har_tall(o) and not s["saerskilt"]:
        diff = o - f
        if diff >= 3:
            avsnitt.append(velg(s["studiekode"] + "k", [
                f"Grensen i ordinær kvote var {tall(diff)} poeng høyere enn i førstegangskvoten. Det er vanlig, fordi søkerne i ordinær kvote kan ha alderspoeng og tilleggspoeng i tillegg til skolepoengene.",
                f"Ordinær kvote lå {tall(diff)} poeng over førstegangskvoten. Søkerne der har ofte samlet alderspoeng og tilleggspoeng, så det er normalt at grensen er høyere.",
            ]))
        elif diff <= -1:
            avsnitt.append(f"Litt uvanlig var grensen {tall(-diff)} poeng lavere i ordinær kvote enn i førstegangskvoten. "
                           "Er du ferdig med videregående og har alders- eller tilleggspoeng, kan ordinær kvote være en god vei inn.")
        else:
            avsnitt.append("Grensene i de to kvotene lå tett, så det var omtrent like vanskelig å komme inn i begge.")

    # 5. Supplering
    endringer = []
    for kvote, h, sp in (("førstegangskvoten", f, fs), ("ordinær kvote", o, os_)):
        if har_tall(h) and sp is not None and sp >= 0 and sp != h:
            if sp == 0:
                endringer.append(f"i {kvote} kom alle kvalifiserte inn")
            elif sp < h:
                endringer.append(f"i {kvote} falt grensen til {tall(sp)}")
            else:
                endringer.append(f"i {kvote} endte grensen på {tall(sp)}")
    if endringer:
        avsnitt.append("Etter suppleringsopptaket endret bildet seg: " + ", og ".join(endringer) +
                       ". Det skjer når noen takker nei og plassene går videre til søkere på venteliste.")
    elif har_tall(o) and os_ == o:
        avsnitt.append("Grensen i ordinær kvote var den samme etter suppleringsopptaket.")

    # 6. Samme studium andre steder
    andre = [x for x in st.samme_navn[slug(navn)] if x is not s and har_tall(x["o"]) and not x["saerskilt"]]
    if andre and har_tall(o):
        lav = min(andre, key=lambda x: x["o"])
        hoy = max(andre, key=lambda x: x["o"])
        if len(andre) == 1:
            avsnitt.append(f"«{e(navn)}» tilbys også ved {e(lav['lkort'])} i {e(lav['studiested'])}, der grensen i ordinær kvote var {tall(lav['o'])}.")
        else:
            avsnitt.append(f"Et studium med samme navn finnes ved {len(andre)} andre steder i oversikten. Lavest grense i ordinær kvote hadde "
                           f"{e(lav['lkort'])} i {e(lav['studiested'])} ({tall(lav['o'])}), og høyest {e(hoy['lkort'])} i {e(hoy['studiested'])} ({tall(hoy['o'])}).")
    return avsnitt


# ---------------------------------------------------------------- sider
def studieside(s, st, studier_per_fag, ar):
    navn, sted, lk = s["navn"], s["studiested"], s["lkort"]
    # Unngå «Sykepleie, Oslo, Oslo» når stedet allerede står i studienavnet
    sted_i_navn = sted.lower() in navn.lower()
    tittel = (f"Poenggrense {navn} ({lk}) {ar}" if sted_i_navn else f"Poenggrense {navn}, {sted} ({lk}) {ar}") + (f" – studiekode {s['studiekode']}" if s["dup"] else "")

    def kort_desc(g):
        return "alle kvalifiserte kom inn" if g == 0 else ("ikke oppgitt" if g is None or g < 0 else tall(g))
    beskrivelse = (f"Poenggrensen for {navn} ved {s['llangt']} i {sted} var {kort_desc(s['o'])} i ordinær kvote og "
                   f"{kort_desc(s['f'])} i førstegangskvoten (hovedopptaket {ar})." + (f" Studiekode {s['studiekode']}." if s["dup"] else "") + " Sjekk om du kommer inn.")

    def boks(etikett, g, under):
        klasse = "verdi" if har_tall(g) else "verdi ord"
        return f'<div class="tall"><div class="etikett">{etikett}</div><div class="{klasse}">{grense(g)}</div><div class="under">{under}</div></div>'

    sup = s["supplering"]
    bokser = (boks("Førstegangskvote", s["f"], f"Hovedopptak {ar} · skolepoeng") +
              boks("Ordinær kvote", s["o"], f"Hovedopptak {ar} · konkurransepoeng") +
              boks("Førstegang etter supplering", sup["forste"], "Suppleringsopptak") +
              boks("Ordinær etter supplering", sup["ordinar"], "Suppleringsopptak"))

    tekst = "".join(f"<p>{a}</p>" for a in forklaring(s, st, ar))

    data_f = "" if s["f"] is None else s["f"]
    data_o = "" if s["o"] is None else s["o"]
    sjekk = ""
    if not s["saerskilt"]:
        sjekk = f"""<section class="kort" aria-labelledby="sjekk-h">
<h2 id="sjekk-h">Kommer du inn?</h2>
<p class="muted">Skriv inn poengene dine, eller regn dem ut med <a href="{url('')}#kalkulator">poengkalkulatoren</a> først – da fylles de inn automatisk.</p>
<form id="sjekk" class="sjekk-form" data-f="{data_f}" data-o="{data_o}">
<label>Skolepoeng<input id="s-skole" inputmode="decimal" placeholder="f.eks. 48,5"></label>
<label>Konkurransepoeng<input id="s-konk" inputmode="decimal" placeholder="f.eks. 52,5"></label>
<button class="knapp" type="submit">Sjekk</button>
</form>
<div id="s-ut" aria-live="polite"></div>
</section>"""

    # FAQ
    sporsmal = [
        (f"Hva var poenggrensen for {navn} ved {lk} i {ar}?",
         f"I hovedopptaket {ar} var grensen {grense(s['f']).lower()} i førstegangskvoten og {grense(s['o']).lower()} i ordinær kvote. "
         f"Etter suppleringsopptaket var tallene {grense(sup['forste']).lower()} og {grense(sup['ordinar']).lower()}."),
        ("Hva er forskjellen på førstegangskvoten og ordinær kvote?",
         "I førstegangskvoten konkurrerer du med skolepoengene dine hvis du har førstegangsvitnemål og ikke fyller mer enn 21 år i opptaksåret. "
         "I ordinær kvote konkurrerer alle med konkurransepoeng, som også inkluderer alderspoeng og tilleggspoeng."),
        (f"Blir poenggrensen den samme i {ar + 1}?",
         "Ingen vet det på forhånd. Poenggrensen er poengsummen til den siste som fikk tilbud, så den avhenger av hvor mange som søker og hvor gode "
         "karakterer de har. Bruk fjorårets grense som en pekepinn, ikke en garanti."),
        ("Hva gjør jeg hvis jeg ikke kommer inn?",
         "Du kan stå på venteliste og få tilbud i suppleringsopptaket. Du kan også forbedre karakterer eller ta nye fag som privatist, "
         "eller søke et lignende studium med lavere grense."),
        ("Har studiet spesielle opptakskrav?",
         f"Det står ikke i dataene vi bruker. Sjekk studiets side hos {e(s['llangt'])} eller i søknadsportalen til Samordna opptak."),
    ]
    if 0 in (s["f"], s["o"]):
        sporsmal.insert(1, ("Hva betyr det at alle kvalifiserte kom inn?",
                            "Det betyr at det var nok plasser til alle som oppfylte opptakskravene, så poengsummen var ikke avgjørende."))
    faq, faq_ld = faq_html(sporsmal)

    # Lignende studier
    samme = samme_studium(s, st)
    nabo = []
    if har_tall(s["o"]):
        kandidater = [x for x in studier_per_fag[s["fagomrade"]] if x is not s and har_tall(x["o"]) and x not in samme]
        nabo = sorted(kandidater, key=lambda x: abs(x["o"] - s["o"]))[:8]
    else:
        nabo = [x for x in studier_per_fag[s["fagomrade"]] if x is not s and x not in samme][:8]

    def li(x):
        return (f'<li><a href="{url(x["url"])}">{e(x["navn"])}</a><span class="meta">{e(x["lkort"])}, {e(x["studiested"])}</span>'
                f'<span class="grenser">Førstegang: {grense(x["f"])} · Ordinær: {grense(x["o"])}</span></li>')

    lignende = ""
    if samme:
        lignende += f'<h3>Samme studium andre steder</h3><ul class="studieliste">{"".join(li(x) for x in samme[:12])}</ul>'
    if nabo:
        lignende += f'<h3>Lignende studier innen {e(s["fagnavn"].lower())}</h3><ul class="studieliste">{"".join(li(x) for x in nabo)}</ul>'

    innhold = f"""{sti((s['lkort'], lared_url(s['laerested'])), (navn, None))}
<h1>Poenggrense {e(navn)}</h1>
<p class="muted">{e(s['llangt'])} · {e(sted)} · Studiekode {e(s['studiekode'])} · <a href="{url(fag_url(s['fagomrade']))}">{e(s['fagnavn'])}</a></p>
<div class="tall-grid">{bokser}</div>
{sjekk}
<section><h2>Hva betyr tallene?</h2>{tekst}
<p class="small muted">0 i Samordna opptaks tall betyr at alle kvalifiserte søkere fikk tilbud. «Ikke oppgitt» betyr at grensen ikke er publisert.</p></section>
{faq}
<section><h2>Lignende studier</h2>{lignende}
<p><a href="{url(lared_url(s['laerested']))}">Alle studier ved {e(s['llangt'])}</a> · <a href="{url(fag_url(s['fagomrade']))}">Alle studier innen {e(s['fagnavn'].lower())}</a></p></section>
"""
    side(s["url"], tittel, beskrivelse, innhold, ekstra_head=faq_ld)


def samme_studium(s, st):
    """Samme studienavn ved andre læresteder/steder."""
    return [x for x in st.samme_navn[slug(s["navn"])] if x is not s]


def snitt(verdier):
    v = [x for x in verdier if har_tall(x)]
    return statistics.median(v) if v else None


def larestedside(kode, liste, ar):
    kort, langt = LAERESTEDER.get(kode, (kode, kode))
    liste = sorted(liste, key=lambda s: (s["navn"], s["studiested"]))
    tall_o = [s for s in liste if har_tall(s["o"]) and not s["saerskilt"]]
    topp = sorted(tall_o, key=lambda s: -s["o"])[:5]
    steder = sorted({s["studiested"] for s in liste})
    fag = sorted({s["fagomrade"] for s in liste}, key=lambda f: FAGOMRADER.get(f, f))
    med = snitt(s["o"] for s in tall_o)
    alle_inn = sum(1 for s in liste if s["o"] == 0)
    intro = (f"{e(langt)} hadde {len(liste)} studier i hovedopptaket {ar}, fordelt på {len(steder)} studiested"
             f"{'er' if len(steder) > 1 else ''} ({e(', '.join(steder))}).")
    if med:
        intro += f" Mediangrensen i ordinær kvote var {tall(med)} poeng."
    if alle_inn:
        intro += f" På {alle_inn} av studiene kom alle kvalifiserte inn i ordinær kvote."
    topptekst = ""
    if topp:
        topptekst = "<p>Høyest grense i ordinær kvote: " + ", ".join(
            f'<a href="{url(s["url"])}">{e(s["navn"])}</a> ({tall(s["o"])})' for s in topp) + ".</p>"
    faglenker = " · ".join(f'<a href="{url(fag_url(f))}">{e(FAGOMRADER.get(f, f))}</a>' for f in fag)
    innhold = f"""{sti(("Læresteder", "#laresteder"), (kort, None))}
<h1>Poenggrenser {e(langt)} {ar}</h1>
<p>{intro}</p>{topptekst}
<p class="small">Fagområder: {faglenker}</p>
{studietabell(liste, vis_lared=False, vis_fag=True)}"""
    side(lared_url(kode), f"Poenggrenser {langt} ({kort}) {ar} – alle studier",
         f"Se poenggrensene for alle {len(liste)} studier ved {langt} i {ar}, i førstegangskvoten og ordinær kvote.", innhold)


def fagside(fag, liste, alle_fag, ar):
    navn = FAGOMRADER.get(fag, fag)
    liste = sorted(liste, key=lambda s: (-(s["o"] if har_tall(s["o"]) else -1), s["navn"]))
    tall_o = [s for s in liste if har_tall(s["o"]) and not s["saerskilt"]]
    med = snitt(s["o"] for s in tall_o)
    lav = min(tall_o, key=lambda s: s["o"]) if tall_o else None
    hoy = max(tall_o, key=lambda s: s["o"]) if tall_o else None
    larer = sorted({s["laerested"] for s in liste}, key=lambda k: LAERESTEDER.get(k, (k,))[0])
    intro = f"Det var {len(liste)} studier innen {e(navn.lower())} i hovedopptaket {ar}, ved {len(larer)} læresteder."
    if med:
        intro += f" Mediangrensen i ordinær kvote var {tall(med)} poeng."
    if hoy and lav and hoy is not lav:
        intro += (f' Høyest var <a href="{url(hoy["url"])}">{e(hoy["navn"])} ({e(hoy["lkort"])}, {e(hoy["studiested"])})</a> med {tall(hoy["o"])}, '
                  f'og lavest (blant studier med poenggrense) <a href="{url(lav["url"])}">{e(lav["navn"])} ({e(lav["lkort"])}, {e(lav["studiested"])})</a> med {tall(lav["o"])}.')
    alle_inn = sum(1 for s in liste if s["o"] == 0)
    if alle_inn:
        intro += f" På {alle_inn} studier kom alle kvalifiserte inn."
    larlenker = " · ".join(f'<a href="{url(lared_url(k))}">{e(LAERESTEDER.get(k, (k,))[0])}</a>' for k in larer)
    andre = " · ".join(f'<a href="{url(fag_url(f))}">{e(FAGOMRADER.get(f, f))}</a>' for f in alle_fag if f != fag)
    innhold = f"""{sti(("Fagområder", "#fagomrader"), (navn, None))}
<h1>Poenggrenser {e(navn.lower())} {ar}</h1>
<p>{intro}</p>
<p class="small">Læresteder: {larlenker}</p>
{studietabell(liste, vis_lared=True)}
<h2>Andre fagområder</h2><p class="small">{andre}</p>"""
    side(fag_url(fag), f"Poenggrenser {navn.lower()} {ar} – alle studier og læresteder",
         f"Sammenlign poenggrensene for {len(liste)} studier innen {navn.lower()} i {ar}. Se hvor det er lettest og vanskeligst å komme inn.",
         innhold)


def forside(studier, per_lared, per_fag, ar):
    neste = ar + 1
    lared_li = "".join(
        f'<li><a href="{url(lared_url(k))}">{e(LAERESTEDER.get(k, (k, k))[1])}</a> <span class="ant">({len(v)})</span></li>'
        for k, v in sorted(per_lared.items(), key=lambda kv: LAERESTEDER.get(kv[0], (kv[0], kv[0]))[1]))
    grupper = defaultdict(list)
    for f in per_fag:
        grupper[FAGGRUPPER.get(f.split(" - ")[0], "Andre fagområder")].append(f)
    fag_html = ""
    for g in ["Helse og sosial", "Lærer og pedagogikk", "Teknologi og arkitektur", "Andre fagområder"]:
        if g not in grupper:
            continue
        lis = "".join(f'<li><a href="{url(fag_url(f))}">{e(FAGOMRADER.get(f, f))}</a> <span class="ant">({len(per_fag[f])})</span></li>'
                      for f in sorted(grupper[g], key=lambda f: FAGOMRADER.get(f, f)))
        fag_html += f'<h3>{g}</h3><ul class="lenkenett">{lis}</ul>'
    topp = sorted([s for s in studier if har_tall(s["o"]) and not s["saerskilt"]], key=lambda s: -s["o"])[:10]
    topp_li = "".join(f'<li><a href="{url(s["url"])}">{e(s["navn"])}</a><span class="meta">{e(s["lkort"])}, {e(s["studiested"])}</span>'
                      f'<span class="grenser">Ordinær: {tall(s["o"])}</span></li>' for s in topp)

    fodt = "".join(f'<option value="{y}"{" selected" if y == neste - 19 else ""}>{y}</option>' for y in range(neste - 15, neste - 66, -1))
    realfag = "".join(f'<label><input type="checkbox" name="realfag" value="{k}"> {e(n)}</label>' for k, n in REALFAG_VALG)
    sprakvalg = ('<option value="0">Ingen</option><option value="0.5">Nivå I eller II som programfag (0,5)</option>'
                 '<option value="1">Nivå I og II som programfag (1,0)</option><option value="1">Nivå III som programfag (1,0)</option>')
    fagvalg = "".join(f'<option value="{e(FAGOMRADER.get(f, f))}">{e(FAGOMRADER.get(f, f))}</option>'
                      for f in sorted(per_fag, key=lambda f: FAGOMRADER.get(f, f)))
    karakterer = "".join(f'<label>{k}<input type="number" name="k{k}" min="0" max="60" inputmode="numeric" placeholder="0"></label>' for k in range(6, 1, -1))

    innhold = f"""<section class="helt">
<h1>Poenggrenser {ar} – kommer du inn?</h1>
<p>Søk i poenggrensene fra Samordna opptak for {len(studier)} studier, regn ut poengene dine og se hvilke studier du ville kommet inn på.</p>
<label for="sok" class="skjult">Søk etter studium, lærested eller sted</label>
<input id="sok" type="search" class="stort-sok" placeholder="Søk: sykepleie, NTNU, Bergen, medisin …" autocomplete="off">
<ul id="sok-treff" class="studieliste" aria-live="polite"></ul>
</section>

<section id="kalkulator" class="kort">
<h2>Poengkalkulator</h2>
<p class="muted">Fyll inn det du har, så regner vi ut skolepoeng og konkurransepoeng etter reglene til Samordna opptak. Alt skjer i nettleseren din – ingenting sendes noe sted.</p>
<div class="kalk-grid">
<form id="kalk" autocomplete="off">
<fieldset><legend>1. Om deg</legend>
<div class="rad">
<label>Fødselsår<select name="fodt">{fodt}</select></label>
<label>Når søker du?<select name="aar"><option value="{neste}">Opptak {neste} (gjeldende regler)</option><option value="{neste + 1}">Opptak {neste + 1} (nye regler)</option></select></label>
</div>
<label class="chk"><input type="checkbox" name="fgv" checked> Jeg har (eller får) førstegangsvitnemål</label>
</fieldset>
<fieldset><legend>2. Karakterer</legend>
<p class="small muted">Hvor mange av hver karakter har du på vitnemålet? (Ta med alle fag, også standpunkt og eksamen.)</p>
<div class="karakterer">{karakterer}</div>
<p id="snitt-ut" class="small muted" aria-live="polite"></p>
<label>… eller skriv inn snittet direkte<input name="snitt" inputmode="decimal" placeholder="f.eks. 4,62"></label>
</fieldset>
<fieldset><legend>3. Realfag (programfag)</legend>
<div class="valg">{realfag}</div>
<p class="small muted">Du får maks 1,5 poeng for samme fag (f.eks. S1 + S2 + R2), og maks 4 realfags- og språkpoeng til sammen.</p>
</fieldset>
<fieldset><legend>4. Fremmedspråk som programfag</legend>
<div class="rad"><label>Språk 1<select name="sprak">{sprakvalg}</select></label><label>Språk 2<select name="sprak">{sprakvalg}</select></label></div>
<p class="small muted">Fremmedspråk som fellesfag, engelsk og skandinaviske språk gir ikke språkpoeng.</p>
</fieldset>
<fieldset><legend>5. Tilleggspoeng (bare ordinær kvote)</legend>
<label class="chk"><input type="checkbox" name="fhs"> Folkehøgskole (minst 33 uker)</label>
<label class="chk"><input type="checkbox" name="mil"> Fullført førstegangstjeneste eller siviltjeneste</label>
<label>Høyere utdanning eller fagskole<select name="hu"><option value="0">Ingen</option><option value="1">30–59 studiepoeng</option><option value="2">60 studiepoeng eller mer</option></select></label>
</fieldset>
<noscript><p>Kalkulatoren trenger JavaScript.</p></noscript>
</form>
<div id="resultat-boks">
<div id="resultat" class="kort" hidden aria-live="polite">
<h3>Dine poeng</h3>
<table class="poengtabell"><tbody id="poengtabell"></tbody></table>
<p id="kvoteinfo"></p>
<p id="regelinfo" class="small muted"></p>
<p class="small muted">Kjønnspoeng og poeng for opptaksprøver gjelder bare enkelte studier og er ikke med her.</p>
</div>
</div>
</div>
<div id="treff-boks">
<h3>Studier du ville kommet inn på med {ar}-grensene: <span id="treff-antall">–</span></h3>
<p class="small muted">Vi sammenligner med grensene fra hovedopptaket {ar}. Vi sjekker ikke spesielle opptakskrav (for eksempel R2 eller fysikk), så sjekk dem selv.</p>
<div class="filterlinje"><input id="treff-sok" type="search" placeholder="Filtrer: navn, sted, lærested …"><select id="treff-fag"><option value="">Alle fagområder</option>{fagvalg}</select><span></span></div>
<ul id="treff-liste" class="studieliste"><li class="mer">Fyll inn karakterene dine over for å se resultatet.</li></ul>
<button id="treff-mer" class="knapp sekundar" type="button" hidden>Vis flere</button>
<h3>Nesten der – under 3 poeng unna</h3>
<ul id="nesten-liste" class="studieliste"></ul>
</div>
</section>

<section id="regler">
<h2>Nye opptaksregler fra {neste} og 2028</h2>
<p>Regjeringen har vedtatt en ny opptaksforskrift. Den gjelder fra opptaket i {neste}, men de største endringene kommer i 2028. Går du på videregående nå, kan dette påvirke hvilke fag du bør velge.</p>
<div class="regler">
<div class="kort"><h3>Opptak {neste}</h3><ul>
<li>Poengberegningen er som før: alderspoeng, tilleggspoeng, realfags- og språkpoeng gjelder fortsatt.</li>
<li>Har to søkere like mange poeng, avgjøres det ved loddtrekning – ikke etter alder.</li>
<li>23/5-regelen blir 23/6-regelen: kravet om fem års praksis fjernes.</li>
<li>Det blir ikke lenger mulig å søke særskilt vurdering.</li>
<li>Lærestedene kan selv innføre rangerende opptaksprøver og søke om kjønnskvoter.</li>
</ul></div>
<div class="kort"><h3>Opptak 2028</h3><ul>
<li>Førstegangskvoten: aldersgrensen øker fra 21 til 23 år, og kvoten blir 65 % av plassene (i dag 50 %).</li>
<li>Realfagspoengene halveres: 0,25 per realfag på 140 timer, 0,5 for R2 og Fysikk 2, maks 2 poeng.</li>
<li>Alderspoeng, språkpoeng, kjønnspoeng og poeng for naturbruk fjernes.</li>
<li>Tilleggspoeng for høyere utdanning, fagskole og folkehøgskole fjernes. Militær- og siviltjeneste gir 1 poeng i stedet for 2.</li>
<li>Det kommer tilleggspoeng for søkere med samisk som førstespråk.</li>
<li>Du kan ikke lenger bytte opptaksgrunnlag (dobbeltrangering) for å få en bedre poengsum.</li>
</ul></div>
</div>
<p class="small muted">Kilde: <a href="https://www.samordnaopptak.no/universitet-og-hogskole/aktuelt/nye-regler-for-opptak-til-hoyere-utdanning.html" rel="noopener">Samordna opptak – Nye regler for opptak til høyere utdanning</a>. Velg «Opptak 2028» i kalkulatoren for å se et forenklet anslag med de nye reglene.</p>
</section>

<section><h2>Høyeste poenggrenser {ar}</h2>
<ul class="studieliste">{topp_li}</ul>
<p><a href="{url('alle-studier/')}">Se alle {len(studier)} studier →</a></p></section>

<section id="laresteder"><h2>Læresteder</h2><ul class="lenkenett">{lared_li}</ul></section>
<section id="fagomrader"><h2>Fagområder</h2>{fag_html}</section>
"""
    side("", f"Poenggrenser {ar} og poengkalkulator – {SITE_NAVN}",
         f"Se poenggrensene fra Samordna opptak {ar} for {len(studier)} studier, regn ut skolepoeng og konkurransepoeng, og finn ut hvilke studier du kommer inn på.",
         innhold)


def alle_studier_side(studier, ar):
    lared_opts = "".join(f'<option value="{e(k)}">{e(LAERESTEDER.get(k, (k, k))[1])}</option>'
                         for k in sorted({s["laerested"] for s in studier}, key=lambda k: LAERESTEDER.get(k, (k, k))[1]))
    fag_opts = "".join(f'<option value="{e(f)}">{e(FAGOMRADER.get(f, f))}</option>'
                       for f in sorted({s["fagomrade"] for s in studier}, key=lambda f: FAGOMRADER.get(f, f)))
    rader = []
    for s in studier:
        sok = " ".join([s["studiekode"], s["navn"], s["lkort"], s["llangt"], s["studiested"], s["fagnavn"]]).lower()
        rader.append(f'<tr data-l="{e(s["laerested"])}" data-f="{e(s["fagomrade"])}" data-s="{e(sok)}">'
                     f'<td><a href="{url(s["url"])}">{e(s["navn"])}</a></td><td>{e(s["lkort"])}, {e(s["studiested"])}</td>'
                     f'<td class="n">{grense(s["f"])}</td><td class="n">{grense(s["o"])}</td></tr>')
    innhold = f"""{sti(("Alle studier", None))}
<h1>Alle poenggrenser {ar}</h1>
<p>Her er alle {len(studier)} studiene fra hovedopptaket {ar}. Filtrer på navn, lærested eller fagområde. Viser <b id="antall">{len(studier)}</b> studier.</p>
<div id="filter" class="filterlinje">
<label class="skjult" for="f-sok">Søk</label><input id="f-sok" type="search" placeholder="Søk etter studium, sted eller studiekode">
<label class="skjult" for="f-lared">Lærested</label><select id="f-lared"><option value="">Alle læresteder</option>{lared_opts}</select>
<label class="skjult" for="f-fag">Fagområde</label><select id="f-fag"><option value="">Alle fagområder</option>{fag_opts}</select>
</div>
<div class="tabell-wrap"><table class="data" id="alle"><thead><tr><th>Studium</th><th>Lærested og sted</th><th class="n">Førstegang</th><th class="n">Ordinær</th></tr></thead>
<tbody>{"".join(rader)}</tbody></table></div>"""
    side("alle-studier/", f"Alle poenggrenser {ar} – {len(studier)} studier | {SITE_NAVN}",
         f"Komplett liste over poenggrensene i Samordna opptak {ar} for {len(studier)} studier, med søk og filter på lærested og fagområde.",
         innhold)


def om_side(meta, ar):
    innhold = f"""{sti(("Om", None))}
<h1>Om Poenghjelpen</h1>
<p>Poenghjelpen er en gratis og reklamefri side for deg som går på videregående og lurer på hva som skal til for å komme inn på drømmestudiet.</p>
<h2>Hvor kommer tallene fra?</h2>
<p>Poenggrensene kommer fra Samordna opptak (Direktoratet for høyere utdanning og kompetanse). Vi lastet ned statistikken «Poenggrenser» for hovedopptaket og suppleringsopptaket {ar} den {e(meta['hentet'])}.
Se kilden selv på <a href="https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/poenggrenser.html" rel="noopener">samordnaopptak.no</a>.</p>
<h2>Slik leser du tallene</h2>
<ul>
<li><b>Poenggrensen</b> er poengsummen til den siste søkeren som fikk tilbud om plass.</li>
<li><b>Alle kvalifiserte</b> (0 i Samordna opptaks tall) betyr at alle som oppfylte opptakskravene, fikk tilbud.</li>
<li><b>Ikke oppgitt</b> (-1 i Samordna opptaks tall) betyr at grensen ikke er publisert.</li>
<li><b>–</b> betyr at det ikke finnes en grense for den kvoten i dataene.</li>
<li>Noen studier rangerer med opptaksprøve. Der er tallene på en annen skala, og de er tatt ut av kalkulatorens treffliste.</li>
</ul>
<h2>Om kalkulatoren</h2>
<p>Kalkulatoren følger reglene som står på samordnaopptak.no for opptaket i {ar + 1}, og en forenklet versjon av de nye reglene fra 2028. Den regner ikke med kjønnspoeng, opptaksprøver eller spesielle opptakskrav.
Svaret er et anslag – det er alltid Samordna opptak som regner ut de endelige poengene dine.</p>
<h2>Ansvar</h2>
<p>Vi gjør vårt beste for at tallene er riktige, men vi kan ikke garantere det. Sjekk alltid med Samordna opptak og lærestedet før du tar viktige valg.
Poenghjelpen er ikke tilknyttet Samordna opptak, HK-dir eller noe lærested.</p>"""
    side("om/", f"Om {SITE_NAVN} – poenggrenser og kalkulator", "Hvem som lager Poenghjelpen, hvor poenggrensene kommer fra og hvordan du leser tallene.", innhold)


def personvern_side():
    innhold = f"""{sti(("Personvern", None))}
<h1>Personvern</h1>
<p>Kort fortalt: Poenghjelpen samler ikke inn opplysninger om deg.</p>
<ul>
<li>Vi har ingen annonser, ingen analyseverktøy og ingen sporing.</li>
<li>Vi bruker ikke informasjonskapsler (cookies).</li>
<li>Kalkulatoren regner ut alt i nettleseren din. Ingenting du skriver inn, sendes til oss eller andre.</li>
<li>Nettleseren din husker poengene du regnet ut sist og om du valgte lys eller mørk modus (lokal lagring). Dette ligger bare på din enhet, og du kan slette det ved å tømme nettstedsdata i nettleseren.</li>
<li>Siden ligger på GitHub Pages. GitHub kan registrere tekniske opplysninger som IP-adresse i sine serverlogger for å drive tjenesten. Les <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHubs personvernerklæring</a>.</li>
</ul>"""
    side("personvern/", f"Personvern – {SITE_NAVN}", "Poenghjelpen har ingen sporing, ingen annonser og ingen informasjonskapsler. Les hvordan siden behandler data.", innhold)


def side_404():
    innhold = f"""<h1>Fant ikke siden</h1>
<p>Siden du lette etter finnes ikke. Kanskje studiet har fått ny studiekode, eller lenken er feil.</p>
<p><a class="knapp" href="{url('')}">Til forsiden</a></p>
<p><a href="{url('alle-studier/')}">Se alle studier</a> · <a href="{url('')}#kalkulator">Poengkalkulator</a></p>"""
    side("404.html", f"Fant ikke siden – {SITE_NAVN}", "Siden finnes ikke.", innhold, ekstra_head='<meta name="robots" content="noindex">', i_sitemap=False)


# ---------------------------------------------------------------- hovedprogram
def main():
    meta, studier = last_data()
    ar = max(s["ar"] for s in studier)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for f in (ROOT / "static").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)

    st = Statistikk(studier)
    per_lared, per_fag = defaultdict(list), defaultdict(list)
    for s in studier:
        per_lared[s["laerested"]].append(s)
        per_fag[s["fagomrade"]].append(s)
    alle_fag = sorted(per_fag, key=lambda f: FAGOMRADER.get(f, f))

    forside(studier, per_lared, per_fag, ar)
    alle_studier_side(studier, ar)
    for s in studier:
        studieside(s, st, per_fag, ar)
    for k, v in per_lared.items():
        larestedside(k, v, ar)
    for f, v in per_fag.items():
        fagside(f, v, alle_fag, ar)
    om_side(meta, ar)
    personvern_side()
    side_404()

    # Søkeindeks for søk og kalkulator
    indeks = [[s["studiekode"], s["navn"], s["lkort"], s["studiested"], s["fagnavn"], s["f"], s["o"], s["url"],
               1 if s["saerskilt"] else 0, s["llangt"]] for s in studier]
    (OUT / "assets" / "studier.json").write_text(json.dumps(indeks, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    sitemap = "".join(f"<url><loc>{e(u)}</loc><lastmod>{I_DAG}</lastmod></url>\n" for u in SIDER)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}</urlset>\n',
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # Bekreftelsesfil fra Google Search Console (f.eks. google1234abcd.html) kopieres med
    for f in ROOT.glob("google*.html"):
        shutil.copy(f, OUT / f.name)
    print(f"Ferdig! Laget {len(SIDER) + 1} sider i {OUT}/ for {SITE_URL}")


if __name__ == "__main__":
    main()
