# Poenghjelpen

Gratis nettside med poenggrenser fra Samordna opptak og en poengkalkulator for VGS-elever.

## Hva ligger hvor?

| Fil / mappe | Hva det er |
|---|---|
| `build.py` | Lager hele nettsiden. **Nettadressen står i variabelen `SITE_URL` øverst.** |
| `fetch_data.py` | Laster ned nye poenggrenser fra Samordna opptak til `data/poenggrenser.json`. |
| `data/poenggrenser.json` | Poenggrensene (hovedopptak og suppleringsopptak 2026, 1369 studier). |
| `static/` | Utseende (`style.css`), kalkulatorens regler (`poeng.js`) og knappene/søket (`app.js`). |
| `.github/workflows/pages.yml` | Oppskrift som får GitHub til å bygge og publisere siden automatisk. |
| `site/` | Den ferdige nettsiden. Lages av `build.py`, og skal **ikke** lastes opp. |

---

## Slik får du siden ut på nett (gratis, ca. 20 minutter)

Du trenger ikke installere noe. Alt gjøres i nettleseren på github.com.
Siden blir **offentlig**, så ikke legg inn noe privat.

### Steg 1 – Lag en GitHub-konto
1. Gå til <https://github.com/signup> og lag en gratis konto.
2. Husk brukernavnet ditt. I eksemplene under heter brukeren `ola-nordmann`.

### Steg 2 – Lag et nytt «repository» (en prosjektmappe på GitHub)
1. Trykk på **+** øverst til høyre → **New repository**.
2. **Repository name:** skriv `poenghjelpen`.
3. Velg **Public** (GitHub Pages er bare gratis for offentlige prosjekter).
4. Trykk **Create repository**.

### Steg 3 – Last opp filene
1. På siden til det nye prosjektet: trykk lenken **uploading an existing file**
   (eller **Add file → Upload files**).
2. Åpne prosjektmappen din i Finder og dra inn disse:
   - `build.py`
   - `fetch_data.py`
   - `README.md`
   - mappen `data`
   - mappen `static`
3. **Ikke** dra inn mappen `site`. Den lager GitHub selv.
4. Trykk den grønne knappen **Commit changes**.

### Steg 4 – Legg inn publiseringsoppskriften
Mappen `.github` er skjult på Mac, så du lager filen direkte på GitHub i stedet:
1. Trykk **Add file → Create new file**.
2. I navnefeltet skriver du nøyaktig: `.github/workflows/pages.yml`
   (skråstrekene lager mappene automatisk).
3. Åpne filen `.github/workflows/pages.yml` fra prosjektmappen i TextEdit, kopier alt, og lim det inn i det store feltet.
   (Får du ikke tak i filen? Trykk **Cmd + Shift + .** i Finder for å vise skjulte mapper.)
4. Trykk **Commit changes…** og så **Commit changes** igjen.

### Steg 5 – Sett riktig nettadresse
1. Trykk på `build.py` i fillisten, og så på blyant-ikonet ✏️ (Edit).
2. Finn linjen øverst:
   ```python
   SITE_URL = "https://DITT-BRUKERNAVN.github.io/poenghjelpen/"
   ```
3. Bytt `DITT-BRUKERNAVN` med ditt eget brukernavn, for eksempel
   `https://ola-nordmann.github.io/poenghjelpen/`. Bruk små bokstaver, og behold `/` på slutten.
4. Trykk **Commit changes…** → **Commit changes**.

### Steg 6 – Slå på GitHub Pages
1. Trykk **Settings** (tannhjulet i menyen til prosjektet).
2. Velg **Pages** i menyen til venstre.
3. Under **Build and deployment → Source**: velg **GitHub Actions**.

### Steg 7 – Start publiseringen og vent
1. Trykk **Actions** i menyen øverst.
2. Velg **Bygg og publiser Poenghjelpen** til venstre → **Run workflow** → **Run workflow**.
3. Vent 1–2 minutter til du ser en grønn hake ✅.
4. Siden din ligger nå på `https://ola-nordmann.github.io/poenghjelpen/` (med ditt brukernavn).

Hver gang du endrer en fil på GitHub, bygges og publiseres siden automatisk på nytt.

**Får du et rødt kryss ❌?** Trykk på det og les feilmeldingen. Vanlige årsaker:
- Steg 6 er ikke gjort (Source må være **GitHub Actions**).
- Filen i steg 4 har feil navn eller mangler noe av teksten.
- Mappen `data` eller `static` ble ikke lastet opp.

---

## Etter at siden er ute (valgfritt)

- **Bli funnet på Google:** Gå til <https://search.google.com/search-console> (gratis), legg til nettadressen din,
  og send inn sitemap-adressen `https://ola-nordmann.github.io/poenghjelpen/sitemap.xml`.
  Søkemotorer leser bare `robots.txt` på roten av et domene. Med en adresse som slutter på `/poenghjelpen/`
  er det derfor sitemap-innsendingen som gjør jobben.
- **Kortere adresse:** Kaller du prosjektet `ola-nordmann.github.io` i stedet for `poenghjelpen`, blir siden
  `https://ola-nordmann.github.io/`. Husk da å endre `SITE_URL` til det samme.
- **Eget domene** (f.eks. poenghjelpen.no) koster penger og trengs ikke.

## Oppdatere tallene neste år

Samordna opptak publiserer nye poenggrenser i juli. Da gjør du dette på din egen Mac:

1. Åpne programmet **Terminal** og gå til prosjektmappen.
2. Kjør:
   ```bash
   python3 fetch_data.py
   ```
3. Last opp den nye `data/poenggrenser.json` til GitHub (**Add file → Upload files**). Siden oppdateres av seg selv.

### Hvis den automatiske nedlastingen slutter å virke
1. Gå til <https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/poenggrenser.html> og åpne statistikken.
2. I Tableau-visningen: trykk nedlastingsikonet → **Krysstabell / Crosstab** → velg **CSV** → **Last ned**.
3. Legg filen i prosjektmappen, for eksempel med navnet `poenggrenser.csv`.
4. Kjør:
   ```bash
   python3 fetch_data.py poenggrenser.csv
   ```
5. Kolonnene må hete `Kvote`, `Lærested`, `Opptaksrunde`, `Studiekode`, `Studienavn`, `Studiested`,
   `Utdanningsområde og -type`, `År` og `Poenggrense`. Hvis ikke, sier skriptet fra.

## Se siden på din egen maskin (valgfritt)

```bash
python3 build.py
```
Siden havner i mappen `site/`. Lenkene forventer adressen fra `SITE_URL`, så det enkleste er å se siden på GitHub.

## Kilder

- Poenggrenser: Samordna opptak, statistikken «Poenggrenser» (hentet 17. oktober 2026).
- Poengregler: <https://www.samordnaopptak.no/universitet-og-hogskole/poengberegning/>
- Nye regler: <https://www.samordnaopptak.no/universitet-og-hogskole/aktuelt/nye-regler-for-opptak-til-hoyere-utdanning.html>
