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
