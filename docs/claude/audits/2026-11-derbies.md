# Derby audit, phase 3a (November 2026)

Fact check of `data/derbies.csv`: a full mechanical check of all 248 rows
(Part A, offline) and a seeded sample of 60 rows read against the article
each row names as its source (Part B). This file was written in two
steps: the method and the sample first, **before any page was read**
(its own commit), the results after.

## Part B: method and sample (written before any page was read)

- **Population**: the 248 data rows of `data/derbies.csv` as of
  2026-11-14 (after the one Part A fix, which changes no stratum). A
  row's id is its **line number in the file** (the header is line 1),
  as `check_derbies.py` prints it.
- **Strata**. *Map status* is decided by the club files, not by the
  `offMap` cell: "on" when both Q-ids are in a `data/clubs/??.json`,
  "off" otherwise (195 on, 53 off). *Country* is the checker's own
  label: the country of the row's clubs that are on the map (one row is
  `DE/ES`, Bayern v Real Madrid, and is its own group).
- **Seats per country**: 60 x rows / 248, rounded down, at least 1 per
  country group; the seats left over go one at a time to the largest
  remainder (ties by country code).
- **Seats on and off the map**: 60 x 53 / 248 = 12.8, so 13 off and 47
  on. Inside each country the off share of its seats is rounded down,
  and the off seats still missing go to the largest remainders.
- **Draw**: Python `random.Random(20261115)`; countries in alphabetical
  order, inside each country first the "on" rows, then the "off" rows,
  each with `rng.sample(rows_in_file_order, seats)`.
- **Seed**: 20261115.

| country | rows | on | off | seats | on | off |
|---|---|---|---|---|---|---|
| AT | 8 | 6 | 2 | 2 | 1 | 1 |
| BE | 15 | 12 | 3 | 4 | 3 | 1 |
| CH | 13 | 10 | 3 | 3 | 2 | 1 |
| DE | 25 | 25 | 0 | 6 | 6 | 0 |
| DE/ES | 1 | 1 | 0 | 1 | 1 | 0 |
| ES | 17 | 15 | 2 | 4 | 4 | 0 |
| FR | 35 | 25 | 10 | 8 | 6 | 2 |
| GB | 50 | 37 | 13 | 12 | 9 | 3 |
| GR | 16 | 9 | 7 | 4 | 2 | 2 |
| IT | 16 | 13 | 3 | 4 | 3 | 1 |
| NL | 28 | 28 | 0 | 7 | 7 | 0 |
| RO | 15 | 8 | 7 | 3 | 2 | 1 |
| RS | 9 | 6 | 3 | 2 | 1 | 1 |
| total | 248 | 195 | 53 | 60 | 47 | 13 |

Portugal has a club file and no derby row, so it has no seat.

**The 60 rows drawn** (line, country, map status, name, pair):

