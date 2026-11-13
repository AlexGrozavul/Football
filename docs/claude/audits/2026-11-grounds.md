# Club fact check, phase 1e: ground and coordinates of the clubs of tier 3 and lower (2026-11-13)

Pull request #214. Everything below was read on 2026-11-13 through a temporary probe workflow on a GitHub runner (4 runs of the 8 allowed; run ids 43463934819, 43478459132, 43513100724, 43514311910). The workflow and its script were removed before the merge.

## Step 0

- "Build club layer" run 43449217819 (commit `012d233`, PR #213): **success**.
- The 27 capacity rows PR #213 added to `data/clubs-manual.csv` were compared with `data/clubs/*.json` on `main`: **27 of 27 present, none missing**.

## Scope

Every club on the map at tier 3 or lower: **136 clubs**.

| league | clubs |
|---|---|
| 3. Liga (DE, tier 3) | 20 |
| Regionalliga, five divisions (DE, tier 4): Bayern 13, Nord 5, Nordost 13, Südwest 12, West 11, the generic item 2, hand rows without a division 30 | 86 |
| VfR Garching (DE, hand row at tier 7) | 1 |
| Liga a III-a (RO, tier 3) | 29 |

## Method

- **Grounds.** The 2026/27 season article of each league, the country's wiki first and English second, read through the MediaWiki API (`action=parse`, `maxlag=5`, one request a second; no lag refusal occurred). The grounds table of each article was parsed and each row joined to a map club by the Wikidata item of the club link, or by the club's name where the row has no link. A club in no grounds table was looked for in the league tables of the same articles.
- **Whether a table is filled from Wikidata.** The wikitext of all eleven articles was searched for Wikidata calls (`#property`, `#statements`, `#invoke:Wikidata`, `{{Wikidata}}`): **none in any of them**. The grounds tables are hand-written wikitext, so they are independent of the Wikidata values the map holds. Wikipedia in all languages still counts as one source.
- **Coordinates.** One Overpass query per club (named `leisure=stadium` or `leisure=pitch`, or a building or leisure object with the ground's name, within 3 km of the map point), then one Nominatim search where Overpass found nothing. Distance is from the map point to the centre of the OpenStreetMap object.
- **Corrections** rest on a page or an API response opened that day. A "differs" was resolved with the club's own page or a source cited in the article.

### Limits, stated plainly

- **Overpass answered only in run 1.** `overpass-api.de` returned HTTP 502/504 or timed out for most requests: run 1 got answers for 52 clubs in 83 minutes, run 2 two answers out of 50 requests, run 3 none out of 8. Overpass answered for 53 clubs in all (45 found by name within 500 m, 8 not found by name). **The other 83 clubs got no Overpass answer and were checked through Nominatim alone**, as were the 8: a name search bounded to a box of about 3 km around the map point, and in run 3, for the clubs still open, a reverse lookup of the map point and a listing of the stadiums Nominatim knows in the same box. This is a deviation from the planned method (Overpass first), forced by the server. Nominatim only matches whole words of a name, so it finds fewer spelling variants than the Overpass name comparison would have.
- ro.wikipedia has **no 2026-27 Liga III article** (the title redirects to the general "Liga a III-a" article) and the English one has league tables but **no grounds table**. The 29 Romanian clubs could not be compared on ground at all.
- en.wikipedia "2026–27 Regionalliga" has no grounds table either; the Regionalliga comparison rests on the five de.wikipedia division articles.
- Closed hosts were not read (the hosts listed as closed in `conventions.md` and `open-problems.md`, eredivisie.nl, keukenkampioendivisie.nl). kicker.de answered HTTP 403 to the root page and was not read.

## Part A: grounds

Articles read: de "3. Fußball-Liga 2026/27" (grounds table, 20 rows), de "Fußball-Regionalliga 2026/27" (no table; it links the five division articles), de "Fußball-Regionalliga Bayern / Nord / Nordost / Südwest / West 2026/27" (grounds tables of 20, 20, 18, 19 and 19 rows), en "2026–27 3. Liga" (grounds table, 20 rows), en "2026–27 Regionalliga" (no grounds table), ro "Liga a III-a" (no season article), en "2026–27 Liga III" (no grounds table).

### Comparison counts (136 clubs)

| result | clubs |
|---|---|
| agrees (same ground, spelling or sponsor name aside), mechanically | 90 |
| differs, mechanically | 12 |
| club in the league but not in the grounds table | 0 |
| no grounds table for the league | 28 (27 Liga III clubs found in the English league tables, and Știința Poli Timișoara II, which is there as "Politehnica Timișoara II") |
| club not listed in its league at all | 6 (the six clubs of Part C, see below) |

Two rows needed a second look before they could be counted: Hannoverscher SC is in the Nord table as "HSC Hannover" with the map's ground (agrees), and Știința Poli Timișoara II is in the English Liga III table as "Politehnica Timișoara II" (in the league; `roster-links-manual.csv` already records this).

### The 12 that differ, resolved

| club | Q-id | map ground | table ground | verdict | evidence |
|---|---|---|---|---|---|
| Würzburger Kickers | `Q535785` | Flyeralarm Arena | Akon Arena | **agrees** (renamed) | de.wikipedia "Flyeralarm Arena" redirects to "Akon Arena" (`Q1716424`); OSM way/663167079 "AKON ARENA" is 7 m from the map point |
| SC Verl | `Q666010` | Stadion an der Poststraße | Sportclub Arena | **agrees** (renamed) | de.wikipedia redirect to "Sportclub Arena" (`Q1408225`); OSM way/35710101 "Sportclub Arena", 76 m |
| FSV Frankfurt | `Q157352` | PSD Bank Arena | BBBank Arena | **agrees** (renamed) | de.wikipedia redirect to "BBBank Arena" (`Q319774`); OSM way/663164612 "BBBank Arena", 11 m |
| Kickers Offenbach | `Q159936` | Sparda-Bank-Hessen-Stadion | Stadion am Bieberer Berg | **agrees** (renamed) | de.wikipedia redirect to "Stadion am Bieberer Berg" (`Q368642`); OSM way/26656405 "PLUTOS Stadion am Bieberer Berg", 25 m |
| FSV Zwickau | `Q316896` | Stadion Zwickau | GGZ-Arena | **agrees** (renamed) | de.wikipedia redirect to "GGZ-Arena" (`Q26791679`); OSM way/1177356445 "GGZ-Arena", 3 m |
| VfR Aalen | `Q692586` | Centus Arena | Bediani-Arena | **agrees** (renamed) | de.wikipedia redirect to "Bediani-Arena" (`Q872808`); OSM way/164637880 "Bediani-Arena", 10 m |
| SpVgg Unterhaching | `Q158121` | Sportpark Unterhaching | Uhlsport Park | **agrees** (renamed) | the table's link target is the article "Sportpark Unterhaching"; OSM way/181862852 "uhlsport Park", 28 m |
| SV Bergisch Gladbach 09 | `Q493464` | BELKAW-Arena | Stadion An der Paffrather Straße | **agrees** (same ground) | the table's link target is the article "BELKAW-Arena" |
| FC Memmingen | `Q566136` | Memminger Arena | e-con ArenaPark | **agrees** (renamed) | the table's link target is the article "Memminger Arena" |
| TSV Steinbach Haiger | `Q16743331` | SIBRE-Sportzentrum Haarwasen | Sportzentrum Haarwasen Haiger | **agrees** (sponsor prefix) | OSM way/750296487 "Sibre Sportzentrum", 16 m (Overpass, run 1) |
| **Hamburger SV II** | `Q5644342` | Sportpark Eimsbüttel | Stadion Hoheluft | **wrong, corrected** | the club's own page https://www.hsv.de/teams/nachwuchs/spielorte-tickets : "Während die U21 ihre Heimspiele im Stadion Hoheluft austrägt" and "Stadion Hoheluft, Lokstedter Steindamm 87, 22529 Hamburg, U21, 4.680 Plätze"; ground, position (OSM way/23815941, 1,691 m from the old point) and capacity (4,680, was 2,400 for the other ground) written |
| **TSV Havelse** | `Q537301` | Wilhelm-Langrehr-Stadion | 3× Eilenriedestadion, 4× Heinz-von-Heiden-Arena (both Hannover) | **disputed, not corrected** | see below |

The map keeps the older sponsor names of the ten renamed grounds; the names were not changed (the task counts a sponsor name as agreement).

**TSV Havelse, for Alexandru.** The map's Wilhelm-Langrehr-Stadion is not where the 3. Liga matches are played: the table's footnote says it does not meet the DFB's requirements, and the DFB's own page of 12 October 2026 (https://www.dfb.de/news/eilenriedestadion-als-weitere-heimspielstaette-des-tsv-havelse-zugelassen) says the club's licence for 2026/27 was granted "auf Basis der Heinz von Heiden Arena als Heimspielstätte" and that the Eilenriedestadion is now approved "als weitere Heimspielstätte". So there are **two approved home grounds**, and the sources name different ones as the ground: the DFB's licence the Heinz-von-Heiden-Arena, de.wikipedia's club infobox the Eilenriedestadion; the season table counts 4 and 3 matches. The club's own site was read and names neither. Which one the map should show is his decision; nothing was written. Positions if he decides: Heinz-von-Heiden-Arena OSM way/9923195 (52.360026, 9.731016), Eilenriedestadion OSM way/179158024 (52.376639, 9.772730). The existing point is 65 m from an OSM node named "Wilhelm-Langrehr-Stadion", so it is right for the ground it names.

Totals for the 12: **10 agree on reading, 1 corrected, 1 disputed, 0 cannot verify.**

### Clubs the season article no longer lists in their league

Six, and they are exactly the six of Part C: **TuS Koblenz, SV Heimstetten, VFC Plauen, TSG Neustrelitz, VfR Garching** (in no league table and no grounds table of the 3. Liga and Regionalliga articles; Koblenz appears only in a navigation box) and **Dacia Unirea Brăila** (in no league table of en "2026–27 Liga III"). They were skipped in this session only because the coordinator's decision of 13 November covers them (Part C). **No other club of the scope is missing from its league.**

## Part B: coordinates

### Comparison counts (136 clubs)

| result | clubs |
|---|---|
| ground found by name within 500 m of the map point (agrees) | 117 (45 through Overpass, 72 through Nominatim) |
| ground found by name 500 m to 3 km away (differs) | 0 |
| ground not found by name | 19 |

The largest distance among the 117 is 164 m (BSG Chemie Leipzig, Alfred-Kunze-Sportpark, way/20313355).

### The 19 not found by name

For 15 of them the map point lies on a pitch or stadium that OpenStreetMap either does not name or names differently, so the position is plausible but the name could not be matched. **None was changed.**

| club | Q-id | map ground | what OpenStreetMap has at the map point |
|---|---|---|---|
| FSV Schöningen | `Q112633360` | Elm-Stadion | point on an unnamed pitch, way/37295887, 13 m |
| VfR Garching | `Q127275134` | Sportplatz Schleißheimer Straße | nothing by name (run 1 Overpass: 9 named objects in 3 km, none matching); skipped in Part C |
| TSV Aubstadt | `Q1507157` | NGN-Arena | point on an unnamed pitch, way/103891118, 0 m |
| Hannoverscher SC | `Q1576328` | HSC-Stadion Constantinstraße | point on an unnamed pitch, way/97240443, 25 m |
| Kickers Emden | `Q319167` | Ostfriesland-Stadion | point on an unnamed pitch, way/47860452, 10 m |
| SV Heimstetten | `Q324983` | Stadion im ATS-Sportpark | nothing by name (run 2 Overpass: 10 named objects in 3 km, none matching); skipped in Part C |
| SV Bergisch Gladbach 09 | `Q493464` | BELKAW-Arena | point on an unnamed pitch, way/1021775151, 5 m; a bus stop named "BELKAW arena" (node/5172272072) is 117 m away |
| FC Memmingen | `Q566136` | Memminger Arena | an unnamed stadium polygon, way/34395431, 47 m |
| TSV Buchbach | `Q566183` | SMR-Arena | point on an unnamed pitch, way/391060003, 7 m |
| SC Eltersdorf | `Q821096` | Sportanlage Langenau | nothing named and no pitch at the point (nearest object: a restaurant, 33 m) |
| SC Weiche Flensburg 08 | `Q831867` | Manfred-Werner-Stadion | point on an unnamed pitch, way/159639086, 5 m |
| CSM Pașcani | `Q1024393` | Stadionul CFR Pașcani | a stadium named "Stadionul municipal Pașcani", way/705395339, 11 m (the map says Stadionul CFR Pașcani) |
| Oltul Curtișoara | `Q130199486` | Stadionul Tineretului | point on an unnamed pitch, way/659012696, 0 m |
| Sănătatea Cluj | `Q1463313` | Stadionul Clujana | point on an unnamed pitch, way/283751546, 40 m |
| Aerostar Bacău | `Q5014447` | Stadionul Aerostar | point on an unnamed pitch, way/174871603, 2 m |
| CS Inter Ilfov | `Q5014453` | Stadionul Orășenesc (Buftea) | a pitch named "Stadionul Constantin Bălălău", way/407006284, 24 m (the map says Stadionul Orășenesc) |
| CSO Tricolorul Breaza | `Q5014496` | Stadionul Parc | an unnamed stadium polygon, way/16943595, 15 m |
| ACS Înainte Modelu | `Q55864953` | Stadionul Vasile Enache | point on an unnamed pitch, way/1179867606, 4 m |
| FC Unirea Dej | `Q966392` | Stadionul Municipal Dej | THE MAP POINT IS WRONG: it lies on the pitch "Stadionul Berceni", way/25240552, 362.5 km from Dej |

**FC Unirea Dej, for Alexandru: the map point is wrong and was NOT corrected.** The map says "Stadionul Municipal Dej" but its point (44.308611, 26.183889) is the pitch "Stadionul Berceni" in Berceni, Ilfov (OSM way/25240552, which carries the Wikidata tag `Q7596366`), 362.5 km from Dej. ro.wikipedia's club article says the home ground is "Stadionul Municipal Dej" in Dej, the English one "Stadionul Unirea (Dej)". Nominatim knows exactly one stadium in a box of about 3 km around Dej: OSM way/271928305 (`leisure=stadium`, `sport=soccer`, **no name**, Strada Aurora, Dealul Florilor, Dej; 47.1308716, 23.8903761). Because the object has no name, the match is by elimination and not by name; the task says to leave a doubtful match and list it. If he accepts it, the row is `Q966392` with that position and source https://www.openstreetmap.org/way/271928305 .

**Two ground names OpenStreetMap disagrees with** (no season table exists to compare them, nothing changed): CSM Pașcani (map "Stadionul CFR Pașcani"; OSM "Stadionul municipal Pașcani") and CS Inter Ilfov (map "Stadionul Orășenesc (Buftea)"; OSM "Stadionul Constantin Bălălău").

### Positions corrected

| club | Q-id | reason | new position | OSM element |
|---|---|---|---|---|
| Hamburger SV II | `Q5644342` | ground changed in Part A | 53.587215, 9.969698 | way/23815941 "Stadion Hoheluft" |
| Paris FC (Part C, tier 1) | `Q1051013` | ground changed in Part C | 48.843319, 2.252962 | way/403524549 "Stade Jean-Bouin" |

No club was in the 500 m to 3 km band, so no position was corrected for distance alone.

### Every club: ground and coordinate result

Ground: `=` agrees mechanically, `≈` agrees on reading (see the table above), `≠` differs, `–` no grounds table, `x` not in the league. Coordinate: OSM element, how it was found (O Overpass, N Nominatim), distance in metres; `nf` not found by name.

| club | Q-id | league | map ground | ground | coordinate |
|---|---|---|---|---|---|
| 1. FC Saarbrücken | `Q157463` | 3. Liga | Ludwigsparkstadion | = | way/1177001117 O 74 |
| Alemannia Aachen | `Q153535` | 3. Liga | Tivoli | = | relation/1755976 O 24 |
| FC Ingolstadt 04 | `Q170117` | 3. Liga | Audi-Sportpark | = | way/67237986 O 38 |
| FC Viktoria Köln | `Q695008` | 3. Liga | Sportpark Höhenberg | = | way/26490834 N 12 |
| Fortuna Düsseldorf | `Q151747` | 3. Liga | Merkur Spiel-Arena | = | way/24547706 O 11 |
| Hansa Rostock | `Q142005` | 3. Liga | Ostseestadion | = | way/33781737 O 6 |
| MSV Duisburg | `Q154293` | 3. Liga | Schauinsland-Reisen-Arena | = | way/1576428128 O 3 |
| Preußen Münster | `Q316865` | 3. Liga | Preußenstadion | = | relation/1360363 N 10 |
| Rot-Weiss Essen | `Q155218` | 3. Liga | Stadion an der Hafenstraße | = | way/610528384 O 28 |
| SC Fortuna Köln | `Q310608` | 3. Liga | Südstadion | = | way/27816189 O 6 |
| SC Verl | `Q666010` | 3. Liga | Stadion an der Poststraße | ≈ | way/35710101 N 76 |
| SG Sonnenhof Großaspach | `Q692755` | 3. Liga | WIRmachenDRUCK Arena | = | way/372567612 N 24 |
| SSV Jahn Regensburg | `Q265570` | 3. Liga | Jahnstadion Regensburg | = | way/365735150 O 34 |
| SV Meppen | `Q819400` | 3. Liga | Hänsch-Arena | = | way/196582775 N 12 |
| SV Waldhof Mannheim | `Q170134` | 3. Liga | Carl-Benz-Stadion | = | way/181915119 O 6 |
| SV Wehen Wiesbaden | `Q310621` | 3. Liga | Brita-Arena | = | way/201467283 O 17 |
| TSG 1899 Hoffenheim II | `Q16637410` | 3. Liga | Dietmar-Hopp-Stadion | = | way/28482163 O 4 |
| TSV Havelse | `Q537301` | 3. Liga | Wilhelm-Langrehr-Stadion | ≠ | node/1448681252 N 65 |
| VfB Stuttgart II | `Q107421` | 3. Liga | WIRmachenDRUCK Arena | = | way/372567612 O 8 |
| Würzburger Kickers | `Q535785` | 3. Liga | Flyeralarm Arena | ≈ | way/663167079 N 7 |
| 1. FC Bocholt | `Q162213` | Regionalliga (hand row) | Stadion am Hünting | = | way/104981785 O 0 |
| 1. FC Phönix Lübeck | `Q162366` | Regionalliga (hand row) | Buniamshof | = | way/151836165 O 22 |
| 1. FC Schweinfurt 05 | `Q162394` | Regionalliga (hand row) | Sachs-Stadion | = | way/23646182 O 59 |
| 1. FSV Mainz 05 II | `Q16525419` | Regionalliga (hand row) | Bruchwegstadion | = | way/1374173989 O 3 |
| BFC Preussen | `Q666155` | Regionalliga (hand row) | Preussenstadion | = | relation/20335480 N 0 |
| Bremer SV | `Q479276` | Regionalliga (hand row) | Stadion am Panzenberg | = | way/231977701 N 0 |
| Eimsbütteler TV | `Q468738` | Regionalliga (hand row) | Sportpark Hinschenfelde | = | relation/1106317 N 0 |
| FC Astoria Walldorf | `Q325270` | Regionalliga (hand row) | Stadion im Dietmar-Hopp-Sportpark | = | way/159034730 N 0 |
| FC Eintracht Norderstedt 03 | `Q831602` | Regionalliga (hand row) | Edmund-Plambeck-Stadion | = | way/26790284 N 0 |
| FC Gütersloh 2000 | `Q694464` | Regionalliga (hand row) | Heidewaldstadion | = | way/26927517 N 0 |
| FSV 63 Luckenwalde | `Q479371` | Regionalliga (hand row) | Werner-Seelenbinder-Stadion | = | way/51780507 N 0 |
| FSV Schöningen | `Q112633360` | Regionalliga (hand row) | Elm-Stadion | = | nf |
| Greifswalder FC | `Q55364716` | Regionalliga (hand row) | Volksstadion Greifswald | = | way/65043195 N 0 |
| Hallescher FC | `Q316855` | Regionalliga (hand row) | Leuna-Chemie-Stadion | = | way/130575966 N 15 |
| Hannoverscher SC | `Q1576328` | Regionalliga (hand row) | HSC-Stadion Constantinstraße | = | nf |
| SC Freiburg II | `Q20631356` | Regionalliga (hand row) | Dreisamstadion | = | relation/1614762 O 7 |
| SG Wattenscheid 09 | `Q524378` | Regionalliga (hand row) | Lohrheidestadion | = | way/663054792 N 0 |
| SGV Freiberg | `Q885184` | Regionalliga (hand row) | Kleiner Arena | = | way/25015055 N 0 |
| SSV Ulm 1846 | `Q14551982` | Regionalliga (hand row) | Donaustadion | = | way/614515727 O 11 |
| SV Atlas Delmenhorst | `Q30090061` | Regionalliga (hand row) | Stadion an der Düsternortstraße | = | way/232692520 N 7 |
| SV Drochtersen/Assel | `Q1425370` | Regionalliga (hand row) | Kehdinger Stadion | = | way/667512316 O 52 |
| SV Todesfelde | `Q1585026` | Regionalliga (hand row) | Joda Sportpark | = | way/753432639 O 11 |
| SpVgg Ansbach | `Q885187` | Regionalliga (hand row) | Xaver-Bertsch-Sportpark | = | way/156675035 N 24 |
| SpVgg Bayreuth | `Q526949` | Regionalliga (hand row) | Hans-Walter-Wild-Stadion | = | way/439206373 N 0 |
| TSV Aubstadt | `Q1507157` | Regionalliga (hand row) | NGN-Arena | = | nf |
| TSV Schwaben Augsburg | `Q529579` | Regionalliga (hand row) | Rosenaustadion | = | way/26039742 N 0 |
| VfB Lübeck | `Q665920` | Regionalliga (hand row) | Stadion an der Lohmühle | = | way/656606219 N 3 |
| VfR Mannheim | `Q666179` | Regionalliga (hand row) | Rhein-Neckar-Stadion | = | way/439077870 N 0 |
| Wacker Burghausen | `Q161034` | Regionalliga (hand row) | Wacker-Arena | = | way/26954909 O 5 |
| Werder Bremen II | `Q4107588` | Regionalliga (hand row) | Weserstadion Platz 11 | = | way/232421157 N 22 |
| VfB Oldenburg | `Q826212` | Regionalliga (the generic fourth-division item) | Marschweg-Stadion | = | relation/2903130 N 80 |
| VfL Bochum II | `Q7924284` | Regionalliga (the generic fourth-division item) | Mondpalast-Arena | = | way/87347983 N 0 |
| 1. FC Nürnberg II | `Q4545849` | Regionalliga Bayern | Max-Morlock-Platz Valznerweiher | = | way/47073829 N 5 |
| DJK Vilzing | `Q17321080` | Regionalliga Bayern | Manfred Zollner Stadion | = | node/13043406139 O 0 |
| FC Augsburg II | `Q5424829` | Regionalliga Bayern | Rosenaustadion | = | way/26039742 N 20 |
| FC Bayern München II | `Q994701` | Regionalliga Bayern | Städtisches Stadion an der Grünwalder Straße | = | way/23463412 N 19 |
| FC Memmingen | `Q566136` | Regionalliga Bayern | Memminger Arena | ≈ | nf |
| FV Illertissen | `Q479321` | Regionalliga Bayern | Vöhlinstadion | = | way/1301973503 N 7 |
| SC Eltersdorf | `Q821096` | Regionalliga Bayern | Sportanlage Langenau | = | nf |
| SV Heimstetten | `Q324983` | Regionalliga Bayern | Stadion im ATS-Sportpark | x | nf |
| SpVgg Greuther Fürth II | `Q7572134` | Regionalliga Bayern | Konrad-Ammon-Platz im Sportzentrum | = | way/147177507 N 0 |
| SpVgg Unterhaching | `Q158121` | Regionalliga Bayern | Sportpark Unterhaching | ≈ | way/181862852 O 33 |
| TSV 1860 München | `Q131603` | Regionalliga Bayern | Städtisches Stadion an der Grünwalder Straße | = | way/23463412 O 17 |
| TSV Buchbach | `Q566183` | Regionalliga Bayern | SMR-Arena | = | nf |
| VfB Eichstätt | `Q2521441` | Regionalliga Bayern | HIRSCH Sportpark | = | way/652930200 O 6 |
| Hamburger SV II | `Q5644342` | Regionalliga Nord | Sportpark Eimsbüttel | ≠ | way/75900927 N 6 |
| Hannover 96 II | `Q16573990` | Regionalliga Nord | Eilenriedestadion | = | way/179158024 O 10 |
| Kickers Emden | `Q319167` | Regionalliga Nord | Ostfriesland-Stadion | = | nf |
| SC Weiche Flensburg 08 | `Q831867` | Regionalliga Nord | Manfred-Werner-Stadion | = | nf |
| SSV Jeddeloh | `Q2207914` | Regionalliga Nord | Haskamp Arena | = | way/1121559196 O 0 |
| 1. FC Lokomotive Leipzig | `Q162317` | Regionalliga Nordost | Bruno-Plache-Stadion | = | way/32995500 O 6 |
| BFC Dynamo | `Q159930` | Regionalliga Nordost | Stadion im Sportforum | = | way/43942433 O 63 |
| BSG Chemie Leipzig | `Q1921747` | Regionalliga Nordost | Alfred-Kunze-Sportpark | = | way/20313355 O 164 |
| Chemnitzer FC | `Q161554` | Regionalliga Nordost | Stadion an der Gellertstraße | = | way/653342937 O 20 |
| FC Carl Zeiss Jena | `Q155186` | Regionalliga Nordost | Ernst-Abbe-Sportfeld | = | relation/18457347 O 96 |
| FC Erzgebirge Aue | `Q97927365` | Regionalliga Nordost | eins Erzgebirgsstadion | = | way/440664813 N 20 |
| FC Rot-Weiß Erfurt | `Q170107` | Regionalliga Nordost | Steigerwaldstadion | = | way/37437787 N 14 |
| FSV Zwickau | `Q316896` | Regionalliga Nordost | Stadion Zwickau | ≈ | way/1177356445 N 3 |
| Hertha BSC II | `Q920263` | Regionalliga Nordost | Stadion auf dem Wurfplatz | = | way/24296069 N 6 |
| SV Babelsberg 03 | `Q97927380` | Regionalliga Nordost | Karl-Liebknecht-Stadion | = | relation/20424231 N 7 |
| SV Tasmania Berlin | `Q1565781` | Regionalliga Nordost | Werner-Seelenbinder-Sportpark | = | way/18942529 O 147 |
| TSG Neustrelitz | `Q176168` | Regionalliga Nordost | Parkstadion | x | way/158277880 O 0 |
| VFC Plauen | `Q700029` | Regionalliga Nordost | Vogtlandstadion | x | way/105445412 N 7 |
| 1. FC Kaiserslautern II | `Q16525407` | Regionalliga Suedwest | Fritz-Walter-Stadion | = | way/27880400 O 55 |
| Eintracht Trier | `Q647893` | Regionalliga Suedwest | Moselstadion | = | node/267551453 N 29 |
| FC 08 Homburg | `Q137499` | Regionalliga Suedwest | Waldstadion Homburg | = | way/438209778 O 9 |
| FSV Frankfurt | `Q157352` | Regionalliga Suedwest | PSD Bank Arena | ≈ | way/663164612 N 11 |
| KSV Hessen Kassel | `Q819354` | Regionalliga Suedwest | Auestadion | = | relation/14312319 N 81 |
| Kickers Offenbach | `Q159936` | Regionalliga Suedwest | Sparda-Bank-Hessen-Stadion | ≈ | way/26656405 O 27 |
| SG Barockstadt Fulda-Lehnerz | `Q15849956` | Regionalliga Suedwest | Stadion der Stadt Fulda im Sportpark Johannisau | = | way/24929913 O 5 |
| SV Sandhausen | `Q639525` | Regionalliga Suedwest | Hardtwaldstadion | = | way/223139712 N 3 |
| Stuttgarter Kickers | `Q170105` | Regionalliga Suedwest | Waldau-Stadion | = | way/14169211 O 2 |
| TSV Steinbach Haiger | `Q16743331` | Regionalliga Suedwest | SIBRE-Sportzentrum Haarwasen | ≈ | way/750296487 O 16 |
| TuS Koblenz | `Q155452` | Regionalliga Suedwest | Stadion Oberwerth | x | way/108260419 O 2 |
| VfR Aalen | `Q692586` | Regionalliga Suedwest | Centus Arena | ≈ | way/164637880 N 10 |
| 1. FC Köln II | `Q15972883` | Regionalliga West | Franz-Kremer-Stadion | = | way/49930449 O 1 |
| Bonner SC | `Q568276` | Regionalliga West | Sportpark Nord | = | way/5107070 N 28 |
| Borussia Dortmund II | `Q865720` | Regionalliga West | Stadion Rote Erde | = | way/17236684 N 48 |
| Borussia Mönchengladbach II | `Q13397712` | Regionalliga West | Grenzlandstadion | = | way/23918986 N 18 |
| FC Schalke 04 II | `Q3736767` | Regionalliga West | Parkstadion | = | way/770742075 N 4 |
| Rot-Weiß Oberhausen | `Q157020` | Regionalliga West | Stadion Niederrhein | = | way/24004753 O 17 |
| SC Wiedenbrück | `Q479269` | Regionalliga West | Jahnstadion | = | way/34088864 N 37 |
| SV Bergisch Gladbach 09 | `Q493464` | Regionalliga West | BELKAW-Arena | ≈ | nf |
| SV Rödinghausen | `Q15843660` | Regionalliga West | Häcker-Wiehenstadion | = | way/909365791 O 0 |
| Sportfreunde Lotte | `Q666067` | Regionalliga West | Stadion am Lotter Kreuz | = | way/560328555 N 14 |
| Sportfreunde Siegen | `Q609926` | Regionalliga West | Leimbachstadion | = | relation/2020695 N 52 |
| VfR Garching | `Q127275134` | tier 7 (hand row) | Sportplatz Schleißheimer Straße | x | nf |
| ACS ARO Muscelul Câmpulung | `Q7579573` | Liga a III-a | Stadionul Muscelul | – | way/304104666 N 0 |
| ACS Mediaș 2022 | `Q113331350` | Liga a III-a | Stadionul Gaz Metan | – | way/105611613 N 26 |
| ACS Înainte Modelu | `Q55864953` | Liga a III-a | Stadionul Vasile Enache | – | nf |
| ASC Corona Brașov | `Q4654138` | Liga a III-a | Stadionul Carpați | – | way/222122337 N 31 |
| Aerostar Bacău | `Q5014447` | Liga a III-a | Stadionul Aerostar | – | nf |
| CS Inter Ilfov | `Q5014453` | Liga a III-a | Stadionul Orășenesc (Buftea) | – | nf |
| CS Minerul Lupeni | `Q1575208` | Liga a III-a | Stadionul Minerul | – | way/323360774 N 16 |
| CSM Deva | `Q19902101` | Liga a III-a | Stadionul Cetate (Deva) | – | relation/87536 N 69 |
| CSM Pașcani | `Q1024393` | Liga a III-a | Stadionul CFR Pașcani | – | nf |
| CSM Râmnicu Sărat | `Q5014181` | Liga a III-a | Stadionul Municipal (Râmnicu Sărat) | – | way/96851733 N 23 |
| CSM Târgu Jiu | `Q130302376` | Liga a III-a | Stadionul Constantina Diță | – | relation/9897863 N 46 |
| CSM Vaslui | `Q118904605` | Liga a III-a | Stadionul Municipal Vaslui | – | way/256557708 N 10 |
| CSO Băicoi | `Q120784310` | Liga a III-a | Stadionul Petrolul | – | way/14357372 N 27 |
| CSO Tricolorul Breaza | `Q5014496` | Liga a III-a | Stadionul Parc | – | nf |
| Ceahlăul Piatra Neamț | `Q924296` | Liga a III-a | Stadionul Ceahlăul | – | way/611987458 N 9 |
| Dacia Unirea Brăila | `Q639046` | Liga a III-a | Stadionul Municipal | x | way/23838399 N 20 |
| Dunărea Călărași | `Q4680389` | Liga a III-a | Stadionul Ion Comșa | – | way/162470599 N 3 |
| FC Inter Sibiu | `Q533005` | Liga a III-a | Stadionul Municipal Sibiu | – | way/1123069978 N 34 |
| FC Unirea Dej | `Q966392` | Liga a III-a | Stadionul Municipal Dej | – | nf |
| Flacăra Moreni | `Q1426344` | Liga a III-a | Stadionul Flacăra | – | way/15561947 N 26 |
| Jiul Petroșani | `Q1689705` | Liga a III-a | Stadionul Petre Libardi | – | way/793812576 N 19 |
| KSE Târgu Secuiesc | `Q55583717` | Liga a III-a | Stadionul Dr. Sinkovits | – | way/157916749 N 10 |
| Minaur Baia Mare | `Q135627364` | Liga a III-a | Stadionul Viorel Mateianu | – | relation/3363818 N 79 |
| Oltul Curtișoara | `Q130199486` | Liga a III-a | Stadionul Tineretului | – | nf |
| Progresul Spartac | `Q55585581` | Liga a III-a | Stadionul Progresul Spartac | – | way/740122352 N 12 |
| SCM Zalău | `Q66424146` | Liga a III-a | Stadionul Municipal (Zalău) | – | way/172811034 N 4 |
| Sănătatea Cluj | `Q1463313` | Liga a III-a | Stadionul Clujana | – | nf |
| Unirea Alba Iulia | `Q512961` | Liga a III-a | Stadionul Cetate | – | way/217958154 N 13 |
| Știința Poli Timișoara II | `Q5425107` | Liga a III-a | Stadionul Știința | – | way/154295262 N 7 |

## Part C: small leftovers

### 1. The six clubs kept at a wrong tier in phase 1b

Skipped the way phase 1b skipped its clubs, on the coordinator's decision of 13 November 2026. Each `skip` row in `data/clubs-manual.csv` says where phase 1b found the club and what was read again today.

| club | Q-id | was | rows changed |
|---|---|---|---|
| TuS Koblenz | `Q155452` | tier 4 | new skip row; its 4 own rivalry rows deleted |
| SV Heimstetten | `Q324983` | tier 4 | hand row set to skip; its own rivalry row deleted |
| VFC Plauen | `Q700029` | tier 4 | new skip row; its own rivalry row deleted |
| TSG Neustrelitz | `Q176168` | tier 4 | hand row set to skip; its own rivalry row deleted |
| Dacia Unirea Brăila | `Q639046` | tier 3 | new skip row; its own rivalry row deleted; its id blanked in Oțelul Galați's rivalry row (the name stays); "Lower Danube derby" in `derbies.csv` marked `offMap` |
| VfR Garching | `Q127275134` | tier 7 | hand row set to skip; its own rivalry row deleted (rival SpVgg Unterhaching) |

9 rivalry rows deleted, 1 id blanked, 1 derby marked. No row of `club-parents.csv`, `club-friendships.csv`, the ticket files, `football-rules.json` or `attended.json` names any of the six. The culture sources the deleted rows used (C500, C509, C532, C574, C621) stay in `club-culture-sources.csv` and are now reported as unused by the checker, a warning. The map goes from 588 to 582 clubs when the club layer is rebuilt.

### 2. Capacity leftovers of phase 1d

| club | Q-id | result | evidence |
|---|---|---|---|
| PEC Zwolle | `Q269151` | **corrected: 14,000** (was 12,500) | the club's own page https://www.peczwolle.nl/over-het-mac3park-stadion/ : "biedt na de uitbouw in de zomer van 2018 plaats aan 14.000 toeschouwers"; stadiums tables of en "2026–27 Eredivisie" (14,000) and nl "Eredivisie 2026/27 (mannenvoetbal)" (14.000). No page opened gave a different league figure. The contested row of 2026-10-01 is replaced. |
| Juve Stabia | `Q6748` | **unchanged** (13,000) | no page states the approved figure outside Wikipedia: en "2026–27 Serie B" table 7,642, it.wikipedia 7 642 "omologati"; the Lega B club page https://www.legab.it/seriebkt/squadra/juve-stabia carries no capacity |
| Padova | `Q8428` | **unchanged** (32,420) | en "2026–27 Serie B" table 32,420; it.wikipedia "32 420 totali (18 236 omologati)" on the same undated reference as before; the Lega B club page https://www.legab.it/seriebkt/squadra/padova carries no capacity |
| Paris FC | `Q1051013` | **ground corrected: Stade Jean-Bouin** (was Stade Charléty), position too | the club's own home page https://parisfc.fr/ lists the men's home matches at "Stade Jean Bouin" (Angers 22/11/2026, Le Mans 05/12/2026, Le Havre 02/01/2027); stadiums tables of en "2026–27 Ligue 1" (Stade Jean-Bouin, 20,000) and fr "Championnat de France de football 2026-2027" (Stade Jean-Bouin, 19 607). Capacity not written: the map keeps 20,000, and the two tables disagree (20,000 and 19,607), so the figure is left for Alexandru. |

## Corrections written (`data/clubs-manual.csv`)

| row | change |
|---|---|
| Hamburger SV II `Q5644342` (new) | ground Stadion Hoheluft, capacity 4680, position 53.587215 / 9.969698 |
| Paris FC `Q1051013` (new) | ground Stade Jean-Bouin, position 48.843319 / 2.252962 |
| PEC Zwolle `Q269151` | capacity 14000 |
| Koblenz, Plauen, Dacia Unirea Brăila (new), Heimstetten, Neustrelitz, Garching | tier `skip` |

## Left for Alexandru (nothing below was decided)

1. **TSV Havelse**: which of the two approved Hannover grounds the map should show (see Part A).
2. **FC Unirea Dej**: the map point is 362.5 km from Dej; the candidate is the unnamed stadium OSM way/271928305 (see Part B).
3. **Paris FC's capacity** at Stade Jean-Bouin: 20,000 (English table, and the map) or 19,607 (French table).
4. **Hamburger SV II's capacity**: written as the club's 4,680; de.wikipedia's table says 5,000 approved. de.wikipedia also says the move to Hoheluft was for 2024/25 and 2025/26 while Sportpark Eimsbüttel was modernised, so the row needs a look when the side moves back.
5. **Juve Stabia and Padova**: still the full capacity on the map; no page outside Wikipedia states the approved figure.
6. **Ten renamed grounds** keep their older name on the map (Würzburg, Verl, FSV Frankfurt, Offenbach, Zwickau, Aalen, Unterhaching, Bergisch Gladbach, Memmingen, Steinbach Haiger). Say if the current names are wanted.
7. **The 29 Liga III grounds** were not compared at all (no grounds table anywhere); two of their names differ from OpenStreetMap's (Pașcani, Inter Ilfov).
8. **SC Eltersdorf** (`Q821096`, "Sportanlage Langenau"): no pitch or named ground at the map point; the nearest object is a restaurant 33 m away. Not checked further.
9. **Overpass**: the 18 clubs not found by name (Unirea Dej apart) could be run again on a day the server answers.

## Checks

- `load_manual()` of `tools/fetch_clubs.py` reads `data/clubs-manual.csv` with 403 rows; its 16 messages are the standing notes on `skip` rows (13 before, plus the three hand rows now set to skip). A dry `apply_manual()` over the 13 club files gives 582 clubs (588 less the six skipped) and applies Hamburger SV II, Paris FC and PEC Zwolle as written. No new kind of message compared with the file before this session.
- `tools/check_club_culture.py` exits 0 (462 warnings, none new in kind: unused sources and clubs not on the map), `tools/check_derbies.py` exits 0, `tools/check_tickets.py` exits 0, `tools/test_propose_country.py` passes.
- Page tests run locally: `test_derbies.js` 17 passed, `test_zoom.js` 25, `test_search.js` 28, `test_coverage.js` 23, `test_nearme.js` 66; none failed.
- The club files are regenerated by `build-clubs.yml` on `main` after the merge. No `SHELL_VERSION` change.
