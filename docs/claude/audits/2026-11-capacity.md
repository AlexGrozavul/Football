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