| line | country | map | name | pair |
|---|---|---|---|---|
| 4 | AT | on | Graz derby | Grazer AK v SK Sturm Graz |
| 8 | AT | off | Derby of Love | First Vienna FC 1894 v Wiener Sport-Club |
| 16 | RO | on | Pride derby | Dinamo București v Universitatea Craiova |
| 20 | RO | off | North-East derby | FC Botoșani v ACS Foresta Suceava |
| 24 | RO | on | Crișana derby | Bihor Oradea v UTA Arad |
| 25 | RS | on | Eternal derby | FK Crvena zvezda v FK Partizan |
| 28 | RS | off | Novi Sad derby | FK Vojvodina v RFK Novi Sad 1921 |
| 36 | CH | on | Die Klassiker (Basel v FC Zürich) | FC Basel v FC Zürich |
| 39 | CH | on | Luzerner Derby | FC Luzern v SC Kriens |
| 45 | CH | off | Ticino derby (Bellinzona) | FC Lugano v AC Bellinzona |
| 47 | GB | on | South Wales derby | Swansea City A.F.C. v Cardiff City F.C. |
| 50 | DE | on | Frankenderby | 1. FC Nürnberg v SpVgg Greuther Fürth |
| 52 | DE | on | Südwestderby (KSC v FCK) | Karlsruher SC v 1. FC Kaiserslautern |
| 55 | DE | on | Nordderby | Hamburger SV v Werder Bremen |
| 63 | DE | on | Berlin derby | 1. FC Union Berlin v Hertha BSC |
| 69 | DE | on | Westphalian derby | Arminia Bielefeld v Preußen Münster |
| 71 | DE | on | Cologne derby (Fortuna) | 1. FC Köln v SC Fortuna Köln |
| 75 | IT | on | Derby d'Italia | FC Inter v Juventus FC |
| 77 | IT | on | Derby della Mole | Juventus FC v Torino FC |
| 85 | IT | on | Derby delle Due Sicilie | SSC Napoli v Palermo FC |
| 87 | IT | off | Derby dell'Enza | Parma Calcio 1913 v A.C. Reggiana 1919 |
| 92 | ES | on | Derbi Barceloní | FC Barcelona v RCD Espanyol de Barcelona |
| 98 | ES | on | Canary Islands derby | C.D. Tenerife v UD Las Palmas |
| 100 | ES | on | Derby of eastern Andalusia | Granada CF v Málaga CF |
| 102 | ES | on | El Otro Clásico | Atlético Madrid v FC Barcelona |
| 107 | DE/ES | on | European Clásico | FC Bayern München v Real Madrid Club de Fútbol |
| 110 | FR | on | Derby du Nord | RC Lens v Lille OSC |
| 113 | FR | on | Paris derby | Paris Saint-Germain FC v Paris FC |
| 117 | FR | off | Derby de la Méditerranée | OGC Nice v SC Bastia |
| 121 | FR | on | Derby Breton (Brest v Rennes) | Stade brestois 29 v Stade rennais FC |
| 126 | FR | on | Derby Breton (Lorient v Rennes) | FC Lorient v Stade rennais FC |
| 127 | FR | on | Derby Breton (Nantes v Rennes) | Football Club de Nantes v Stade rennais FC |
| 129 | NL | on | De Topper | AFC Ajax v PSV Eindhoven |
| 131 | NL | on | IJsselderby | Go Ahead Eagles v PEC Zwolle |
| 144 | GR | on | Olympiacos v PAOK | Olympiacos F.C. v PAOK FC |
| 145 | GR | on | Panathinaikos v PAOK | Panathinaikos F.C. v PAOK FC |
| 148 | GR | off | Volos derby | Niki Volos F.C. v A.S. Olympiakos Volou (football) |
| 149 | GB | on | Manchester derby | Manchester United F.C. v Manchester City F.C. |
| 158 | GB | on | East Midlands derby | Derby County F.C. v Nottingham Forest F.C. |
| 165 | GB | off | West Lancashire derby | Preston North End F.C. v Blackpool F.C. |
| 168 | GB | off | Bristol derby | Bristol City F.C. v Bristol Rovers F.C. |
| 172 | GB | off | Humber derby (Grimsby) | Hull City A.F.C. v Grimsby Town F.C. |
| 177 | GB | on | North East London derby | Tottenham Hotspur F.C. v West Ham United F.C. |
| 183 | GB | on | Chelsea v Liverpool | Chelsea F.C. v Liverpool F.C. |
| 187 | GB | on | Liverpool v Manchester City | Liverpool F.C. v Manchester City F.C. |
| 189 | GB | on | South London derby (Charlton v Millwall) | Charlton Athletic F.C. v Millwall F.C. |
| 193 | GB | on | West London derby (Brentford v QPR) | Brentford F.C. v Queens Park Rangers F.C. |
| 196 | GB | on | West London derby (Fulham v QPR) | Fulham F.C. v Queens Park Rangers F.C. |
| 197 | FR | on | Derby de la N77 | AJ Auxerre v ES Troyes AC |
| 203 | FR | off | Derby des Alpes-Maritimes | OGC Nice v AS Cannes |
| 216 | BE | on | Liège derby | RFC Liège v Standard Liège |
| 217 | BE | off | Lier derby | K. Lierse SK v K. Lyra-Lierse |
| 220 | BE | on | South West Flanders derby | SV Zulte Waregem v K.V. Kortrijk |
| 221 | BE | on | Antwerp Province derby | K. Lierse SK v KV Mechelen |
| 229 | NL | on | Friese derby | SC Heerenveen v SC Cambuur |
| 230 | NL | on | Noord-Hollandse derby | AFC Ajax v AZ Alkmaar |
| 236 | NL | on | Zuid-Hollandse derby (Feyenoord v ADO) | Feyenoord Rotterdam v ADO Den Haag |
| 239 | NL | on | Gelderse derby | SBV Vitesse v N.E.C. |
| 241 | NL | on | Kleine Gelderse derby (N.E.C.) | De Graafschap v N.E.C. |
| 249 | GR | off | Thessaly derby (Olympiacos Volos) | Athlitiki Enosi Larissa F.C. v A.S. Olympiakos Volou (football) |

