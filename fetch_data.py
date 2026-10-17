"""Henter poenggrenser for alle år fra Samordna opptak og lagrer dem som data/poenggrenser.json.

Bruk:
    python3 fetch_data.py                 # laster ned CSV automatisk (alle år fra 2015)
    python3 fetch_data.py minfil.csv      # bruker en CSV du har lastet ned selv

Kilde: Tableau-dashbordet som samordnaopptak.no lenker til fra
https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/poenggrenser.html

Studier kobles sammen over år via studiekoden. Har et studium fått ny kode (f.eks. etter en
sammenslåing av læresteder), kobles den gamle koden til den nye når navn, lærested og studiested
er like og årene ikke overlapper. Er koblingen ikke entydig, lar vi være å koble.
"""

import csv
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

FORSTE_AR = 2015
CSV_URL = (
    "https://rapport-dv.educloud.no/t/SO-datavarehus/views/"
    "Poenggrenserogventelistetallhovedopptaksuppleringsopptak_16275618215770/Poenggrenser.csv"
)
OUT = Path(__file__).parent / "data" / "poenggrenser.json"

KVOTER = {"Førstegangsvitnemålskvote": "forste", "Ordinær kvote": "ordinar"}
RUNDER = {"Hovedopptak": "hoved", "Suppleringsopptak": "supplering"}


def read_csv_text():
    if len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_bytes()
    else:
        # Uten filter gir Tableau bare siste år, så vi ber om alle år eksplisitt
        ar = ",".join(str(a) for a in range(FORSTE_AR, date.today().year + 1))
        url = CSV_URL + "?" + urllib.parse.urlencode({"År": ar})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Poenghjelpen"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    # Tableau leverer vanligvis UTF-8, men eksport fra nettleseren kan være UTF-16
    for enc in ("utf-8-sig", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit("Klarte ikke å lese CSV-filen (ukjent tegnkoding).")


def parse_number(s):
    s = s.strip().replace(",", ".")
    if s == "":
        return None
    return float(s)


def tom_runde():
    return {"hoved": {"forste": None, "ordinar": None}, "supplering": {"forste": None, "ordinar": None}}


def normaliser(navn):
    return re.sub(r"[^a-zæøå0-9]", "", navn.lower().rstrip("*"))


def main():
    text = read_csv_text()
    first = text.split("\n", 1)[0]
    delim = ";" if first.count(";") > first.count("\t") else "\t"
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    needed = {"Kvote", "Lærested", "Opptaksrunde", "Studiekode", "Studienavn", "Studiested",
              "Utdanningsområde og -type", "År", "Poenggrense"}
    missing = needed - set(rows[0].keys()) if rows else needed
    if missing:
        raise SystemExit(f"CSV-filen mangler kolonnene: {', '.join(sorted(missing))}")

    # 1. Samle alt per studiekode og år
    koder = {}
    for r in rows:
        kode = r["Studiekode"].replace(" ", "").strip()
        ar = int(r["År"])
        k = koder.setdefault(kode, {"info": {}, "historikk": {}})
        k["info"][ar] = {
            "studienavn": r["Studienavn"].strip(),
            "laerested": r["Lærested"].strip(),
            "studiested": r["Studiested"].strip(),
            "fagomrade": r["Utdanningsområde og -type"].strip(),
        }
        runde, kvote = RUNDER.get(r["Opptaksrunde"]), KVOTER.get(r["Kvote"])
        if runde and kvote:
            k["historikk"].setdefault(ar, tom_runde())[runde][kvote] = parse_number(r["Poenggrense"])

    siste_ar = max(a for k in koder.values() for a in k["info"])
    aktive = {kode for kode, k in koder.items() if siste_ar in k["info"]}

    # 2. Koble gamle koder til nye (samme navn, lærested og sted, ingen overlappende år)
    indeks = defaultdict(list)
    for kode in aktive:
        i = koder[kode]["info"][siste_ar]
        indeks[(normaliser(i["studienavn"]), i["laerested"], i["studiested"])].append(kode)
    forslag = defaultdict(list)
    for kode in set(koder) - aktive:
        k = koder[kode]
        i = k["info"][max(k["info"])]
        kandidater = [n for n in indeks.get((normaliser(i["studienavn"]), i["laerested"], i["studiested"]), [])
                      if not set(koder[n]["info"]) & set(k["info"])]
        if len(kandidater) == 1:
            forslag[kandidater[0]].append(kode)
    koblet = {}
    for ny, gamle in forslag.items():
        ar = [a for g in gamle for a in koder[g]["info"]]
        if len(ar) == len(set(ar)):  # de gamle kodene må ikke overlappe hverandre heller
            for g in gamle:
                koblet[g] = ny

    # 3. Bygg studielisten
    def historikk_json(h):
        return {str(a): h[a] for a in sorted(h)}

    studier = []
    for kode in aktive:
        k = koder[kode]
        historikk = dict(k["historikk"])
        tidligere = sorted(g for g, n in koblet.items() if n == kode)
        for g in tidligere:
            historikk.update(koder[g]["historikk"])
        naa = historikk.get(siste_ar, tom_runde())
        studier.append({
            "studiekode": kode,
            **k["info"][siste_ar],
            "ar": siste_ar,
            "hoved": naa["hoved"],
            "supplering": naa["supplering"],
            "tidligere_koder": tidligere,
            "historikk": historikk_json(historikk),
        })
    nedlagte = []
    for kode in sorted(set(koder) - aktive - set(koblet)):
        k = koder[kode]
        nedlagte.append({"studiekode": kode, **k["info"][max(k["info"])],
                         "siste_ar": max(k["info"]), "historikk": historikk_json(k["historikk"])})

    data = {
        "kilde": "Samordna opptak (HK-dir), Tableau-visningen «Poenggrenser»",
        "kilde_url": CSV_URL.removesuffix(".csv"),
        "hentet": date.today().isoformat(),
        "forste_ar": min(a for k in koder.values() for a in k["info"]),
        "siste_ar": siste_ar,
        "forklaring": {"0": "Alle kvalifiserte søkere fikk tilbud", "-1": "Ikke oppgitt",
                       "null": "Ingen grense publisert for denne kvoten"},
        "studier": sorted(studier, key=lambda s: (s["studienavn"], s["laerested"], s["studiested"])),
        "nedlagte": nedlagte,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Lagret {len(studier)} studier ({siste_ar}) med historikk fra {data['forste_ar']}, "
          f"{len(koblet)} gamle koder koblet til nye, {len(nedlagte)} nedlagte studier, {len(rows)} rader totalt.")


if __name__ == "__main__":
    main()
