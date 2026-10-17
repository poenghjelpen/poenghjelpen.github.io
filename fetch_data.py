"""Henter poenggrenser fra Samordna opptak og lagrer dem som data/poenggrenser.json.

Bruk:
    python3 fetch_data.py                 # laster ned CSV automatisk
    python3 fetch_data.py minfil.csv      # bruker en CSV du har lastet ned selv

Kilde: Tableau-dashbordet som samordnaopptak.no lenker til fra
https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/poenggrenser.html
"""

import csv
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

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
        req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0 Poenghjelpen"})
        with urllib.request.urlopen(req, timeout=60) as resp:
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


def main():
    text = read_csv_text()
    delim = ";" if text.split("\n", 1)[0].count(";") > text.split("\n", 1)[0].count("\t") else "\t"
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    needed = {"Kvote", "Lærested", "Opptaksrunde", "Studiekode", "Studienavn", "Studiested",
              "Utdanningsområde og -type", "År", "Poenggrense"}
    missing = needed - set(rows[0].keys()) if rows else needed
    if missing:
        raise SystemExit(f"CSV-filen mangler kolonnene: {', '.join(sorted(missing))}")

    studier = {}
    for r in rows:
        kode = r["Studiekode"].replace(" ", "").strip()
        s = studier.setdefault(kode, {
            "studiekode": kode,
            "studienavn": r["Studienavn"].strip(),
            "laerested": r["Lærested"].strip(),
            "studiested": r["Studiested"].strip(),
            "fagomrade": r["Utdanningsområde og -type"].strip(),
            "ar": int(r["År"]),
            "hoved": {"forste": None, "ordinar": None},
            "supplering": {"forste": None, "ordinar": None},
        })
        runde, kvote = RUNDER.get(r["Opptaksrunde"]), KVOTER.get(r["Kvote"])
        if runde and kvote:
            s[runde][kvote] = parse_number(r["Poenggrense"])

    data = {
        "kilde": "Samordna opptak (HK-dir), Tableau-visningen «Poenggrenser»",
        "kilde_url": CSV_URL.removesuffix(".csv"),
        "hentet": date.today().isoformat(),
        "forklaring": {"0": "Alle kvalifiserte søkere fikk tilbud", "-1": "Ikke oppgitt",
                       "null": "Ingen grense publisert for denne kvoten"},
        "studier": sorted(studier.values(), key=lambda s: (s["studienavn"], s["laerested"], s["studiested"])),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Lagret {len(studier)} studier ({len(rows)} rader) til {OUT}")


if __name__ == "__main__":
    main()
