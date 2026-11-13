# Club fact check, phase 1c: capacity of the clubs whose capacity comes from Wikidata only (2026-11-12)

PR #212. Phase 1a (sample of 60) and phase 1b (tiers) are in `2026-11-clubs.md`.

## Scope

- Clubs on the map: **588**.
- With a hand capacity in `data/clubs-manual.csv` (a number or `<clear>`): 153. Not checked here.
- With no hand capacity row and no capacity at all (blank on the map): 51. Nothing to compare.
- **In scope: 384** clubs whose capacity is Wikidata's figure for the ground (tier 1: 164, tier 2: 151, tier 3: 30, tier 4: 39).

Seven of the 384 carry a hand note that already records their capacity as contested and deliberately unchanged (Aston Villa, Fulham, Stoke City, PEC Zwolle, Jong Ajax, KRC Genk, SK Beveren). They have no capacity cell, so they are in scope; none was corrected.

## Method

- Temporary workflow `probe-audit.yml` on draft PR #212, **4 runs used of the 8 allowed**. User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, one request per second to Wikimedia, `maxlag` set. What it read was posted as comments on PR #212 (tables and snippets, never a page).
- **Runs 1 and 2 read nothing from Wikidata.** With `maxlag=5` every `wbgetentities` call was refused for the whole run (the log of run 2: query-service lag between 6.7 and 11.4 seconds for 20 minutes; run 1 did not log the reason, which was the session's own omission). Both runs made requests, so both count.
- **Run 3 raised `maxlag` to 15 for www.wikidata.org only**, after 246 seconds of waiting at 5. This departs from the recommended value of 5; it covered 17 read-only calls. Every Wikipedia call stayed at `maxlag=5` and none was refused. Run 3: 824 Wikimedia requests, StadiumDB's 13 country tables (robots.txt read first: it disallows only `/lay-gfx/`), and the references next to the differing figures.
- Run 3 took, per club: the `P115` ground of the club's item whose label is the ground name in the club file (383 matched by label, 1 by its capacity figure), that item's sitelinks, and section 0 of the ground's article in the wiki of the club's country and in English. The capacity field is the first number of the infobox's capacity line.
- Run 4 (follow-up for 32 unresolved clubs): the pages their articles' link lists and references name (at most three per club, robots.txt first, news and statistics hosts left out), seven more pages (three league club pages on the pattern of references found in run 3: Lega Serie A for Parma, Swiss Football League for Étoile Carouge and FC Basel, the Basel one answering 404; three StadiumDB ground pages named by link lists; one club URL guessed from memory for Austria Lustenau, which answered 404), and four it.wikipedia infoboxes.
- **Hosts that did not answer or were closed, none routed around**: mhscfoot.com, fcbotosani.ro, onlinebettingacademy.com, germanfootballgrounds.com and superliga.rs (robots.txt or closed), racingstub.com (429), numero-diez.com (451), pressonline.rs (403), about twenty dead links (404), five unreachable hosts.

### Limits

- **it.wikipedia was not read in the comparison**: its infobox calls the field `posti`, which the probe did not look for. All 36 Italian clubs were compared with en.wikipedia. Found in run 4, not fixed in the probe.
- The first number of an infobox line can be an old or a concert figure. Eight of the 60 resolved differences were this and nothing else ("agrees on reading" below); the 56 left over will contain more.
- "Agrees" means within 3 percent of Wikipedia's literal figure. It does not say Wikipedia is right, and for a ground with one figure everywhere Wikidata and Wikipedia may share an origin.
- No infobox in scope pulled its capacity from Wikidata by an explicit call. The two "not independent" clubs have an article with no capacity figure in the local wiki and none in English.

## Verdict rules

The capacity rule of phase 1a, unchanged. `wrong` only when no source read is within 3 percent of the map's figure AND the evidence is solid: two independent sources within 3 percent of each other, or a page of the club or its league, or a Wikipedia figure whose cited reference was read and says the same. Wikipedia in all languages is one source; Wikidata judges nothing. `disputed` when the sources disagree by more than 3 percent or the figure depends on the configuration (the range is recorded, nothing is corrected). `cannot verify` when Wikipedia stands alone without a readable reference. `agrees on reading` (added here) when the mechanical difference came from the first number of the infobox line being another state of the ground, and the article or a league page gives the map's figure as the current one.

## Comparison (run 3)

| class | tiers 1 and 2 | tier 3 and lower | all |
|---|---|---|---|
| agrees (within 3 percent) | 222 | 44 | 266 |
| differs (more than 3 percent, literal figure) | 91 | 25 | 116 |
| not independent (no figure of its own) | 2 | 0 | 2 |
| no article | 0 | 0 | 0 |
| total | 315 | 69 | 384 |

The two "not independent" clubs are named below the table of resolved clubs.

## Resolved: the first 60 of the 116 in priority order

Priority: tier 3 and lower first (25), then the largest percentage difference (35).

| verdict | tiers 1 and 2 | tier 3 and lower | all |
|---|---|---|---|
| wrong, corrected | 10 | 11 | 21 |
| disputed | 14 | 10 | 24 |
| agrees on reading | 8 | 0 | 8 |
| cannot verify | 3 | 4 | 7 |
| total | 35 | 25 | 60 |

### Corrections written (21 rows in `data/clubs-manual.csv`)

Each row names its sources and the date in the `source` and `note` cells; where other figures exist the note has the contested-capacity shape. Five rows already existed (tier rows) and got the capacity cell and an added note; 16 are new.

| club | Q-id | tier | map held | now | sources read (first is the row's first URL) |
|---|---|---|---|---|---|
| BSG Chemie Leipzig | `Q1921747` | 4 | 20000 | **4999** | de/en infobox 4,999 (current, limited by the authority); europlan-online "Kapazität: 4.999"; StadiumDB 10500 not taken. https://de.wikipedia.org/wiki/Alfred-Kunze-Sportpark |
| Hannover 96 II | `Q16573990` | 4 | 18000 | **5001** | de infobox 5.001; liga3-online (a reference of the article) "Eilenriedestadion in Hannover (5.000 Plätze)". https://de.wikipedia.org/wiki/Eilenriedestadion |
| 1. FSV Mainz 05 II | `Q16525419` | 4 | 20300 | **7134** | club page mainz05.de/bruchwegstadion "Kapazität: 7.134 Plätze"; de/en infobox. https://www.mainz05.de/bruchwegstadion |
| VfB Oldenburg | `Q826212` | 4 | 32000 | **15200** | de/en infobox and en text 15,200; StadiumDB 15200. https://de.wikipedia.org/wiki/Marschweg-Stadion |
| Würzburger Kickers | `Q535785` | 3 | 10504 | **13090** | de/en infobox; europlan-online "Kapazität: 13.090"; wuerzburgwiki.de 13.138 and names 10.504 (the map's figure) as the earlier 3. Liga state. https://de.wikipedia.org/wiki/Akon_Arena |
| Rot-Weiß Oberhausen | `Q157020` | 4 | 21318 | **17165** | club page rwo1904.de/stadion/stadion-niederrhein "Platz für 17.165 Zuschauer"; de/en infobox; StadiumDB 21318 not taken. https://www.rwo1904.de/stadion/stadion-niederrhein |
| VfR Aalen | `Q692586` | 4 | 13271 | **11088** | club page vfr-aalen.de/verein/arena "Gesamtkapazität 11.088"; europlan-online; de infobox; StadiumDB 11088; en 14500 not taken. https://www.vfr-aalen.de/verein/arena |
| SC Fortuna Köln | `Q310608` | 3 | 13750 | **11748** | club page fortuna-koeln.de/club/suedstadion/ "gesamt: 11.748 Plätze"; de/en infobox; StadiumDB 14944 not taken. https://www.fortuna-koeln.de/club/suedstadion/ |
| SC Verl | `Q666010` | 3 | 5001 | **5207** | de/en infobox (since the 2023 extension); liga3-online (a reference of the article) "mit nun 5.207 Plätzen"; club page 404. https://de.wikipedia.org/wiki/Sportclub_Arena |
| KSV Hessen Kassel | `Q819354` | 4 | 17993 | **18737** | de/en infobox and text 18,737; StadiumDB 18800 (within 3 percent). https://de.wikipedia.org/wiki/Auestadion |
| SV Meppen | `Q819400` | 3 | 13663 | **13241** | club page svmeppen.de/stadion "13.241 Zuschauern Platz"; de/en infobox. https://www.svmeppen.de/stadion |
| Racing de Santander | `Q12236` | 1 | 22 | **22514** | es infobox 22.514 citing the club (404); StadiumDB 22514; en and es text 22,308 not taken; the map held 22. https://es.wikipedia.org/wiki/Campos_de_Sport_de_El_Sardinero_(1988) |
| Pisa Sporting Club | `Q289613` | 2 | 10442 | **12508** | it infobox and text "12508 omologati", citing pisanews.net (read: "nuova capienza, fissata a 12.508"); en "25,000 (12,508 approved)". https://it.wikipedia.org/wiki/Stadio_Arena_Garibaldi-Romeo_Anconetani |
| Athens Kallithea F.C. | `Q1547133` | 2 | 4200 | **6300** | club page akfc66.gr/tickets/stadium "seating capacity of 6,300"; el/en infobox; el text: 4,200 was the 1970 figure. https://akfc66.gr/tickets/stadium |
| Étoile Carouge | `Q166496` | 2 | 7200 | **4110** | league page sfl.ch/teams/etoile-carouge-fc "4110 Capacité du stade"; fr infobox; en 3600 not taken. https://sfl.ch/teams/etoile-carouge-fc |
| ACF Fiorentina | `Q2052` | 1 | 43325 | **24786** | league page legaseriea.it/team/fiorentina/stadium "Capienza: 24 786"; en infobox; it text 43147 (full ground) and StadiumDB 22000 not taken. https://www.legaseriea.it/team/fiorentina/stadium |
| FK Javor Ivanjica | `Q218724` | 2 | 5000 | **3000** | club page fkjavor.com/stadion/ "Kapacitet stadiona je 3000 mesta"; en infobox; sr text; StadiumDB 3000. https://fkjavor.com/stadion/ |
| Yverdon-Sport FC | `Q669130` | 2 | 6600 | **5100** | league page sfl.ch/teams/yverdon-sport-fc "5100 Capacité du stade"; fr infobox; de 4000 and en 6600 not taken. https://sfl.ch/teams/yverdon-sport-fc |
| CFR Cluj | `Q205998` | 1 | 23500 | **17408** | club page cfr1907.ro/info-utile/: seven sectors adding up to 17408; ro/en infobox cite it; StadiumDB 23500 not taken. https://cfr1907.ro/info-utile/ |
| Dijon FCO | `Q503317` | 2 | 15995 | **15459** | club page dfco.fr/club/stade-gaston-gerard/ "capacité commerciale totale ... 15459 places"; en infobox; fr 18692 and StadiumDB 16288 not taken. https://www.dfco.fr/club/stade-gaston-gerard/ |
| Unión Deportiva Almería | `Q10407` | 2 | 22000 | **18331** | club news page udalmeriasad.com "el aforo, que ahora es de 18.331" (undated); es infobox; en 17,400 and ca 23.000 not taken. https://www.udalmeriasad.com/noticias/mas-de-17000-espectadores-en-el-power-horse-stadium |

### Every resolved club

`wp` is the figure the comparison used (wiki in brackets), `sdb` StadiumDB's country table (blank: no ground matched).

| # | club | Q-id | tier | map | wp | diff | sdb | verdict | figure or range | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | BSG Chemie Leipzig | `Q1921747` | 4 | 20000 | 4999 (de) | -75.0% | 10500 | wrong, corrected | 4999 | de/en infobox 4,999 (current, limited by the authority); europlan-online "Kapazität: 4.999"; StadiumDB 10500 not taken |
| 2 | Hannover 96 II | `Q16573990` | 4 | 18000 | 5001 (de) | -72.2% |  | wrong, corrected | 5001 | de infobox 5.001; liga3-online (a reference of the article) "Eilenriedestadion in Hannover (5.000 Plätze)" |
| 3 | 1. FSV Mainz 05 II | `Q16525419` | 4 | 20300 | 7134 (de) | -64.9% |  | wrong, corrected | 7134 | club page mainz05.de/bruchwegstadion "Kapazität: 7.134 Plätze"; de/en infobox |
| 4 | Sănătatea Cluj | `Q1463313` | 3 | 2000 | 750 (ro) | -62.5% |  | cannot verify | 750 (ro/en infobox, 500 seats) | no reference, no second source, no page named by the link lists |
| 5 | Știința Poli Timișoara II | `Q5425107` | 3 | 1000 | 1600 (ro) | 60.0% |  | disputed | 1600 to 2600 | ro infobox 1.600, en infobox 2,600; both describe a 2020 project; map 1000 |
| 6 | CSM Deva | `Q19902101` | 3 | 4000 | 1637 (ro) | -59.1% |  | disputed | 1637 to 4000 | ro infobox 1637, en infobox "4,000 seated" (= map) |
| 7 | VfB Oldenburg | `Q826212` | 4 | 32000 | 15200 (de) | -52.5% | 15200 | wrong, corrected | 15200 | de/en infobox and en text 15,200; StadiumDB 15200 |
| 8 | VFC Plauen | `Q700029` | 4 | 10490 | 5000 (de) | -52.3% |  | disputed | 5000 to 16400 | de infobox 5000, de text "16.400 Plätze" (5,000 seats and about 12,000 standing); a page on vogtlandstadion.de names an approved capacity of 5,000 but could not be tied to this ground; map 10490 matches neither |
| 9 | Chemnitzer FC | `Q161554` | 4 | 25000 | 15000 (de) | -40.0% |  | cannot verify | 15000 (de/en infobox, "current") | en text says 16,061; no reference; the club page read (chemnitzerfc.de/cfc/stadion/anfahrt/) carries no figure; map 25000 is the en infobox's "original" |
| 10 | SC Wiedenbrück | `Q479269` | 4 | 5000 | 3000 (de) | -40.0% |  | cannot verify | 3000 (de) or 3500 (en text) | no reference, no second source |
| 11 | Sportfreunde Lotte | `Q666067` | 4 | 7474 | 10059 (de) | 34.6% |  | cannot verify | 10059 (de/en infobox and text) | club page 404; stadionwelt and groundhopping.de pages carry no figure; map 7474 |
| 12 | SV Sandhausen | `Q639525` | 4 | 12100 | 15414 (de) | 27.4% | 12100 | disputed | 12100 to 15414 | de/en infobox 15,414 against StadiumDB 12100 (= map) |
| 13 | Würzburger Kickers | `Q535785` | 3 | 10504 | 13090 (de) | 24.6% |  | wrong, corrected | 13090 | de/en infobox; europlan-online "Kapazität: 13.090"; wuerzburgwiki.de 13.138 and names 10.504 (the map's figure) as the earlier 3. Liga state |
| 14 | Rot-Weiß Oberhausen | `Q157020` | 4 | 21318 | 17165 (de) | -19.5% | 21318 | wrong, corrected | 17165 | club page rwo1904.de/stadion/stadion-niederrhein "Platz für 17.165 Zuschauer"; de/en infobox; StadiumDB 21318 not taken |
| 15 | VfR Aalen | `Q692586` | 4 | 13271 | 11088 (de) | -16.4% | 11088 | wrong, corrected | 11088 | club page vfr-aalen.de/verein/arena "Gesamtkapazität 11.088"; europlan-online; de infobox; StadiumDB 11088; en 14500 not taken |
| 16 | Hamburger SV II | `Q5644342` | 4 | 2400 | 2018 (de) | -15.9% |  | disputed | 2018 to 2400 | de infobox and text 2018; stadionwelt "Kapazität: 2.400" (= map) |
| 17 | SC Fortuna Köln | `Q310608` | 3 | 13750 | 11748 (de) | -14.6% | 14944 | wrong, corrected | 11748 | club page fortuna-koeln.de/club/suedstadion/ "gesamt: 11.748 Plätze"; de/en infobox; StadiumDB 14944 not taken |
| 18 | SSV Ulm 1846 | `Q14551982` | 4 | 19500 | 17400 (de) | -10.8% | 19500 | disputed | 17400 to 19500 | de/en infobox 17,400 against StadiumDB 19500 (= map) |
| 19 | SV Waldhof Mannheim | `Q170134` | 3 | 27000 | 24302 (de) | -10.0% | 27000 | disputed | 24302 to 27000 | de infobox 24.302, en infobox 25,667 (reference 404), StadiumDB 27000 (= map) |
| 20 | TuS Koblenz | `Q155452` | 4 | 9500 | 10176 (de) | 7.1% | 15000 | disputed | 9500 to 15000 | de infobox 10.176, en text 9,500 (= map), StadiumDB 15000 |
| 21 | SC Verl | `Q666010` | 3 | 5001 | 5207 (de) | 4.1% |  | wrong, corrected | 5207 | de/en infobox (since the 2023 extension); liga3-online (a reference of the article) "mit nun 5.207 Plätzen"; club page 404 |
| 22 | KSV Hessen Kassel | `Q819354` | 4 | 17993 | 18737 (de) | 4.1% | 18800 | wrong, corrected | 18737 | de/en infobox and text 18,737; StadiumDB 18800 (within 3 percent) |
| 23 | SV Wehen Wiesbaden | `Q310621` | 3 | 12560 | 12100 (de) | -3.7% | 12600 | disputed | 12100 to 15295 | de infobox 12.100, en infobox 15,295, StadiumDB 12600; the map's 12560 is within 3 percent of StadiumDB |
| 24 | Rot-Weiss Essen | `Q155218` | 3 | 20650 | 19962 (de) | -3.3% | 19962 | disputed | 19962 to 20650 | de infobox and StadiumDB 19962; en infobox 20,650 (= map); stadion-essen.de says "aktuellen 20.000" |
| 25 | SV Meppen | `Q819400` | 3 | 13663 | 13241 (de) | -3.1% |  | wrong, corrected | 13241 | club page svmeppen.de/stadion "13.241 Zuschauern Platz"; de/en infobox |
| 26 | Racing de Santander | `Q12236` | 1 | 22 | 22514 (es) | 102236.4% | 22514 | wrong, corrected | 22514 | es infobox 22.514 citing the club (404); StadiumDB 22514; en and es text 22,308 not taken; the map held 22 |
| 27 | Pisa Sporting Club | `Q289613` | 2 | 10442 | 25000 (en) | 139.4% |  | wrong, corrected | 12508 | it infobox and text "12508 omologati", citing pisanews.net (read: "nuova capienza, fissata a 12.508"); en "25,000 (12,508 approved)" |
| 28 | Jong FC Utrecht | `Q24068131` | 2 | 450 | 1000 (nl) | 122.2% |  | disputed | 450 seated, 1000 total | configuration: nl infobox "1.000 (waarvan 450 zitplaatsen)"; the map holds the 450 seats of the stand |
| 29 | Mantova 1911 | `Q430993` | 2 | 7367 | 14884 (en) | 102.0% | 12000 | disputed | 7367 to 14884 | en infobox 14,884 ("capienza reale"), StadiumDB 12000, map 7367; club page 404 |
| 30 | MVV Maastricht | `Q876568` | 2 | 10000 | 18000 (nl) | 80.0% | 10000 | agrees on reading | 10000 | en infobox and StadiumDB 10000 (= map); nl infobox "18.000 (maximaal); 9.000 (huidig)", the first number is the old maximum |
| 31 | FK Čukarički | `Q213161` | 1 | 4070 | 7000 (sr) | 72.0% |  | disputed | 4070 to 7000 | sr infobox 7.000 (reference superliga.rs closed by robots.txt), en infobox 4,070 (= map) |
| 32 | A.S. Anagennisi Karditsas (football) | `Q123283162` | 2 | 13000 | 5000 (el) | -61.5% |  | disputed | 3500 to 5000 | el infobox "~5.000" (reference is a PDF, not parsed), en infobox 3,500; map 13000 is outside both |
| 33 | G.D. Estoril Praia | `Q634829` | 1 | 5094 | 8000 (pt) | 57.0% | 8000 | agrees on reading | 5094 | pt/en infobox "8 000; 5 094 permitido" and text: current capacity limited to 5,094 (= map); 8000 is the nominal figure (StadiumDB too) |
| 34 | Jong Ajax | `Q1770361` | 2 | 5000 | 2250 (nl) | -55.0% |  | disputed | 2250 or 5000 | ALREADY ON RECORD as contested (hand row of 2026-10-01, not changed). New this session: nl/en infobox 2250 (en: "2,250 seats (main field)"), and ajaxinside.nl, the page both cite, reads "Capaciteit 2.250" |
| 35 | Athens Kallithea F.C. | `Q1547133` | 2 | 4200 | 6300 (el) | 50.0% |  | wrong, corrected | 6300 | club page akfc66.gr/tickets/stadium "seating capacity of 6,300"; el/en infobox; el text: 4,200 was the 1970 figure |
| 36 | AFC Metalul Buzău | `Q37855796` | 2 | 3000 | 1606 (ro) | -46.5% |  | cannot verify | 1606 (ro/en infobox and ro text) | no reference, no second source, no page named by the link lists; map 3000 |
| 37 | FC Basel | `Q189671` | 1 | 38512 | 56000 (de) | 45.4% | 36000 | agrees on reading | 38512 | de infobox "56'000 (altes Stadion); 38'512 (neues Stadion)", fr 38512, en "38,512 (Football)" (= map); StadiumDB 36000 |
| 38 | Étoile Carouge | `Q166496` | 2 | 7200 | 4110 (fr) | -42.9% |  | wrong, corrected | 4110 | league page sfl.ch/teams/etoile-carouge-fc "4110 Capacité du stade"; fr infobox; en 3600 not taken |
| 39 | ACF Fiorentina | `Q2052` | 1 | 43325 | 24786 (en) | -42.8% | 22000 | wrong, corrected | 24786 | league page legaseriea.it/team/fiorentina/stadium "Capienza: 24 786"; en infobox; it text 43147 (full ground) and StadiumDB 22000 not taken |
| 40 | SC Austria Lustenau | `Q696507` | 1 | 8800 | 5138 (de) | -41.6% |  | agrees on reading | 8800 | en infobox "5,138 (before the most recent renovation)", en text "a total of 8,800 spectators" (= map); de infobox still has 5138; rests on en.wikipedia's text alone |
| 41 | FK Javor Ivanjica | `Q218724` | 2 | 5000 | 3000 (en) | -40.0% | 3000 | wrong, corrected | 3000 | club page fkjavor.com/stadion/ "Kapacitet stadiona je 3000 mesta"; en infobox; sr text; StadiumDB 3000 |
| 42 | Yverdon-Sport FC | `Q669130` | 2 | 6600 | 4000 (de) | -39.4% |  | wrong, corrected | 5100 | league page sfl.ch/teams/yverdon-sport-fc "5100 Capacité du stade"; fr infobox; de 4000 and en 6600 not taken |
| 43 | SK Beveren | `Q509170` | 1 | 13290 | 8190 (nl) | -38.4% |  | disputed | 8190 or 13290 | ALREADY ON RECORD as contested (hand row, not changed): nl/fr/en infobox 8,190 (reference 404), fr text 13290 for 2011, StadiumDB 13290 per the hand note |
| 44 | Getafe CF | `Q8806` | 1 | 16500 | 10500 (es) | -36.4% | 10500 | disputed | 10500 or 16500 | club page getafecf.com DatosGenerales "CAPACIDAD: 16.500" (= map); es infobox "~10.500 (En reforma)", the Marca article it cites (read) and StadiumDB say 10,500 while the ground is rebuilt until 2027 |
| 45 | FC Botoșani | `Q1262822` | 1 | 12000 | 7782 (ro) | -35.1% | 8500 | disputed | 7782 to 8500 | ro/en infobox 7,782; StadiumDB 8500, and its ground page reads "used to hold 12,000 ... now around 8,500"; the map's 12000 is the old figure by both, but the two current figures are 8 percent apart; fcbotosani.ro closed |
| 46 | Montpellier Hérault SC | `Q19513` | 2 | 32900 | 22000 (fr) | -33.1% |  | disputed | 20484 to 22000 | fr infobox 22000 (allezpaillade.com, 2017, read), en infobox "20,484 (full capacity 33,556 not used)"; mhscfoot.com closed; map 32900 is the full ground |
| 47 | Almere City FC | `Q653119` | 2 | 4501 | 5800 (nl) | 28.9% | 4501 | disputed | 4501 or 5800 | en infobox and StadiumDB 4501 (= map); nl infobox 5.800 ("in de zomer van 2026 uitgebreid"); the club's page almerecity.nl speaks of the extension to 5.800 as coming |
| 48 | FCV Dender EH | `Q1065328` | 2 | 12000 | 8548 (nl) | -28.8% |  | disputed | 6429 to 12000 | nl infobox 8.548, fr 12000 (= map), en 6,429; club reference 404 |
| 49 | H. Verona | `Q8639` | 2 | 31045 | 39211 (en) | 26.3% |  | agrees on reading | 31045 | it text "39211 posti complessivi, di cui solo 31045 omologati" (= map); en infobox 39,211 is the total (en text says 31,713 approved) |
| 50 | CFR Cluj | `Q205998` | 1 | 23500 | 17408 (ro) | -25.9% | 23500 | wrong, corrected | 17408 | club page cfr1907.ro/info-utile/: seven sectors adding up to 17408; ro/en infobox cite it; StadiumDB 23500 not taken |
| 51 | Parma Calcio 1913 | `Q2693` | 1 | 22352 | 27906 (en) | 24.8% |  | agrees on reading | 22352 | league page legaseriea.it/team/parma/stadium "Capienza: 22 352" (= map); en infobox "27,906 (often just 22,352 allowed)" |
| 52 | Coventry City F.C. | `Q19580` | 1 | 32609 | 40000 (en) | 22.7% | 32609 | agrees on reading | 32609 | en infobox "40,000 (concerts); 32,609 (football and rugby matches)" (= map); StadiumDB 32609 |
| 53 | RC Strasbourg Alsace | `Q126334` | 1 | 26109 | 32000 (fr) | 22.6% |  | cannot verify | 32000 (fr) or 32300 (en) | fr text calls it the target of works "à l'horizon 2026"; the cited destination-meinau.eu carries no figure; racingstub.com answered 429; map 26109 |
| 54 | First Vienna FC 1894 | `Q686826` | 2 | 5500 | 4500 (de) | -18.2% | 6000 | disputed | 4238 to 6000 | de infobox 4500 (Wien Museum article, read: "rund 4.500"), en infobox 4,238, en text 5,500 (= map), StadiumDB 6000 |
| 55 | Empoli Football Club | `Q6703` | 2 | 19847 | 16284 (en) | -18.0% |  | cannot verify | 16284 (en) or 16800 (it text) | no reference; numero-diez.com 451, empolifc.com unreachable; map 19847 |
| 56 | FK Borac Čačak | `Q754310` | 2 | 8000 | 6574 (sr) | -17.8% |  | agrees on reading | 8000 | en infobox 8,000 (= map) and two news pages the article cites (blic.rs, novosti.rs, read) on the rebuilt ground with 8,000 seats; sr infobox 6.574 is the 2007 figure |
| 57 | Dijon FCO | `Q503317` | 2 | 15995 | 18692 (fr) | 16.9% | 16288 | wrong, corrected | 15459 | club page dfco.fr/club/stade-gaston-gerard/ "capacité commerciale totale ... 15459 places"; en infobox; fr 18692 and StadiumDB 16288 not taken |
| 58 | Kapfenberger SV | `Q741382` | 2 | 12000 | 10000 (de) | -16.7% |  | disputed | 9640 to 12000 | de infobox 10.000, en 9,640 (reference closed), StadiumDB's ground page "Capacity 12 000" (= map) |
| 59 | Unión Deportiva Almería | `Q10407` | 2 | 22000 | 18331 (es) | -16.7% |  | wrong, corrected | 18331 | club news page udalmeriasad.com "el aforo, que ahora es de 18.331" (undated); es infobox; en 17,400 and ca 23.000 not taken |
| 60 | FK Novi Pazar | `Q995069` | 1 | 12000 | 10000 (en) | -16.7% | 6900 | disputed | 6900 to 10000 | en infobox 10,000, sr text about 9.200, StadiumDB 6900; map 12000 is outside all three |

The two "not independent" clubs as the map names them: Niki Volos F.C. (`Q3180055`, GR, tier 2, map 2500; the el.wikipedia article has no capacity figure and there is no English figure) and FK Mladost Lučani (`Q1945740`, RS, tier 1, map 8000; the same for sr.wikipedia).

### Left for Alexandru (nothing below was decided)

- **Jong Ajax** (`Q1770361`): the hand row of 2026-10-01 leaves 5000 against 2250 contested because 2250 had one source. This session read a second page, ajaxinside.nl ("Capaciteit 2.250"), which both infoboxes cite, and en.wikipedia's infobox says "2,250 seats (main field)". ajaxinside.nl is not the club's own site. Not changed, because the row records a deliberate decision.
- **FC Botoșani** (`Q1262822`): Wikipedia (7,782) and StadiumDB (about 8,500) both say the map's 12,000 is the figure before the ground became all-seated. They are 8 percent apart, so nothing was written.
- **Getafe CF** (`Q8806`): the club's own page still says 16,500 (the map's figure); Marca, es.wikipedia and StadiumDB say 10,500 while the Coliseum is rebuilt until 2027.
- **Montpellier HSC** (`Q19513`): the map's 32,900 is the full ground; Wikipedia gives 22,000 (fr) and 20,484 (en) in use. The club's site is closed to the probe.
- **Almere City** (`Q653119`): 4,501 on the map; nl.wikipedia says extended to 5,800 in summer 2026 and the club's site announces that extension; no page read confirms it is finished.
- **A.S. Anagennisi Karditsa** (`Q123283162`, map 13,000) and **FK Novi Pazar** (`Q995069`, map 12,000): every figure read is far below the map's, and the figures read disagree with each other.
- **Chemnitzer FC** (map 25,000; Wikipedia 15,000 "current"), **Sportfreunde Lotte** (7,474; 10,059), **Metalul Buzău** (3,000; 1,606), **Sănătatea Cluj** (2,000; 750), **Empoli** (19,847; 16,284 or 16,800), **RC Strasbourg** (26,109; about 32,000 after the works), **SC Wiedenbrück** (5,000; 3,000 or 3,500): Wikipedia alone, no reference that could be read. A club or league page would settle each.

## Left for a next session: 56 clubs

Classified "differs" and not opened in Part B, in priority order (all tiers 1 and 2). `en` is en.wikipedia's figure where the comparison used another wiki (`=` where it is the same wiki, N where it has none). Italian clubs: read it.wikipedia's `posti` field first.

| # | club | Q-id | cc | tier | map | wp | diff | en | sdb | other numbers on the line |
|---|---|---|---|---|---|---|---|---|---|---|
| 61 | Panionios F.C. | `Q460494` | GR | 2 | 11115 | 9363 (el) | -15.8% | 11700 | 11115 |  |
| 62 | FC Thun | `Q464775` | CH | 1 | 10000 | 8426 (de) | -15.7% | 10000 | 9500! | 1972/10398 |
| 63 | AD Ceuta FC | `Q5773365` | ES | 2 | 6500 | 5500 (es) | -15.4% | 5500 |  |  |
| 64 | Cesena Football Club | `Q16848949` | IT | 2 | 23860 | 20194 (en) | -15.4% | = |  |  |
| 65 | KRC Genk | `Q216032` | BE | 1 | 25000 | 21300 (nl) | -14.8% | 23718 |  |  |
| 66 | Royal Excelsior Virton | `Q650917` | BE | 2 | 4000 | 4572 (nl) | 14.3% | 4015 |  |  |
| 67 | FC Wil | `Q187091` | CH | 2 | 6958 | 6048 (de) | -13.1% | 6048 |  |  |
| 68 | K.V.C. Westerlo | `Q849544` | BE | 1 | 7982 | 9000 (nl) | 12.8% | 8035 | 8035 |  |
| 69 | Lincoln City F.C. | `Q18519` | GB | 2 | 10120 | 11400 (en) | 12.6% | = | 10669! |  |
| 70 | Football Club d'Annecy | `Q1140695` | FR | 2 | 15660 | 13699 (fr) | -12.5% | 15660 |  |  |
| 71 | Atromitos F.C. | `Q757754` | GR | 1 | 10200 | 8969 (el) | -12.1% | 9035 | 10000 |  |
| 72 | PEC Zwolle | `Q269151` | NL | 1 | 12500 | 14000 (nl) | 12.0% | 14000 | 13250 |  |
| 73 | Admira Wacker | `Q698702` | AT | 2 | 12000 | 10600 (de) | -11.7% | 10600 | 7010 |  |
| 74 | FK Crvena zvezda | `Q173009` | RS | 1 | 55538 | 49167 (sr) | -11.5% | 49167 | 51755 |  |
| 75 | FC Volendam | `Q738060` | NL | 2 | 6200 | 6800 (nl) | 9.7% | N | 6984 |  |
| 76 | Fulham F.C. | `Q18708` | GB | 1 | 25700 | 28107 (en) | 9.4% | = | 27782 |  |
| 77 | US Boulogne CO | `Q309400` | FR | 2 | 6600 | 6000 (fr) | -9.1% | 6600 | 15034 |  |
| 78 | Ascoli Calcio 1898 FC | `Q6630` | IT | 2 | 13708 | 12461 (en) | -9.1% | = |  |  |
| 79 | FK Partizan | `Q188656` | RS | 1 | 32710 | 29775 (sr) | -9.0% | 29775 | 32710 | 40000 |
| 80 | FC Aarau | `Q603271` | CH | 2 | 9249 | 8450 (de) | -8.6% | 9249 | 9249 | 1262/7188 |
| 81 | Stoke City F.C. | `Q18736` | GB | 2 | 27740 | 30089 (en) | 8.5% | = |  |  |
| 82 | A.P.S. Panthrakikos | `Q433230` | GR | 2 | 6198 | 6700 (el) | 8.1% | 6198 | 3000 |  |
| 83 | Feyenoord Rotterdam | `Q134241` | NL | 1 | 51577 | 47500 (nl) | -7.9% | 47500 | 51117! |  |
| 84 | NAC Breda | `Q332642` | NL | 2 | 19000 | 20500 (nl) | 7.9% | 20500 | 19000 |  |
| 85 | Standard Liège | `Q190561` | BE | 1 | 30023 | 27670 (nl) | -7.8% | 27670 | 27670 |  |
| 86 | Elche CF | `Q10512` | ES | 1 | 31388 | 33732 (es) | 7.5% | 31388 | 31388 |  |
| 87 | FC Eindhoven | `Q876699` | NL | 2 | 4500 | 4200 (nl) | -6.7% | N | 4200 |  |
| 88 | Atalanta Bergamasca Calcio | `Q1886` | IT | 1 | 24950 | 23439 (en) | -6.1% | = |  |  |
| 89 | Real Sociedad | `Q10315` | ES | 1 | 40000 | 42300 (es) | 5.8% | 40000 | 40000 |  |
| 90 | Athlitiki Enosi Larissa F.C. | `Q275626` | GR | 2 | 17118 | 16118 (el) | -5.8% | 17118 |  | 33000 |
| 91 | Villarreal CF | `Q12297` | ES | 1 | 24891 | 23500 (es) | -5.6% | 24000 | 21332 |  |
| 92 | US Cremonese | `Q759482` | IT | 2 | 15191 | 16003 (en) | 5.3% | = | 15191 |  |
| 93 | C.D. Tenerife | `Q216661` | ES | 2 | 21732 | 22824 (es) | 5.0% | 22824 |  |  |
| 94 | SV Ried | `Q457460` | AT | 1 | 7680 | 7300 (de) | -4.9% | 7680 |  |  |
| 95 | FC St. Gallen | `Q659212` | CH | 1 | 19694 | 20660 (de) | 4.9% | 20660 | 19694 |  |
| 96 | SC Kriens | `Q671950` | CH | 2 | 5360 | 5100 (de) | -4.9% |  |  |  |
| 97 | Sint-Truidense V.V. | `Q138248` | BE | 1 | 11250 | 11756 (nl) | 4.5% | 11756 |  |  |
| 98 | Grasshopper Club Zürich | `Q201360` | CH | 1 | 25000 | 26104 (de) | 4.4% | 26105 |  | 30930/25773/50044 |
| 99 | FC Zürich | `Q206692` | CH | 1 | 25000 | 26104 (de) | 4.4% | 26105 | 25000 | 30930/25773/50044 |
| 100 | Eintracht Braunschweig | `Q154053` | DE | 2 | 24406 | 23325 (de) | -4.4% | 24406 | 23325 | 24406 |
| 101 | Chelsea F.C. | `Q9616` | GB | 1 | 41875 | 40044 (en) | -4.4% | = | 40022 |  |
| 102 | Stade rennais FC | `Q19509` | FR | 1 | 31127 | 29778 (fr) | -4.3% | 29778 | 29778 |  |
| 103 | SC Heerenveen | `Q200321` | NL | 1 | 26100 | 27224 (nl) | 4.3% | 27224 |  |  |
| 104 | Neuchâtel Xamax | `Q335195` | CH | 2 | 12000 | 12500 (de) | 4.2% | 12000 | 12000 |  |
| 105 | Paris FC | `Q1051013` | FR | 1 | 20000 | 19151 (fr) | -4.2% | 19142 | 20000 |  |
| 106 | Birmingham City F.C. | `Q19444` | GB | 2 | 30016 | 28754 (en) | -4.2% | = | 29409 |  |
| 107 | RKC Waalwijk | `Q24699` | NL | 2 | 7500 | 7186 (nl) | -4.2% | 7186 | 7500 |  |
| 108 | PSV Eindhoven | `Q11938` | NL | 1 | 36500 | 35000 (nl) | -4.1% | 35119 | 35119 |  |
| 109 | Crystal Palace F.C. | `Q19467` | GB | 1 | 26255 | 25194 (en) | -4.0% | = | 25194 |  |
| 110 | Willem II | `Q332664` | NL | 1 | 14637 | 15220 (nl) | 4.0% | 15220 | 14637 | 20000 |
| 111 | Fortuna Sittard | `Q854167` | NL | 1 | 12500 | 12000 (nl) | -4.0% | 12000 | 12000 |  |
| 112 | VfL Wolfsburg | `Q101859` | DE | 2 | 30000 | 28917 (de) | -3.6% | 30000 | 30000 |  |
| 113 | AJ Auxerre | `Q182876` | FR | 1 | 18541 | 17897 (fr) | -3.5% | 17897 |  |  |
| 114 | FC Emmen | `Q1061627` | NL | 2 | 8600 | 8309 (nl) | -3.4% | 8600 | 8301 |  |
| 115 | FC Vaduz | `Q216773` | CH | 1 | 7584 | 7838 (de) | 3.3% | 7584 |  |  |
| 116 | CD Castellón | `Q743557` | ES | 2 | 16000 | 15500 (es) | -3.1% | 15500 |  |  |

A `!` after a StadiumDB figure means the tool's ground name did not match the map's.

## Checks

- `load_manual()` of `tools/fetch_clubs.py` reads the file with 374 rows and reports nothing about the new or edited rows (its 13 messages are the standing notes on `skip` rows); a dry `apply_manual()` over the 13 club files gives 588 clubs and applies all 21 capacities.
- The club files were **not** regenerated here (the build has no offline mode); `build-clubs.yml` does it on `main` after the merge.
- No `SHELL_VERSION` change.


---

# Phase 1d: the capacity check finished (2026-11-13)

PR #213. The rules are those of phase 1c above: every correction rests on a page opened in this session, Wikidata judges nothing, Wikipedia in all languages is one source, the stored capacity is the league figure, a disputed value is never corrected, a closed host is never read.

## Method and limits

- Temporary workflow `probe-audit.yml` on draft PR #213, **3 runs used of the 8 allowed**, removed in its own commit before the data commit. User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, one request per second to Wikimedia, `maxlag=5` throughout and **never raised**.
- **Run 1** (97 clubs, 26 minutes, 277 Wikimedia and 500 other requests on 147 hosts): Wikidata refused every call at `maxlag=5` for 1,210 seconds (query-service lag of 6 to 15 seconds); the probe waited with a doubling pause, then gave the call up and found each ground's English article by the ground's name. 58 of those titles are the ones phase 1c took from Wikidata's sitelinks; the other 11 were wrong or missing (a disambiguation page, the club's article, no article) and were read again in run 2 with the phase 1c titles. **Run 2** (60 clubs, 4 minutes): Wikidata answered at `maxlag=5` with no wait for the 28 clubs asked; pages that need a browser were opened in Chromium. **Run 3** (39 clubs, 2 minutes): the displayed infobox row of it.wikipedia for the 36 Italian clubs, the references of five of them, two article re-reads.
- Per club: the capacity line of the ground's infobox in the local wiki and in English (the whole line), the sentences with a capacity figure, the references cited on that line, the StadiumDB country table and the ground's StadiumDB page where the article links it, club stadium pages among the article's external links, and the league's own club page where the league site's root page links it (sfl.ch, bundesliga.at, legab.it; laliga.com, ligue1.com, lpf.ro, proleague.be, legaseriea.it and slgr.gr gave no figure or no links). For every host: robots.txt, then the root page and the terms page it links, then the content page.
- **Closed or silent, never read and not routed around**: `eredivisie.nl` and `keukenkampioendivisie.nl` (their terms forbid robots, spiders, scrapers and automatic systems; run 1 had opened two keukenkampioendivisie.nl club pages, which gave no text, before run 2 found the wording, and nothing from them is used), and IABotmemento.invalid (robots.txt URLError), all.in.com.free.fr (root 403), dimoskarditsas.gov.gr (robots.txt URLError), empolifc.com (robots.txt URLError), jable.ulpgc.es (robots.txt 403), magnesianews.gr (robots.txt 403), ricerca.gelocal.it (robots.txt 403), stadion-stgallen.ch (robots.txt URLError), www.adceuta.org (robots.txt URLError), www.comune.modena.it (robots.txt URLError), www.fff.fr (robots.txt 403), www.fichajes.com (robots.txt 429), www.italia1910.com (robots.txt 403), www.lavoixdunord.fr (robots.txt 403), www.limmattalerzeitung.ch (robots.txt 403), www.lombardiabeniculturali.it (robots.txt URLError), www.osservatoriosport.interno.gov.it (robots.txt URLError), www.superleaguegreece.net (robots.txt URLError), www.tagblatt.ch (robots.txt 403), www.vicenzacalcio.com (robots.txt 503), www.vipiu.it (robots.txt 403), www.zurnal.rs (robots.txt 403). The hosts phase 1c found closed were not opened again. Single pages that a robots.txt disallows were skipped the same way (among them crvenazvezdafk.com, marca.com, excelsiorvirton.be, hln.be, sporza.be, nzz.ch, bernerzeitung.ch, cesenatoday.it, telegraph.co.uk, digitalhub.fifa.com).
- A club or league page that answers but shows no figure (premierleague.com, legaseriea.it, krcgenk.be, laliga.com, lpf.ro, bcfc.com, chelseafc.com) is recorded as "no figure", not as agreement.
- **"Two independent sources" here is often Wikipedia plus StadiumDB.** They may share an origin. The rows that rest on that pair alone, with no club or league page, say so: Crystal Palace, Fortuna Sittard, Chelsea, Standard Liège, Eintracht Braunschweig, Atalanta, Empoli.

## Part A: the 56 clubs left by phase 1c

| verdict | clubs |
|---|---|
| wrong, corrected | 25 |
| disputed, unchanged | 21 |
| agrees on a closer read | 8 |
| cannot verify | 2 |
| total | 56 |

Four of the 21 disputed clubs carry a hand row that already records the capacity as contested (KRC Genk, PEC Zwolle, Fulham, Stoke City). They were not changed. **New for PEC Zwolle**: the club's own page says 14,000, which by the verdict rule would decide it; the hand row of 2026-10-01 is left as it is and the decision is Alexandru's. For Stoke City (30,089) and Fulham (28,107) nothing new was read beyond what their rows already name.

| # | club | Q-id | cc | map held | verdict | figure or range | evidence | first URL |
|---|---|---|---|---|---|---|---|---|
| 61 | Panionios F.C. | `Q460494` | GR | 11115 | disputed | 9363 to 11700 | el infobox 9.363, en infobox 11,700, StadiumDB 11115 (= map) | https://el.wikipedia.org/wiki/%CE%A3%CF%84%CE%AC%CE%B4%CE%B9%CE%BF_%CE%9D%CE%AD%CE%B1%CF%82_%CE%A3%CE%BC%CF%8D%CF%81%CE%BD%CE%B7%CF%82 |
| 62 | FC Thun | `Q464775` | CH | 10000 | disputed | 9500 to 10398 | de infobox "Sitzplätze: 8426 Stehplätze: 1972 Total: 10'398" (phase 1c compared the seats alone); its reference sport.ch "Die Gesamtkapazität beträgt 10'398 Zuschauer"; en infobox 10,000 (= map); StadiumDB 9500; the league site's link list had no page for the club | https://sport.ch/fc-thun/374955/der-ewige-aussenseiter-will-die-erwartungen-auch-in-dieser-saison-uebertreffen-alles-wissenswerte-zum-fc-thun-gibt-es-hier |
| 63 | AD Ceuta FC | `Q5773365` | ES | 6500 | disputed | 5500 to 6500 | es and en infobox 5,500 (club page unreachable); en text 6,500 (= map); StadiumDB 6000; espanaestadios.com "a slightly reduced capacity of 6,000" for 2025-26 | https://espanaestadios.com/2018/12/05/ceuta-estadio-alfonso-murube/ |
| 64 | Cesena Football Club | `Q16848949` | IT | 23860 | wrong, corrected | 20194 | the club's stadium page "con i suoi 20.194 posti a sedere" and "Capienza 20.194"; it.wikipedia infobox "posti = 20 194"; en.wikipedia infobox 20,194; StadiumDB's country table 20194. Not taken: 23860 (Wikidata, which the map held until now). | https://www.cesenafc.com/it/society/stadium |
| 65 | KRC Genk | `Q216032` | BE | 25000 | disputed | 21300 to 25000 | the hand row of 2026-10-01 stands. nl infobox 21.300; en infobox 23,718 citing the club page, which was opened in a browser and showed no figure; StadiumDB 23718 | https://en.wikipedia.org/wiki/Cegeka_Arena |
| 66 | Royal Excelsior Virton | `Q650917` | BE | 4000 | cannot verify | 4015 or 4572 | Wikipedia alone: nl infobox 4.572, en infobox 4,015 (within 3 percent of the map); the club's stadium page is closed by robots.txt | https://nl.wikipedia.org/wiki/Yvan_Georgesstadion |
| 67 | FC Wil | `Q187091` | CH | 6958 | wrong, corrected | 5530 | the Swiss Football League's club page "5530 Capacité du stade", the league figure. Not taken: 6000 (the club's own page "Gesamtkapazität: 6000 Zuschauer", 700 seats and 5300 standing places; fcwil1900.ch the same); 6048 (de.wikipedia and en.wikipedia infobox); 6958 (Wikidata, which the map held until now). | https://sfl.ch/teams/fc-wil-1900 |
| 68 | K.V.C. Westerlo | `Q849544` | BE | 7982 | agrees | 8035 | club page "The stadium has a capacity of 8,035 spectators", en infobox and StadiumDB 8035, 0.7 percent from the map; nl infobox 9.000 stands alone | https://kvcwesterlo.be/en/t-kuipje/ |
| 69 | Lincoln City F.C. | `Q18519` | GB | 10120 | disputed | 10669 to 11400 | en infobox 11,400 (its club references answered 202 with no text); StadiumDB 10669; map 10120 below both | https://en.wikipedia.org/wiki/Sincil_Bank |
| 70 | Football Club d'Annecy | `Q1140695` | FR | 15660 | agrees | 15660 | en infobox 15,660 (= map), StadiumDB 15714; the fr infobox's 13699 equals a 2026 attendance listed on stades-spectateurs.com | https://en.wikipedia.org/wiki/Parc_des_Sports_(Annecy) |
| 71 | Atromitos F.C. | `Q757754` | GR | 10200 | wrong, corrected | 8969 | the club's stadium page "Σήμερα η χωρητικότητα του σταδίου είναι 8.969 θέσεις"; el.wikipedia infobox 8.969; en.wikipedia text 8,969. Not taken: 9035 (en.wikipedia infobox, 0.7 percent higher); 10000 (StadiumDB); 10200 (Wikidata, which the map held until now). | https://www.atromitosfc.gr/facilities/peristeri-stadium/ |
| 72 | PEC Zwolle | `Q269151` | NL | 12500 | disputed | 12500 to 14000 | the hand row of 2026-10-01 stands. NEW: the club's page "biedt na de uitbouw in de zomer van 2018 plaats aan 14.000 toeschouwers"; nl and en infobox 14,000; StadiumDB 13250 | https://www.peczwolle.nl/over-het-mac3park-stadion/ |
| 73 | Admira Wacker | `Q698702` | AT | 12000 | wrong, corrected | 10600 | the club's stadium page "bietet rund 10.600 Besuchern Platz"; stadionwelt.de "Kapazität von 10.600 Zuschauerplätzen"; de.wikipedia and en.wikipedia infobox 10.600. Not taken: 7010 (StadiumDB); 12000 (Wikidata, which the map held until now). | https://admirawacker.at/verein/stadion/ |
| 74 | FK Crvena zvezda | `Q173009` | RS | 55538 | disputed | 49167 to 51755 | sr and en infobox 49,167 citing the club's site (closed by robots.txt); StadiumDB 51755; map 55538 above both | https://sr.wikipedia.org/wiki/%D0%A1%D1%82%D0%B0%D0%B4%D0%B8%D0%BE%D0%BD_%D0%A0%D0%B0%D1%98%D0%BA%D0%BE_%D0%9C%D0%B8%D1%82%D0%B8%D1%9B |
| 75 | FC Volendam | `Q738060` | NL | 6200 | wrong, corrected | 6800 | the club's stadium page "tezamen goed voor een capaciteit van 6.800 toeschouwers"; nl.wikipedia infobox 6.800, citing that page. Not taken: 6984 (StadiumDB, 2.7 percent higher); 6200 (Wikidata, which the map held until now). | https://fcvolendam.nl/kras-stadion/algemene-informatie/ |
| 76 | Fulham F.C. | `Q18708` | GB | 25700 | disputed | 27782 to 28107 | the hand row of 2026-09-30 stands. en infobox 28,107 citing a Premier League news page (opened in a browser: no figure); StadiumDB 27782; map 25700 | https://en.wikipedia.org/wiki/Craven_Cottage |
| 77 | US Boulogne CO | `Q309400` | FR | 6600 | disputed | 6000 to 15034 | fr infobox 6 000 (reference lavoixdunord.fr closed); en infobox "6,600 ... 9,534 (2021)"; StadiumDB 15034 | https://fr.wikipedia.org/wiki/Stade_de_la_Lib%C3%A9ration |
| 78 | Ascoli Calcio 1898 FC | `Q6630` | IT | 13708 | wrong, corrected | 11326 | Lega B's own article on the ground, undated, "Attualmente lo Stadio Cino e Lillo Del Duca ha una capienza complessiva di 11.326 spettatori"; StadiumDB 11326. Not taken: 12461 (en.wikipedia infobox, no reference); 13708 (Wikidata, which the map held until now; it.wikipedia's infobox has no figure of its own and displays Wikidata's). | https://www.legab.it/news/5-curiosita-sullo-stadio-cino-e-lillo-del-duca-di-ascoli |
| 79 | FK Partizan | `Q188656` | RS | 32710 | disputed | 29775 to 32710 | sr and en infobox 29,775 citing the club page (404); en text 29,662; StadiumDB 32710 (= map) | https://sr.wikipedia.org/wiki/%D0%A1%D1%82%D0%B0%D0%B4%D0%B8%D0%BE%D0%BD_%D0%9F%D0%B0%D1%80%D1%82%D0%B8%D0%B7%D0%B0%D0%BD%D0%B0 |
| 80 | FC Aarau | `Q603271` | CH | 9249 | wrong, corrected | 8450 | the club's stadium page "momentan für 8'450 Zuschauer zugelassen"; the Swiss Football League's club page "8450 Capacité du stade"; europlan-online "Kapazität: 8.450"; de.wikipedia infobox 8'450. Not taken: 9249 (en.wikipedia infobox, StadiumDB and Wikidata, which the map held until now). | https://fcaarau.ch/stadion/ |
| 81 | Stoke City F.C. | `Q18736` | GB | 27740 | disputed | 27740 to 30089 | the hand row of 2026-09-30 stands. en infobox 30,089 (EFL reference 404; the Premier League page opened: no figure); StadiumDB 30089 | https://en.wikipedia.org/wiki/Bet365_Stadium |
| 82 | A.P.S. Panthrakikos | `Q433230` | GR | 6198 | disputed | 3000 to 6700 | el infobox 6.700 (reference unreachable); en infobox 6,198 (= map); StadiumDB 3000 | https://el.wikipedia.org/wiki/%CE%94%CE%B7%CE%BC%CE%BF%CF%84%CE%B9%CE%BA%CF%8C_%CE%A3%CF%84%CE%AC%CE%B4%CE%B9%CE%BF_%CE%9A%CE%BF%CE%BC%CE%BF%CF%84%CE%B7%CE%BD%CE%AE%CF%82 |
| 83 | Feyenoord Rotterdam | `Q134241` | NL | 51577 | wrong, corrected | 47500 | the stadium's own page "Het stadion heeft tijdens voetbalwedstrijden een capaciteit van 47.500 toeschouwers", the figure for football matches; nl.wikipedia infobox 47.500; en.wikipedia infobox "47,500 (limited capacity)". Not taken: 51117 (stadionfeijenoord.nl "een capaciteit van 51.117 plaatsen", en.wikipedia and StadiumDB: the full ground); 51577 (Wikidata, which the map held until now). | https://www.dekuip.com/nl/stadion-feijenoord |
| 84 | NAC Breda | `Q332642` | NL | 19000 | wrong, corrected | 20500 | nl.wikipedia and en.wikipedia infobox 20.500; Voetbal International, the reference of the nl infobox, "De club kan nu zo'n 20.500 toeschouwers ontvangen". Not taken: 19000 (StadiumDB and Wikidata, which the map held until now: the figure before the extension). | https://www.vi.nl/nieuws/nac-bouwt-door-en-kijkt-alweer-naar-verdere-uitbreiding-rat-verlegh-stadion |
| 85 | Standard Liège | `Q190561` | BE | 30023 | wrong, corrected | 27670 | nl.wikipedia infobox "27.670 toeschouwers"; en.wikipedia infobox "27,670 (limited capacity), 30,023 (maximum capacity)"; StadiumDB 27670. Not taken: 30023 (the maximum capacity, Wikidata's figure, which the map held until now). | https://nl.wikipedia.org/wiki/Maurice_Dufrasnestadion |
| 86 | Elche CF | `Q10512` | ES | 31388 | agrees | 31388 | club page "su capacidad actual es de 31.388 localidades" (= map), en infobox and StadiumDB the same; es infobox 33 732 stands alone | https://www.elchecf.es/estadio |
| 87 | FC Eindhoven | `Q876699` | NL | 4500 | wrong, corrected | 4200 | the club's stadium page "Het stadion heeft 4.200 zitplaatsen"; nl.wikipedia infobox 4.200; StadiumDB's country table 4200. Not taken: 4500 (Wikidata, which the map held until now). | https://fc-eindhoven.nl/de-club/jan-louwers-stadion/ |
| 88 | Atalanta Bergamasca Calcio | `Q1886` | IT | 24950 | wrong, corrected | 23439 | it.wikipedia infobox "posti = 23439" and en.wikipedia infobox 23,439, both citing Lega Serie A's stadium page for Atalanta, which was opened in a browser and showed no figure; StadiumDB's country table 23439. Not taken: 24950 (Wikidata, which the map held until now). The club's own stadium page (atalanta.it/stadio) was read and states no current capacity. | https://it.wikipedia.org/wiki/Stadio_di_Bergamo |
| 89 | Real Sociedad | `Q10315` | ES | 40000 | agrees | 40000 | en infobox and StadiumDB 40000 (= map); club page "Con capacidad para 41.000 espectadores" (2.5 percent); es infobox 42300 stands alone | https://www.realsociedad.eus/es/club/instalaciones |
| 90 | Athlitiki Enosi Larissa F.C. | `Q275626` | GR | 17118 | disputed | 16118 to 17118 | el infobox 16.118 and stadia.gr 16118; en infobox 17,118 (= map) | https://el.wikipedia.org/wiki/AEL_FC_Arena |
| 91 | Villarreal CF | `Q12297` | ES | 24891 | wrong, corrected | 23173 | the club's stadium page "tiene un aforo de 23.173 espectadores". Not taken: 23500 (es.wikipedia infobox, citing that page); 24000 (en.wikipedia infobox); 21332 (StadiumDB); 24891 (Wikidata, which the map held until now). | https://villarrealcf.es/es/estadio-de-la-ceramica/nuestro-hogar/ |
| 92 | US Cremonese | `Q759482` | IT | 15191 | agrees | 15191 | it text "15 191 posti a sedere, suddivisi in 7 settori" and StadiumDB 15191 (= map); en infobox 16,003 is the figure before works (sporteimpianti.it "passando dai 16.003 ai 14.834"); the it infobox displays Wikidata's figure | http://stadiumdb.com/stadiums/ita/stadio_giovanni_zini |
| 93 | C.D. Tenerife | `Q216661` | ES | 21732 | agrees | 21594 | club page "una capacidad actual de 21.594 espectadores", 0.6 percent from the map; es and en infobox 22 824 | https://www.clubdeportivotenerife.es/heliodoro-rodriguez-lopez |
| 94 | SV Ried | `Q457460` | AT | 7680 | wrong, corrected | 7334 | the Austrian Bundesliga's stadium page for the club "Kapazität 7,334"; StadiumDB 7336; de.wikipedia infobox 7.300. Not taken: 7680 (en.wikipedia infobox and Wikidata, which the map held until now). | https://www.bundesliga.at/team/sv-oberbank-ried/6514/stadion |
| 95 | FC St. Gallen | `Q659212` | CH | 19694 | disputed | 19694 to 20660 | de and en infobox 20'660 (international 17'317); StadiumDB 19694 (= map); the stadium's site did not answer and the league site's link list had no page for the club | https://de.wikipedia.org/wiki/Berit_Sitterstadion |
| 96 | SC Kriens | `Q671950` | CH | 5360 | wrong, corrected | 3568 | the Swiss Football League's club page "3568 Capacité du stade", the league figure. Not taken: 5100 (de.wikipedia infobox); 5360 (en.wikipedia infobox, europlan-online and Wikidata, which the map held until now). | https://sfl.ch/teams/sc-kriens |
| 97 | Sint-Truidense V.V. | `Q138248` | BE | 11250 | disputed | 11756 to 12125 | nl and en infobox 11,756 (the club's ticket page, its reference, states no total); StadiumDB 12125; map 11250 below both | https://nl.wikipedia.org/wiki/Stayen_(stadion) |
| 98 | Grasshopper Club Zürich | `Q201360` | CH | 25000 | wrong, corrected | 26114 | the Swiss Football League's page for FC Zürich, same ground, "Stadion Letzigrund ... 26114 Capacité du stade"; the stadium's own facts page "Total : 26'104"; de.wikipedia infobox "26'104 (Super League)"; en.wikipedia infobox "26,105 (football, domestic league)". Not taken: 25000 (StadiumDB and Wikidata, which the map held until now); 24061 (international matches); 30930, 25773 and 50044 (Euro 2008, athletics, concerts). | https://sfl.ch/teams/fc-zurich |
| 99 | FC Zürich | `Q206692` | CH | 25000 | wrong, corrected | 26114 | the Swiss Football League's club page "Stadion Letzigrund ... 26114 Capacité du stade"; the stadium's own facts page "Total : 26'104"; de.wikipedia infobox "26'104 (Super League)"; en.wikipedia infobox "26,105 (football, domestic league)". Not taken: 25000 (StadiumDB and Wikidata, which the map held until now); 24061 (international matches); 30930, 25773 and 50044 (Euro 2008, athletics, concerts). | https://sfl.ch/teams/fc-zurich |
| 100 | Eintracht Braunschweig | `Q154053` | DE | 24406 | wrong, corrected | 23325 | de.wikipedia infobox "23.325 Plätze (Fußball) 24.406 Plätze (maximal)"; en.wikipedia infobox "23,325 (football matches)"; StadiumDB 23325. Not taken: 24406 (the maximum, Wikidata's figure, which the map held until now). | https://de.wikipedia.org/wiki/Eintracht-Stadion |
| 101 | Chelsea F.C. | `Q9616` | GB | 41875 | wrong, corrected | 40044 | en.wikipedia infobox 40,044 and text "With a capacity of 40,044"; StadiumDB's country table 40022, 0.1 percent lower. Not taken: 41875 (Wikidata, which the map held until now). | https://en.wikipedia.org/wiki/Stamford_Bridge_(stadium) |
| 102 | Stade rennais FC | `Q19509` | FR | 31127 | wrong, corrected | 29778 | the club's stadium page "peut accueillir 29 778 supporters"; fr.wikipedia and en.wikipedia infobox 29778; StadiumDB's country table 29778. Not taken: 31127 (Wikidata, which the map held until now). | https://www.staderennais.com/le-roazon-park |
| 103 | SC Heerenveen | `Q200321` | NL | 26100 | agrees | 26100 | club page "De huidige capaciteit is 26.100 zit- en staplaatsen" (= map); nl and en infobox 27,224; StadiumDB 26400 | https://www.sc-heerenveen.nl/club/abe-lenstra-stadion |
| 104 | Neuchâtel Xamax | `Q335195` | CH | 12000 | agrees | 12000 | en infobox and StadiumDB 12000 (= map); league page sfl.ch "11997 Capacité du stade"; de infobox 12'500 | https://sfl.ch/teams/neuchatel-xamax-fcs |
| 105 | Paris FC | `Q1051013` | FR | 20000 | disputed | 19141 to 20000 | the map's ground is Stade Charléty (fr infobox 19151, en 19,142, StadiumDB 19141), but StadiumDB's table lists Paris FC at Stade Jean Bouin with 20 000: which ground the club plays at is a venue question, left for Alexandru | https://fr.wikipedia.org/wiki/Stade_Charl%C3%A9ty |
| 106 | Birmingham City F.C. | `Q19444` | GB | 30016 | cannot verify | 28754 | en infobox 28,754 citing a club page that gave no text; StadiumDB 29409, 2.0 percent from the map | https://en.wikipedia.org/wiki/St_Andrew's_(stadium) |
| 107 | RKC Waalwijk | `Q24699` | NL | 7500 | disputed | 7186 to 7500 | nl and en infobox 7,186; StadiumDB 7500 (= map) | https://nl.wikipedia.org/wiki/Mandemakers_Stadion |
| 108 | PSV Eindhoven | `Q11938` | NL | 36500 | wrong, corrected | 35000 | the club's page "Het Philips Stadion heeft een capaciteit van 35.000 zitplaatsen"; nl.wikipedia infobox 35.000, citing that page. Not taken: 35119 (en.wikipedia infobox and StadiumDB, 0.3 percent higher); 36500 (Wikidata, which the map held until now). | https://www.psv.nl/ticketinfo/stadionplattegrond |
| 109 | Crystal Palace F.C. | `Q19467` | GB | 26255 | wrong, corrected | 25194 | en.wikipedia infobox 25,194, citing a Premier League post that was not opened; StadiumDB's country table 25194. Not taken: 26255 (Wikidata, which the map held until now). | https://en.wikipedia.org/wiki/Selhurst_Park |
| 110 | Willem II | `Q332664` | NL | 14637 | disputed | 14637 to 15220 | nl infobox "15.220 (huidig) 20.000 (maximaal)", en 15,220; StadiumDB 14637 (= map) | https://nl.wikipedia.org/wiki/Koning_Willem_II_Stadion |
| 111 | Fortuna Sittard | `Q854167` | NL | 12500 | wrong, corrected | 12000 | nl.wikipedia and en.wikipedia infobox 12.000; StadiumDB "Capacity 12 000". Not taken: 12500 (Wikidata, which the map held until now). | https://nl.wikipedia.org/wiki/Fortuna_Sittard_Stadion |
| 112 | VfL Wolfsburg | `Q101859` | DE | 30000 | wrong, corrected | 28917 | the club's stadium page "Zuschauerkapazität: 28.917 Plätze, davon 23.568 Sitzplätze und 5.349 variable Stehplätze"; de.wikipedia infobox 28.917, citing that page. Not taken: 30000 (en.wikipedia infobox "League matches", StadiumDB and Wikidata, which the map held until now); 26155 (international matches). | https://www.vfl-wolfsburg.de/stadien/volkswagen-arena/stadioninformationen |
| 113 | AJ Auxerre | `Q182876` | FR | 18541 | disputed | 17897 to 18541 | fr and en infobox 17897, no reference; StadiumDB 18541 (= map) | https://fr.wikipedia.org/wiki/Stade_de_l'Abb%C3%A9-Deschamps |
| 114 | FC Emmen | `Q1061627` | NL | 8600 | disputed | 8301 to 8600 | nl infobox 8.309, StadiumDB 8301; en infobox 8,600 (= map) | https://nl.wikipedia.org/wiki/De_Oude_Meerdijk |
| 115 | FC Vaduz | `Q216773` | CH | 7584 | wrong, corrected | 6814 | the Swiss Football League's club page "Rheinpark ... 6814 Capacité du stade", the league figure. Not taken: 7838 (the Liechtenstein FA's page "Gesamtkapazität 7'838 Plätze" with two stands turned into standing areas, and de.wikipedia infobox); 6127 (covered seats, same page; de.wikipedia "Kapazität international"); 7584 (en.wikipedia infobox and Wikidata, which the map held until now). | https://sfl.ch/teams/fc-vaduz |
| 116 | CD Castellón | `Q743557` | ES | 16000 | disputed | 14485 to 15500 | club page "Skyfi Castalia cuenta con 15.000 localidades"; es and en infobox 15 500 citing it; colgadosporelfutbol.com 15.500; StadiumDB 14485; map 16000 above all | http://www.cdcastellon.com/estadio/ |

## Part B: the Italian clubs against it.wikipedia

All 36 Italian clubs in scope. it.wikipedia's infobox names the field `posti` and displays it as "Posti a sedere".

- **20 of the 36 articles have no `posti` parameter at all: the page displays Wikidata's figure**, which is the map's own (for Fiorentina it displays 43 325, the Wikidata figure the map held before phase 1c). These infoboxes are filled from Wikidata and are **not an independent source**; for these clubs the comparison still rests on en.wikipedia, as in phase 1c.
- **16 articles carry their own figure**: 8 agree with the map within 3 percent on the first number and 8 differ. Read as a whole line, a ninth differs (Padova: "32 420 totali (18 236 omologati)").
- Of the 8 that differ: 3 corrected (Cesena, Atalanta, Empoli), 1 agrees on reading (Modena: the infobox's own reference gives the map's figure), 3 disputed and unchanged (Como, Mantova, Vicenza), 1 cannot verify (Juve Stabia). Padova is disputed and unchanged.
- **Left for Alexandru**: Juve Stabia (13,000 on the map is the full ground; 7,642 approved, on Wikipedia alone) and Padova (32,420 full; 18,236 approved on an undated page). The convention says the league figure is stored, and Pisa was corrected on this shape in phase 1c with a dated press page; here no dated or official page was read, so nothing was written.

| club | Q-id | map | it.wikipedia capacity line | result | article |
|---|---|---|---|---|---|
| Pisa Sporting Club | `Q289613` | 12508 | posti = 12508 omologati | agrees (hand row of phase 1c) | https://it.wikipedia.org/wiki/Stadio_Arena_Garibaldi-Romeo_Anconetani |
| Cesena Football Club | `Q16848949` | 23860 | posti = 20 194 | differs: wrong, corrected to 20194 (Part A) | https://it.wikipedia.org/wiki/Orogel_Stadium-Dino_Manuzzi |
| Ascoli Calcio 1898 FC | `Q6630` | 13708 | (no `posti` parameter; the page displays 13 708, Wikidata's figure) | no figure of its own; corrected to 11326 in Part A from Lega B's article and StadiumDB | https://it.wikipedia.org/wiki/Stadio_Cino_e_Lillo_Del_Duca |
| Atalanta Bergamasca Calcio | `Q1886` | 24950 | posti = 23439 | differs: wrong, corrected to 23439 (Part A) | https://it.wikipedia.org/wiki/Stadio_di_Bergamo |
| US Cremonese | `Q759482` | 15191 | (no `posti` parameter; the page displays 15 191, Wikidata's figure) | no figure of its own; agrees on reading in Part A (it text and StadiumDB 15191) | https://it.wikipedia.org/wiki/Stadio_Giovanni_Zini |
| Como 1907 | `Q1120838` | 13602 | posti = 12370 | differs: disputed, 12039 to 13602 (it infobox and StadiumDB 12370; comozero.it of 21/05/2025, the infobox's reference, "potrà ospitare 12.039 spettatori"; en infobox 13,602 = map); unchanged | https://it.wikipedia.org/wiki/Stadio_Giuseppe_Sinigaglia |
| US Lecce | `Q13391` | 31461 | (no `posti` parameter; the page displays 31 461, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Ettore_Giardiniero |
| FC Südtirol | `Q1387710` | 5500 | posti = 5520 | agrees | https://it.wikipedia.org/wiki/Stadio_Druso |
| Juventus FC | `Q1422` | 41700 | (no `posti` parameter; the page displays 41 700, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Juventus_Stadium |
| UC Sampdoria | `Q1457` | 33205 | (no `posti` parameter; the page displays 33 205, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Luigi_Ferraris |
| AC Milan | `Q1543` | 75817 | (no `posti` parameter; the page displays 75 817, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Giuseppe_Meazza |
| Bologna FC 1909 | `Q1893` | 36462 | posti = 36 532 | agrees | https://it.wikipedia.org/wiki/Stadio_Renato_Dall'Ara |
| Cagliari Calcio | `Q1900` | 16416 | posti = {{m/16416}} | agrees | https://it.wikipedia.org/wiki/Unipol_Domus |
| ACF Fiorentina | `Q2052` | 24786 | (no `posti` parameter; the page displays 43 325, Wikidata's figure) | no figure of its own; the row displays Wikidata's 43 325, the map holds the league's 24786 by the hand row of phase 1c | https://it.wikipedia.org/wiki/Stadio_Artemio_Franchi |
| Genoa CFC | `Q2074` | 33205 | (no `posti` parameter; the page displays 33 205, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Luigi_Ferraris |
| Virtus Entella | `Q2276413` | 5587 | (no `posti` parameter; the page displays 5 587, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Enrico_Sannazzari |
| SS Lazio | `Q2609` | 70634 | (no `posti` parameter; the page displays 70 634, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Olimpico_(Roma) |
| SSC Napoli | `Q2641` | 54726 | (no `posti` parameter; the page displays 54 726, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Diego_Armando_Maradona_(Napoli) |
| Palermo FC | `Q2674` | 36365 | posti = 36215 | agrees | https://it.wikipedia.org/wiki/Stadio_Renzo_Barbera |
| Parma Calcio 1913 | `Q2693` | 22352 | (no `posti` parameter; the page displays 22 352, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Ennio_Tardini |
| AS Roma | `Q2739` | 70634 | (no `posti` parameter; the page displays 70 634, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Olimpico_(Roma) |
| Torino FC | `Q2768` | 28177 | (no `posti` parameter; the page displays 28 177, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Olimpico_Grande_Torino |
| Udinese Calcio | `Q2798` | 25312 | posti = 25 132 | agrees | https://it.wikipedia.org/wiki/Stadio_Friuli |
| AC Monza | `Q289482` | 17102 | (no `posti` parameter; the page displays 17 102, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Brianteo |
| SS Arezzo | `Q297430` | 13128 | posti = 13128 | agrees | https://it.wikipedia.org/wiki/Stadio_Citt%C3%A0_di_Arezzo |
| Mantova 1911 | `Q430993` | 7367 | posti = 11 219 | differs: disputed as in phase 1c, 11219 to 14884 (it 11 219, en 14,884, StadiumDB 12000; club page 404; map 7367 below all); unchanged | https://it.wikipedia.org/wiki/Stadio_Danilo_Martelli |
| US Catanzaro 1929 | `Q501372` | 14650 | (no `posti` parameter; the page displays 14 650, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Nicola_Ceravolo |
| L.R. Vicenza | `Q56542463` | 12163 | posti = 17.163 (12.744 omologati) | differs on the approved figure: disputed, 11640 to 12744 (it "12.744 omologati"; its reference ilgiornaledivicenza.it "La capienza totale del Menti, attualmente, è 11.640 posti"; en 12,000); unchanged | https://it.wikipedia.org/wiki/Stadio_Romeo_Menti |
| FC Inter | `Q631` | 75817 | (no `posti` parameter; the page displays 75 817, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Giuseppe_Meazza |
| Empoli Football Club | `Q6703` | 19847 | posti = 16 284 | differs: wrong, corrected to 16284 (it and en infobox; StadiumDB 16167) | https://it.wikipedia.org/wiki/Stadio_Carlo_Castellani |
| SS Juve Stabia | `Q6748` | 13000 | posti = 7642 | differs: cannot verify (it 7 642, en "13,000 (7,642 approved)", it text "capienza complessiva di posti 12 800"; the club page cited answered 404; map 13000 is the full ground); unchanged, for Alexandru | https://it.wikipedia.org/wiki/Stadio_Romeo_Menti_(Castellammare_di_Stabia) |
| Modena Football Club 2018 | `Q8408` | 21151 | posti = 19 387 | differs, agrees on reading: the infobox's own reference, the club page modenacalcio.com/stadio-a-braglia/, says "CAPIENZA: 21.151 spettatori (a sedere)" (= map), as does StadiumDB; unchanged | https://it.wikipedia.org/wiki/Stadio_Alberto_Braglia |
| Calcio Padova | `Q8428` | 32420 | posti = 32420 totali (18236 omologati) | first number agrees; the line adds "18 236 omologati" and its reference apadova.info (undated) says "ridotta ed ora è di 18.236 spettatori"; StadiumDB 32336: disputed (full ground against an undated approved figure); unchanged, for Alexandru | https://it.wikipedia.org/wiki/Stadio_Euganeo |
| Frosinone Calcio | `Q845043` | 16227 | (no `posti` parameter; the page displays 16 227, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Benito_Stirpe |
| Unione Sportiva Sassuolo Calcio | `Q8603` | 21525 | (no `posti` parameter; the page displays 21 525, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Mapei_Stadium_-_Citt%C3%A0_del_Tricolore |
| H. Verona | `Q8639` | 31045 | (no `posti` parameter; the page displays 31 045, Wikidata's figure) | not independent: no figure of its own (the phase 1c verdict, made on en.wikipedia, stands) | https://it.wikipedia.org/wiki/Stadio_Marcantonio_Bentegodi |

## Part C: the open cases of phase 1c

- **Jong Ajax** (`Q1770361`, map 5000): **left as it is.** The only pages that state 2,250 are again ajaxinside.nl ("Capaciteit 2.250") and the two infoboxes that cite it. The league's site is closed by its terms and no link list names another page, so there are not two independent pages.
- **FC Botoșani** (`Q1262822`): **corrected, 12000 to 7782.** ro.wikipedia ("7.782 de locuri, toate pe scaune"), en.wikipedia ("7,782 seated") and Gazeta Sporturilor, a link of the ro article ("Stadionul are 7.782 de locuri"). StadiumDB's "about 8,500" is not taken; its own page says the 12,000 was the figure before the seats. The league's club page (lpf.ro) gave no figure. This is the one open case decided on a press page and Wikipedia rather than on a club or league page: revert the row if that is not enough.
- **Getafe CF** (`Q8806`, map 16500): disputed, unchanged. The club's page still says "CAPACIDAD: 16.500 espectadores"; es.wikipedia "~10.500 (En reforma)" and StadiumDB 10500; Marca is closed by robots.txt and LaLiga's club page showed no figure.
- **Montpellier HSC** (`Q19513`, map 32900): disputed, unchanged. fr.wikipedia, its reference allezpaillade.com (2017) and StadiumDB say 22,000; en.wikipedia 20,484 citing the club's site, which is closed; no league page with a figure.
- **Almere City** (`Q653119`, map 4501): disputed, unchanged. nl.wikipedia 5.800; the club's own article says the works "binnenkort" raise the capacity "naar 5.800 plaatsen"; Omroep Flevoland says "van 4.158 naar 5.885 plaatsen"; en.wikipedia and StadiumDB 4501. No page states the finished figure.
- **Anagennisi Karditsa** (`Q123283162`, map 13000): disputed, unchanged (el infobox "~5.000", en 3,500; the reference is a PDF, not read).
- **FK Novi Pazar** (`Q995069`, map 12000): disputed, unchanged (en infobox 10,000, StadiumDB 6900; the league's site is closed).
- **Niki Volos** (`Q3180055`, map 2500): unchanged, cannot verify. The el article's text does hold a figure, which phase 1c missed: "χωρητικότητα 2 500 θεατές (σήμερα 1 489 λόγω εργασιών)", so the map's 2,500 is the ground's figure and 1,489 the one during the works. The reference for 1,489 (goalpost.gr) was opened and gave no sentence; the other link is closed. Wikipedia alone.
- **FK Mladost Lučani** (`Q1945740`, map 8000): **agrees.** The sr article's text ("капацитетом од 8 000 места") and the StadiumDB page its link list names ("Capacity 8 000").

## Corrections written in phase 1d (27 rows in `data/clubs-manual.csv`)

25 from Part A, Empoli from Part B, Botoșani from Part C. 24 rows are new; FC Wil, FC Volendam and FC Vaduz already had a row and got the capacity cell, the added sources and an added note. Every note starts "CAPACITY FULL CHECK 2026-11-13" and names what was read and what was not taken.

## Final totals of the capacity check (phases 1c and 1d, 384 clubs)

| verdict | clubs | how |
|---|---|---|
| wrong, corrected | 48 | 21 in phase 1c, 25 in Part A, Empoli, Botoșani |
| disputed, unchanged | 47 | 24 in phase 1c less Botoșani, 21 in Part A, Como, Vicenza, Padova |
| cannot verify | 10 | 7 in phase 1c less Empoli, 2 in Part A, Juve Stabia, Niki Volos |
| agrees | 279 | 262 within 3 percent of Wikipedia's literal figure, 8 on reading in phase 1c, 8 on reading in Part A, Mladost Lučani |
| total | 384 | |

"Agrees" for 262 clubs still means: within 3 percent of the first number of one Wikipedia infobox. It does not say Wikipedia is right; for the 20 Italian clubs above, it means en.wikipedia only.

## Checks (phase 1d)

- `load_manual()` of `tools/fetch_clubs.py` reads the file with 398 rows and its 13 messages are the standing notes on `skip` rows; a dry `apply_manual()` over the 13 club files gives 588 clubs and applies all 27 capacities. `tools/test_propose_country.py` passes.
- The club files are regenerated by `build-clubs.yml` on `main` after the merge. No `SHELL_VERSION` change.