**Verdicts, fixed before reading**: *correct* (the article names this
pair as a derby or rivalry, and the row's name and note agree);
*wrong* (the article names a different pair or name: fixed from the
article); *stale* (the article now says the rivalry ended or the clubs
merged: the note is fixed, the row stays); *not in source* (the article
no longer names the pair: listed, not deleted); *cannot verify*.
**Pass rule**: 0 or 1 errors (wrong, stale or not in source) passes; 2
or more means a full check of the 188 rows not sampled, later.

## Part A: mechanical check of all 248 rows (offline, 2026-11-14)

Every row was checked against the thirteen club files (582 clubs) with a
throwaway script and with `tools/check_derbies.py`.

| check | result |
|---|---|
| both club ids are Q-ids, and each is in a club file or named by `offMap` | 248 of 248; no id missing without a flag |
| `offMap` agrees with the club files | **1 disagreement, fixed** (below); no malformed flag |
| no two rows for the same pair, either way round | 0 duplicates |
| `source` present and a URL | 248 of 248 (245 English Wikipedia, 3 German) |
| `name` and `kind` present | 248 of 248 |

- **Fixed: line 59, Augsburg derby.** The row still said "B: TSV Schwaben
  Augsburg is in no division this project tracks for 2026-27". The club
  (Q529579) has been on the map at tier 4 since the tier check of
  2026-11-12 (PR 211). The flag was cleared; the club files decide it.
- **None left over.** The skips and additions of phases 1b and 1e
  produced no other change: no derby names a club that was skipped
  without its flag, and no other flagged club has arrived.
- **Not an inconsistency, noted**: "Eternal derby" is the name of two
  rows (line 10, FCSB v Dinamo; line 25, Red Star v Partizan). They are
  different pairs.
- After the fix: 195 rows with both clubs on the map, 53 with a flag.

## Part C: how the pages were read

A temporary workflow (`probe-audit.yml`, removed before the merge) read
the articles through the MediaWiki API of en.wikipedia.org and
de.wikipedia.org (wikitext; User-Agent `FootballPlannerBot/1.0`,
`maxlag=5`, wait and retry on a lag refusal) and posted only the matching lines
as comments on PR 218. **4 runs of 8 allowed**:

1. The 40 articles behind the 60 rows (40 requests): the lead, the
   infobox and bold names for an article of its own; the list entry or
   table row and its citations for a list.
2. A second look at three rows (5 requests): the Südwestderby sentence,
   and the list and the South London derby article as they stood on
   2026-10-03, the day the rows were written.
3. The clubs each lead or list entry **links** were resolved to their
   Wikidata ids and compared with the row's two ids (52 requests).
4. The same for line 8, which run 3 missed over a spelling (2 requests;
   its comment is headed "run 3").

No closed host was touched; only Wikipedia was read, which is one
source. The pages the list entries cite were not opened.
Runs 1, 2 and 4 sent exactly one request per page, so no lag refusal
occurred in them; run 3's count does not show it either way.

## Part B: results (read 2026-11-14 and 2026-11-15)

| verdict | rows |
|---|---|
| correct | 59 |
| wrong | 1 (line 45, the name) |
| stale | 0 |
| not in source | 0 |
| cannot verify | 0 |

**Errors: 1. The sample passes** (0 or 1 passes). No full check is
called for; it would have covered the 188 rows not sampled.

- **Pairs by identity, not only by name**: for 59 rows both of the
  row's Q-ids are link targets of the lead or of the list entry. The
  sixtieth is line 52, where the article is Karlsruher SC's own and so
  links only Kaiserslautern.
- **Stale**: no lead, infobox or list entry says a sampled rivalry ended
  or that its clubs merged. A list entry carries no status at all, so for
  the 24 list-sourced rows this check can only say the entry is still
  there.
- **`kind`** (city, regional, historic) is this project's own tag
  (conventions.md) and no article contradicts it.

| line | name | verdict | article and section | what it says, and the fix |
|---|---|---|---|---|
| 4 | Graz derby | correct | en: List of association football club rivalries in Europe, section Austria, list entry (rev 1382126581, 2026-10-26) | The list writes "Graz Derby: Grazer AK vs. Sturm Graz", cited to the book Geliebter Feind (the extract cut the citation before the publisher and year). |
| 8 | Derby of Love | correct | en: List of association football club rivalries in Europe, section Austria, list entry (rev 1382126581, 2026-10-26) | "Derby of Love: First Vienna F.C. vs. Wiener Sportklub"; the link Wiener Sportklub resolves to the row's Q266962. laola1.at and vienna.at are among five citations. |
| 16 | Pride derby | correct | en: List of association football club rivalries in Europe, section Romania, list entry (rev 1382126581, 2026-10-26) | "Pride derby: Dinamo Bucharest vs CSU Craiova or FCU Craiova", cited to looktv.ro; the row is the first pairing, as its note says. |
| 20 | North-East derby | correct | en: List of association football club rivalries in Europe, section Romania, list entry (rev 1382126581, 2026-10-26) | "North-East derby: FC Botoşani vs Foresta Suceava vs Politehnica Iași", cited to stiri.botosani.ro. |
| 24 | Crișana derby | correct | en: List of association football club rivalries in Europe, section Romania, list entry (rev 1382126581, 2026-10-26) | "Crișana derby: FC Bihor Oradea vs. UTA Arad", cited to oradeapress.ro; the link is FC Bihor Oradea (1958), Q1386940. |
| 25 | Eternal derby | correct | en: Eternal derby (Serbia), lead and infobox (rev 1383785011, 2026-11-04) | Lead and infobox name both clubs. |
| 28 | Novi Sad derby | correct | en: List of association football club rivalries in Europe, section Serbia, list entry (rev 1382126581, 2026-10-26) | "Novi Sad derby: Vojvodina Novi Sad vs. FK Novi Sad or FK Mladost GAT", cited to fknovisad.com; the link resolves to RFK Novi Sad 1921. |
| 36 | Die Klassiker (Basel v FC Zürich) | correct | en: List of association football club rivalries in Europe, section Switzerland, list entry (rev 1382126581, 2026-10-26) | "Die Klassikier rivalry: FC Basel vs. Grasshoppers, Young Boys or FC Zürich", pitchinvasion.net; the misspelling is in the note already. |
| 39 | Luzerner Derby | correct | en: List of association football club rivalries in Europe, section Switzerland, list entry (rev 1382126581, 2026-10-26) | "Luzerner Derby: FC Luzern vs. SC Kriens", Neue Zürcher Zeitung, 2 October 2006. |
| 45 | Ticino derby (Bellinzona) | **wrong (name)** | en: List of association football club rivalries in Europe, section Switzerland, list entry (rev 1382126581, 2026-10-26) | **The list names it "Derby del Ticino : FC Chiasso vs. AC Bellinzona vs. FC Lugano"**, and did so on 2026-10-03 already (revision 1374387952 of 2026-09-11). "Ticino derby" was a translation, not the source's name. **Fixed**: lines 44 and 45 renamed to "Derby del Ticino (Chiasso)" and "Derby del Ticino (Bellinzona)", notes say so. Pair and citation (Corriere del Ticino) agree. |
| 47 | South Wales derby | correct | en: South Wales derby, lead and infobox (rev 1372367156, 2026-08-31) | Lead and infobox name both clubs. |
| 50 | Frankenderby | correct | de: Frankenderby, lead and infobox (rev 269691513, 2026-08-15) | Lead and infobox name both clubs. |
| 52 | Südwestderby (KSC v FCK) | correct | de: Karlsruher SC, section Gegenwart (seit 2017), one sentence (rev 270869888, 2026-09-29) | "... stand bei seinem letzten Spiel im Südwestderby gegen den 1. FC Kaiserslautern auf dem Platz." Read in run 2. The article is the Karlsruher SC's own, so only Kaiserslautern is a link. |
| 55 | Nordderby | correct | en: Nordderby, lead and infobox (rev 1374317052, 2026-09-11) | Lead and infobox name both clubs. |
| 63 | Berlin derby | correct | en: Berlin derby, lead and infobox (rev 1366955095, 2026-07-31) | Lead and infobox name both clubs. |
| 69 | Westphalian derby | correct | en: German football rivalries, table under Regional, North Rhine-Westphalia (rev 1377684859, 2026-09-30) | Table row "Arminia Bielefeld, SC Preußen Münster, Westphalian derby", cited to dfb.de. |
| 71 | Cologne derby (Fortuna) | correct | en: German football rivalries, list under Local (rev 1377684859, 2026-09-30) | "Cologne derby: 1. FC Köln vs. Fortuna Köln ... vs. Viktoria Köln", Kölner Stadt-Anzeiger, 28 July 2013. |
| 75 | Derby d'Italia | correct | en: Derby d'Italia, lead and infobox (rev 1380919760, 2026-10-18) | Lead and infobox name both clubs. |
| 77 | Derby della Mole | correct | en: Derby della Mole, lead and infobox (rev 1366958734, 2026-07-31) | Lead and infobox name both clubs. |
| 85 | Derby delle Due Sicilie | correct | en: Derby delle Due Sicilie, lead and infobox (rev 1366958756, 2026-07-31) | Lead and infobox name both clubs. |
| 87 | Derby dell'Enza | correct | en: Derby dell'Enza, lead and infobox (rev 1366986528, 2026-07-31) | Lead and infobox name both clubs. |
| 92 | Derbi Barceloní | correct | en: Derbi Barceloní, lead and infobox (rev 1373468173, 2026-09-06) | Lead and infobox name both clubs. |
| 98 | Canary Islands derby | correct | en: Canary Islands derby, lead and infobox (rev 1366976153, 2026-07-31) | Lead and infobox name both clubs. |
| 100 | Derby of eastern Andalusia | correct | en: Derby of eastern Andalusia, lead and infobox (rev 1366976123, 2026-07-31) | Lead and infobox name both clubs. |
| 102 | El Otro Clásico | correct | en: El Otro Clásico, lead and infobox (rev 1383722851, 2026-11-04) | Lead and infobox name both clubs. |
| 107 | European Clásico | correct | en: Bayern Munich–Real Madrid rivalry, lead and infobox (rev 1384188952, 2026-11-07) | Lead and infobox name both clubs. |
| 110 | Derby du Nord | correct | en: Derby du Nord, lead and infobox (rev 1385386232, 2026-11-13) | Lead and infobox name both clubs. |
| 113 | Paris derby | correct | en: Paris derby, lead and infobox (rev 1383449406, 2026-11-02) | Lead and infobox name both clubs. |
| 117 | Derby de la Méditerranée | correct | en: Derby de la Mediterranée, lead and infobox (rev 1366958635, 2026-07-31) | The article and its title spell it "Derby de la Mediterranée"; the row keeps the correct French accent. **Note completed** to say so. Not counted as an error (spelling only). |
| 121 | Derby Breton (Brest v Rennes) | correct | en: Derby Breton, lead and infobox (rev 1366975736, 2026-07-31) | The infobox lists Brest, Guingamp, Lorient, Nantes and Rennes; the lead says any two Breton clubs. |
| 126 | Derby Breton (Lorient v Rennes) | correct | en: Derby Breton, lead and infobox (rev 1366975736, 2026-07-31) | As line 121. |
| 127 | Derby Breton (Nantes v Rennes) | correct | en: Derby Breton, lead and infobox (rev 1366975736, 2026-07-31) | As line 121; the latest meeting in the infobox is Rennes v Nantes. |
| 129 | De Topper | correct | en: AFC Ajax–PSV Eindhoven rivalry, lead and infobox (rev 1383205489, 2026-11-01) | Lead and infobox name both clubs. |
| 131 | IJsselderby | correct | en: IJsselderby, lead and infobox (rev 1385653729, 2026-11-14) | Lead and infobox name both clubs. |
| 144 | Olympiacos v PAOK | correct | en: Olympiacos–PAOK rivalry, lead and infobox (rev 1384559027, 2026-11-08) | Lead and infobox name both clubs. |
| 145 | Panathinaikos v PAOK | correct | en: Panathinaikos–PAOK rivalry, lead and infobox (rev 1373683005, 2026-09-07) | Lead and infobox name both clubs. |
| 148 | Volos derby | correct | en: Volos derby, lead and infobox (rev 1373503211, 2026-09-06) | Lead and infobox name both clubs. |
| 149 | Manchester derby | correct | en: Manchester derby, lead and infobox (rev 1385001799, 2026-11-11) | Lead and infobox name both clubs. |
| 158 | East Midlands derby | correct | en: Derby County F.C.–Nottingham Forest F.C. rivalry, lead and infobox (rev 1382902203, 2026-10-30) | Lead and infobox name both clubs. |
| 165 | West Lancashire derby | correct | en: West Lancashire derby, lead and infobox (rev 1374669282, 2026-09-13) | Lead and infobox name both clubs. |
| 168 | Bristol derby | correct | en: Bristol derby, lead and infobox (rev 1366955587, 2026-07-31) | Lead and infobox name both clubs. |
| 172 | Humber derby (Grimsby) | correct | en: Humber derby, lead and infobox (rev 1368419022, 2026-08-08) | Lead and infobox name both clubs. |
| 177 | North East London derby | correct | en: Tottenham Hotspur F.C.–West Ham United F.C. rivalry, lead and infobox (rev 1383042177, 2026-10-31) | "North East London derby" stands in the infobox (other names), not in the running text. |
| 183 | Chelsea v Liverpool | correct | en: Chelsea F.C.–Liverpool F.C. rivalry, lead and infobox (rev 1382548297, 2026-10-29) | Lead and infobox name both clubs. |
| 187 | Liverpool v Manchester City | correct | en: Liverpool F.C.–Manchester City F.C. rivalry, lead and infobox (rev 1381345008, 2026-10-21) | Lead and infobox name both clubs. |
| 189 | South London derby (Charlton v Millwall) | correct | en: South London derby, lead and infobox (rev 1379553882, 2026-10-10) | The lead says "any two of AFC Wimbledon, Bromley, Charlton Athletic, Crystal Palace and Millwall" and did so on 2026-10-03 (revision 1375665754). The note named three of the five. **Note completed** on lines 188, 189 and 190. Not counted as an error: pair and name are the article's. |
| 193 | West London derby (Brentford v QPR) | correct | en: West London derby, lead and infobox (rev 1381047555, 2026-10-19) | Lead and infobox name both clubs. |
| 196 | West London derby (Fulham v QPR) | correct | en: West London derby, lead and infobox (rev 1381047555, 2026-10-19) | Lead and infobox name both clubs. |
| 197 | Derby de la N77 | correct | en: Football rivalries in France, section Regional derbies (rev 1364747638, 2026-07-18) | "Derby de la N77: AJ Auxerre vs Troyes AC", Foot National. |
| 203 | Derby des Alpes-Maritimes | correct | en: Football rivalries in France, section Regional derbies (rev 1364747638, 2026-07-18) | "Derby des Alpes-Maritimes – OGC Nice vs AS Cannes", Nice Matin. |
| 216 | Liège derby | correct | en: Football rivalries in Belgium, section City derbies (rev 1354170987, 2026-05-14) | "Liège derby: RFC Liège vs. Standard Liège". |
| 217 | Lier derby | correct | en: Football rivalries in Belgium, section City derbies (rev 1354170987, 2026-05-14) | "Lier derby: Lierse vs. Lyra"; the links resolve to Lierse SK (2018), Q2313985, and Lyra-Lierse, Q2010623, the row's ids. |
| 220 | South West Flanders derby | correct | en: Football rivalries in Belgium, section Regional derbies (rev 1354170987, 2026-05-14) | "South West Flanders derby: Zulte-Waregem vs. Kortrijk." |
| 221 | Antwerp Province derby | correct | en: Football rivalries in Belgium, section Regional derbies (rev 1354170987, 2026-05-14) | "Antwerp Province derby: Lierse vs. KV Mechelen"; nieuwsblad.be is one of three citations. |
| 229 | Friese derby | correct | en: Football derbies in the Netherlands, list entry (rev 1338582281, 2026-02-16) | "Friese Derby: SC Heerenveen vs. SC Cambuur". |
| 230 | Noord-Hollandse derby | correct | en: Football derbies in the Netherlands, list entry (rev 1338582281, 2026-02-16) | The list writes "(Grote)Noord-Hollandse Derby: Ajax vs. AZ", NRC, 18 March 2013. |
| 236 | Zuid-Hollandse derby (Feyenoord v ADO) | correct | en: Football derbies in the Netherlands, list entry (rev 1338582281, 2026-02-16) | "Zuid-Hollandse Derby: Feyenoord vs. ADO Den Haag vs. SVV vs. FC Dordrecht". |
| 239 | Gelderse derby | correct | en: Football derbies in the Netherlands, list entry (rev 1338582281, 2026-02-16) | "(Grote)Gelderse Derby: Vitesse vs. N.E.C." |
| 241 | Kleine Gelderse derby (N.E.C.) | correct | en: Football derbies in the Netherlands, list entry (rev 1338582281, 2026-02-16) | "(Kleine)Gelderse Derby: De Graafschap vs. Vitesse or N.E.C." |
| 249 | Thessaly derby (Olympiacos Volos) | correct | en: Football derbies in Greece, list entry (rev 1379693785, 2026-10-11) | "Thessaly derby: AEL vs. Niki Volos or Olympiacos Volos". |

## Fixes made in `data/derbies.csv`

| line | change | evidence |
|---|---|---|
| 59 | `offMap` cleared | club files (Part A) |
| 44, 45 | name "Ticino derby (...)" to "Derby del Ticino (...)"; note says so | the list entry, read 2026-11-15 and as of 2026-10-03 |
| 117 | note: the article spells it "Derby de la Mediterranée" | article title and lead |
| 188, 189, 190 | note: the five clubs the lead names, instead of three | lead, read 2026-11-15 and as of 2026-10-03 |

Lines 44, 188 and 190 were not in the sample; they share the entry or
the article of a sampled row, so the same reading covers them. No row
was deleted and no Q-id, source or kind was changed.

## Left open

1. **A translated or respelt name can sit in rows not sampled.** The one
   error is of that kind. The pass rule does not call for a full check,
   so none was made. 98 rows rest on a list entry (six list pages and
   one club article); 24 of them were in the sample, so a name-only pass
   over the other 74 would be seven pages.
2. **The citation behind line 4** (the book Geliebter Feind) was cut
   short in the extract, so "Leykam, 2008" in the note was not re-read.
3. **`check_derbies.py` already reported the Augsburg flag** ("The
   marker can go") and exits 0 on it, by design: a club arriving on
   the map is reported, not rejected. So a stale flag stays until a
   person reads the report. Whether it should turn red is Alexandru's
   call; nothing was changed in the checker.
