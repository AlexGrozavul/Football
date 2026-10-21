#!/usr/bin/env python3
"""
Offline test of propose_country.py's classification: hand-made Wikidata items,
no network. Run from the repo root:  python3 tools/test_propose_country.py
Exits 1 on the first wrong answer.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import propose_country as pc          # noqa: E402
import propose_grounds as pg          # noqa: E402

REAL_OVERPASS_ELEMENTS = pg.overpass_elements     # the tests below replace pg.overpass_elements with a stub

L1, L2, OTHER = "Q1", "Q2", "Q99"
TRACKED = {L1: 1, L2: 2}
LABELS = {L1: "Liga One", L2: "Liga Two", OTHER: "Third Liga", "Q5000": "association football club",
          "Q5001": "women's association football club", "Q5002": "season of a football club",
          "G1": "Ground One", "G2": "Ground Two"}


def info(qid, label, p118=(), types=("Q5000",), p831=(), dissolved=None, grounds=(), desc=None,
         labels=None, p2094=()):
    stm = [{"league": l, "rank": r, "snaktype": st, "start": None, "end": None}
           for l, r, st in p118]
    visible = pc.dg.truthy_leagues([(s["league"], s["rank"], s["snaktype"]) for s in stm])
    tiers = [TRACKED[q] for q in visible if q in TRACKED]
    gs = [{"value": g, "rank": "normal", "snaktype": "value", "start": None, "end": None} for g in grounds]
    return {"qid": qid, "label": label, "labels": labels or [label], "desc": desc, "sitelinks": {"enwiki": label},
            "types": list(types), "p118": stm, "visible": visible, "tier": min(tiers) if tiers else None,
            "tracked": [s for s in stm if s["league"] in TRACKED], "dissolved": dissolved, "p17": ["Q45"],
            "grounds_all": gs, "grounds_truthy": gs, "coord": None, "p831": list(p831), "p361": [], "p749": [],
            "p2094": list(p2094)}


def rec(tier, qid, team):
    return {"tier": tier, "article": f"A{tier}", "team": team, "title": team, "qid": qid,
            "ground": "G", "ground_title": None, "capacity": 1000}


N = ("normal", "value")
infos = {
    "Q10": info("Q10", "Ok FC", [(L1, *N)]),
    "Q11": info("Q11", "Wrong Tier FC", [(L2, *N)]),                      # roster tier 1, tagged 2
    "Q12": info("Q12", "Untagged FC", [(OTHER, *N)]),
    "Q13": info("Q13", "Shape A FC", [(L1, "deprecated", "value")]),
    "Q14": info("Q14", "Shape B FC", [(L1, "normal", "value"), (L1, "preferred", "novalue")]),
    "Q15": info("Q15", "Shape C FC", [(L1, "normal", "value"), (OTHER, "preferred", "value")]),
    "Q16": info("Q16", "Club Item"),                                      # shape 5: club item, no tag
    "Q17": info("Q17", "Club Item", [(L1, *N)], types=("Q5000",), p831=["Q16"]),   # its team item
    "Q20": info("Q20", "Stale FC", [(L2, *N)]),                           # extra-tagged
    "Q21": info("Q21", "2020-21 Ok FC season", [(L1, *N)], types=("Q5002",)),  # not a club
    "Q22": info("Q22", "Ladies FC", [(L2, *N)], types=("Q5001",)),         # women
    "Q23": info("Q23", "Dead FC", [(L2, *N)], dissolved="1999"),           # dissolved: no row
    "Q24": info("Q24", "Two Grounds FC", [(L2, *N)], grounds=["G1", "G2"]),
    "Q25": info("Q25", "Ok FC", [(L2, *N)]),                               # duplicate label of Q10
    "Q26": info("Q26", "Hidden FC", [(L2, "deprecated", "value")]),        # hidden extra, no row
}
ctx = {
    "country_qid": "Q45", "tracked": TRACKED,
    "roster": [rec(1, "Q10", "Ok FC"), rec(1, "Q11", "Wrong Tier FC"), rec(2, "Q12", "Untagged FC"),
               rec(1, "Q13", "Shape A FC"), rec(1, "Q14", "Shape B FC"), rec(1, "Q15", "Shape C FC"),
               rec(1, "Q16", "Club Item")],
    "gaps": [(2, "A2", "Reserve II", "the team cell has no link of its own")],
    "infos": infos,
    "tagged": {q: [] for q in infos if infos[q]["tracked"]},
    "label": lambda q: LABELS.get(q, q), "league_label": lambda q: LABELS.get(q, q),
    "ground_label": lambda q: LABELS.get(q, q), "ground_coord": lambda i: None,
    "intro": {"Q20": ("Stale FC is a club that plays in the Third Liga.", "https://en.wikipedia.org/wiki/Stale_FC")},
    "team_changes": {"Q11": [("A1", "From Liga One: Wrong Tier FC")]},
    "pointers": {"W1": {"qid": "W1", "label": "Ok FC Women", "desc": "women's team", "to": {("Q10", "P361")},
                        "types": {"women's association football club"}, "classes": set()}},
}
rows, notes = pc.classify(ctx)


def kinds_of(q):
    return sorted(r["kind"] for r in rows if r["clubQid"] == q)


EXPECT = {
    "Q10": ["duplicate", "roster-ok"], "Q11": ["roster-wrong-tier"], "Q12": ["roster-untagged"],
    "Q13": ["rank-shape"], "Q14": ["rank-shape"], "Q15": ["rank-shape"],
    "Q16": ["roster-ok"],                        # joined to its team item Q17 through P831
    "Q17": [],                                   # not an extra: it IS Q16
    "Q20": ["extra-tagged"], "Q21": ["not-a-club"], "Q22": ["women-candidate"], "Q23": [],
    "Q24": ["extra-tagged", "two-grounds"], "Q25": ["duplicate", "extra-tagged"], "Q26": [],
    "W1": ["women-candidate"], "": ["roster-unread"],
}
bad = 0
for q, want in EXPECT.items():
    got = kinds_of(q)
    ok = got == sorted(want)
    bad += not ok
    print(("ok   " if ok else "FAIL ") + f"{q or '(gap)':<5} want {sorted(want)} got {got}")

shape = {r["clubQid"]: r["detail"] for r in rows if r["kind"] == "rank-shape"}
for q, letter in (("Q13", "A"), ("Q14", "B"), ("Q15", "C")):
    ok = f"shape={letter}" in shape.get(q, "")
    bad += not ok
    print(("ok   " if ok else "FAIL ") + f"{q} is shape {letter}")
checks = [
    ("Q23 listed as dissolved-tagged", [x[0] for x in notes["dissolved_tagged"]] == ["Q23"]),
    ("Q26 listed as hidden extra", [x[0] for x in notes["hidden_extras"]] == ["Q26"]),
    ("a roster-ok row has no invented decision words", all("skip" not in r["detail"].lower() for r in rows)),
    ("the wrong-tier row carries the team-changes evidence",
     "From Liga One" in next(r["detail"] for r in rows if r["kind"] == "roster-wrong-tier")),
    ("every row has the seven columns", all(set(r) == set(pc.HEADER) for r in rows)),
    ("season_of", pc.season_of("2026–27 Primeira Liga") == "2026-27"),
    ("fmt_time year precision", pc.fmt_time({"time": "+2010-00-00T00:00:00Z", "precision": 9}) == "2010"),
]
for name, ok in checks:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)
# --- the ground and capacity rules (propose_grounds.py)
cap = pg.capacity_rule
more = [
    ("Arouca: table and StadiumDB 5000 against Wikidata 5600 -> agreed 5000 from the table",
     cap(5000, 5600, None, 5000)[:3] == ("agreed", 5000, "table")),
    ("Casa Pia: table and Wikidata 7000 only -> single source, blank",
     cap(7000, 7000, None, None)[:2] == ("single-source", None)),
    ("Wikidata and OpenStreetMap agree, no table -> agreed, Wikidata's figure",
     cap(None, 12000, 12400, None)[:3] == ("agreed", 12000, "wikidata")),
    ("table 10000, Wikidata 8000, StadiumDB 20000, OSM 5000 -> contested, blank",
     cap(10000, 8000, 5000, 20000)[:2] == ("contested", None)),
    ("table and Wikidata disagree, nothing else -> single source, blank",
     cap(10000, 8000, None, None)[:2] == ("single-source", None)),
    ("no figure at all -> none", cap(None, None, None, None)[0] == "none"),
    ("exactly 5% apart agrees, just over does not", pg.within(1000, 1050) and not pg.within(1000, 1060)),
    ("a ground article and the same name in other words: exact",
     pg.name_strength("Estádio Municipal de Rio Maior", "Estádio Municipal de Rio Maior") == "exact"),
    ("'Estádio do CD Aves' is contained in 'Estádio do Clube Desportivo das Aves'",
     pg.name_strength("Estádio do CD Aves", "Estádio do Clube Desportivo das Aves") == "contained"),
    ("two different grounds do not match", pg.name_strength("Estádio Algarve", "Estádio de São Luís") is None),
    ("the table's ', at Town' tail and footnote go", pg.clean_ground("Estádio Municipal de Rio Maior , at Rio Maior[3]")
     == "Estádio Municipal de Rio Maior"),
    ("haversine: same point 0 m, one degree of latitude about 111 km",
     pg.haversine_m((38.7, -9.1), (38.7, -9.1)) == 0 and 110000 < pg.haversine_m((38, -9), (39, -9)) < 112500),
    ("pick_centre takes the first position it is given",
     pg.pick_centre([("a", None), ("b", (1, 2)), ("c", (3, 4))]) == ("b", (1, 2))),
]
for name, ok in more:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)

# --- the whole of propose_grounds.propose() with the network mocked
def fake_entities(qids, langs, props=""):
    ents = {}
    for q in qids:
        g = GROUNDS[q]
        claims = {}
        if g["coord"]:
            claims["P625"] = [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {
                "type": "globecoordinate", "value": {"latitude": g["coord"][0], "longitude": g["coord"][1]}}}}]
        if g["cap"]:
            claims["P1083"] = [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {
                "type": "quantity", "value": {"amount": f"+{g['cap']}"}}}}]
        ents[q] = {"id": q, "labels": {"en": {"value": g["label"]}}, "claims": claims,
                   "aliases": {"en": [{"value": a} for a in g.get("aliases", [])]}}
    return ents, []


GROUNDS = {"G10": {"label": "Estadio Arouca", "coord": (40.9300, -8.2500), "cap": 5600},
           "G11": {"label": "Estadio Algarve", "coord": (37.0900, -8.1100), "cap": 30305}}
base = dict(tier=1, article="A1", ground_title=None)
roster = [
    dict(base, qid="Q101", team="Arouca", title="Arouca FC", ground="Estadio Arouca", capacity=5000,
         ground_title="Estadio Arouca"),
    dict(base, qid="Q102", team="Farense", title="Farense FC", ground="Estadio de Sao Luis", capacity=7000,
         ground_title="Estadio de Sao Luis"),
    dict(base, qid="Q103", team="Casa Pia", title="Casa Pia AC", ground="Estadio Municipal de Rio Maior , at Rio Maior",
         capacity=7000, ground_title="Estadio Municipal de Rio Maior"),
]
ginfos = {
    "Q101": dict(info("Q101", "Arouca FC", [(L1, *N)]), grounds_all=[{"value": "G10", "rank": "normal", "snaktype": "value", "start": None, "end": None}],
                 grounds_truthy=[{"value": "G10", "rank": "normal", "snaktype": "value", "start": None, "end": None}]),
    "Q102": dict(info("Q102", "Farense FC", [(L1, *N)]), grounds_all=[{"value": "G11", "rank": "normal", "snaktype": "value", "start": None, "end": None}],
                 grounds_truthy=[{"value": "G11", "rank": "normal", "snaktype": "value", "start": None, "end": None}]),
    "Q103": info("Q103", "Casa Pia AC", [(L1, *N)]),
}
pc.fetch_entities = fake_entities
pg.ground_search = lambda pcm, wanted, langs, cw: {}
pg.article_coordinates = lambda pcm, titles: {"Estadio de Sao Luis": (37.0228, -7.9286),
                                              "Estadio Municipal de Rio Maior": (39.3445, -8.9352)}
pg.club_infobox_grounds = lambda pcm, titles: {"Casa Pia AC": "Estadio Pina Manique"}
pg.overpass_elements = lambda pcm, centres: ({
    ("way", 1): {"ref": "way/1", "pos": (40.9302, -8.2501), "tags": {"name": "Estadio Arouca", "leisure": "stadium", "capacity": "5000"}},
    ("way", 2): {"ref": "way/2", "pos": (37.0229, -7.9285), "tags": {"name": "Estadio de Sao Luis", "leisure": "stadium"}},
    ("way", 3): {"ref": "way/3", "pos": (39.3446, -8.9351), "tags": {"name": "Estadio Municipal de Rio Maior", "leisure": "pitch", "sport": "soccer"}},
    ("way", 4): {"ref": "way/4", "pos": (39.3447, -8.9353), "tags": {"name": "Pavilhao qualquer", "leisure": "sports_centre"}}}, None)
pg.robots_allows = lambda pcm, base, path: (True, f"{base}/robots.txt: test")
pg.stadiumdb_grounds = lambda pcm, args, label, probe: ([
    pg.sdb.ground("Estadio Arouca", "Arouca", "Arouca", 5000)], "por", ["StadiumDB slug 'por' answered (test)"], [])


class A:                      # the arguments propose() reads
    country = "PT"
    probe_slug = False


gctx = {"infos": ginfos, "roster": roster, "twin_of": {}, "country_label": "Portugal"}
gfail = []
grows = pg.propose(pc, A, gctx, [], gfail)
gd = {(r["kind"], r["clubQid"]): r["detail"] for r in grows}
more2 = [
    ("two rows per club", len(grows) == 6 and not gfail),
    ("Arouca's ground agrees everywhere", "verdict=ok" in gd[("ground-proposal", "Q101")]),
    ("Arouca capacity: table and StadiumDB agree, the map's 5600 is replaced",
     "proposed=5000" in gd[("capacity-proposal", "Q101")] and "REPLACE the map's 5600" in gd[("capacity-proposal", "Q101")]),
    ("Farense: Wikidata names another ground, and the map would be far from the proposal",
     "verdict=attention" in gd[("ground-proposal", "Q102")] and "THE MAP WOULD BE" in gd[("ground-proposal", "Q102")]
     and "Wikidata names 'Estadio Algarve'" in gd[("ground-proposal", "Q102")]),
    ("Farense: the proposed position is the ground article's, OSM agrees within 150 m",
     "proposed_position=37.022800" in gd[("ground-proposal", "Q102")] and "AGREE within 150 m" in gd[("ground-proposal", "Q102")]),
    ("Casa Pia: the build leaves it unplaced, and the proposal says where",
     "verdict=unplaced" in gd[("ground-proposal", "Q103")] and "UNPLACED" in gd[("ground-proposal", "Q103")]
     and "proposed_position=39.3445" in gd[("ground-proposal", "Q103")]),
    ("Casa Pia: the club article's infobox ground is listed as another name",
     "club article infobox=Estadio Pina Manique" in gd[("ground-proposal", "Q103")]),
    ("Casa Pia: a ', at Rio Maior' tail is not part of the ground", "proposed_venue=Estadio Municipal de Rio Maior;" in gd[("ground-proposal", "Q103")]),
    ("the sports hall that is not the ground is not an OSM candidate",
     "Pavilhao" not in gd[("ground-proposal", "Q103")]),
]
for name, ok in more2:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)

# --- three corrections found on the first real run
GROUNDS.update({"G12": {"label": "Estadio da Luz", "coord": (38.7527, -9.1847), "cap": 64642, "aliases": ["Benfica Stadium"]},
                "G13": {"label": "Estadio Municipal 22 de Junho", "coord": (41.4013, -8.5224), "cap": 5307}})
roster2 = [
    dict(base, qid="Q104", team="Benfica", title="S.L. Benfica", ground="Estadio da Luz", capacity=64642, ground_title="Estadio da Luz"),
    dict(base, qid="Q105", team="Benfica B", title="S.L. Benfica B", ground="Benfica Campus - Campo n.o 1", capacity=2644,
         ground_title="Benfica Campus"),
    dict(base, qid="Q106", team="Famalicao", title="F.C. Famalicao", ground="Estadio Municipal de Famalicao", capacity=5307,
         ground_title="Estadio Municipal de Famalicao"),
]
G = lambda g: [{"value": g, "rank": "normal", "snaktype": "value", "start": None, "end": None}]
ginfos2 = {
    "Q104": dict(info("Q104", "S.L. Benfica", [(L1, *N)]), grounds_all=G("G12"), grounds_truthy=G("G12")),
    "Q105": dict(info("Q105", "S.L. Benfica B", [(L2, *N)]), grounds_all=G("G12"), grounds_truthy=G("G12")),
    "Q106": dict(info("Q106", "F.C. Famalicao", [(L1, *N)]), grounds_all=G("G13"), grounds_truthy=G("G13")),
}
pg.article_coordinates = lambda pcm, titles: {"Benfica Campus": (38.6405, -9.0919), "Estadio Municipal de Famalicao": (41.4014, -8.5225),
                                              "Estadio da Luz": (38.7527, -9.1847)}
pg.club_infobox_grounds = lambda pcm, titles: {"F.C. Famalicao": "Estadio Municipal 22 de Junho"}
pg.stadiumdb_grounds = lambda pcm, args, label, probe: ([
    pg.sdb.ground("Estadio Municipal 22 de Junho", "Vila Nova de Famalicao", "Famalicao", 5307)], "por", [], [])
robots_asked = []
pg.robots_allows = lambda pcm, base, path: robots_asked.append(base) or (True, f"{base}/robots.txt: test")
pg.ground_search = lambda pcm, wanted, langs, cw: {"Q107": [{"qid": "Q900", "label": "Complexo Desportivo FC Alverca",
                                                         "coord": (38.8988, -9.0368), "cap": None, "desc": "stadium"}]}
asked = []
pg.overpass_elements = lambda pcm, centres: asked.append(1) or ({}, None)
gfail2 = []
grows2 = pg.propose(pc, A, {"infos": ginfos2, "roster": roster2, "twin_of": {}, "country_label": "Portugal"}, [], gfail2)
gd2 = {(r["kind"], r["clubQid"]): r["detail"] for r in grows2}
more3 = [
    ("Overpass is asked (the published usage policy governs, not its robots.txt) and robots.txt is not read for it",
     asked and not gfail2 and "osm=queried" in gd2[("ground-proposal", "Q105")]
     and not any("overpass" in b for b in robots_asked)),
    ("Benfica B: 'Benfica Stadium' is the club's name, not agreement; the P115 is flagged as the first team's",
     "verdict=attention" in gd2[("ground-proposal", "Q105")] and "first team's ground" in gd2[("ground-proposal", "Q105")]),
    ("Benfica B: the proposal is the campus article's position, not the Luz",
     "proposed_position=38.640500" in gd2[("ground-proposal", "Q105")]),
    ("Benfica (first team) is not flagged for sharing with its own reserve side",
     "verdict=ok" in gd2[("ground-proposal", "Q104")] and "also its reserve side's" in gd2[("ground-proposal", "Q104")]),
    ("Famalicao: the table is the odd one out, a note and not a problem",
     "verdict=ok" in gd2[("ground-proposal", "Q106")] and "odd one out" in gd2[("ground-proposal", "Q106")]),
    ("Famalicao: the table is the odd one out, so Wikidata's capacity is this ground's and nothing is cleared",
     "verdict=agreed" in gd2[("capacity-proposal", "Q106")] and "CLEAR" not in gd2[("capacity-proposal", "Q106")]),
    ("a pitch number is not part of the ground's name",
     pg.name_strength("Benfica Campus - Campo n.° 1", "Caixa Futebol Campus", {"benfica"}) == "contained"),
    ("a name that is only the club's name is no agreement",
     pg.name_strength("Benfica Campus", "Benfica Stadium", {"benfica"}) is None
     and pg.name_strength("Estadio Benfica", "Estadio Benfica", {"benfica"}) == "exact"),
]
for name, ok in more3:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)

# --- the name-search route and the capacity corrections
GROUNDS.update({"G14": {"label": "Estadio Municipal Jorge Sampaio", "coord": (41.0671, -8.5448), "cap": 8500}})
roster3 = [
    dict(base, qid="Q107", team="Alverca", title="F.C. Alverca", ground="Complexo Desportivo FC Alverca", capacity=6932, ground_title=None),
    dict(base, qid="Q108", team="Porto B", title="FC Porto B", ground="Estadio Luis Filipe Menezes", capacity=3800, ground_title=None),
    dict(base, qid="Q109", team="Casa Pia", title="Casa Pia AC", ground="Estadio Municipal de Rio Maior", capacity=7000,
         ground_title="Estadio Municipal de Rio Maior"),
]
ginfos3 = {
    "Q107": info("Q107", "F.C. Alverca", [(L1, *N)]),
    "Q108": dict(info("Q108", "FC Porto B", [(L2, *N)]), grounds_all=G("G14"), grounds_truthy=G("G14")),
    "Q109": info("Q109", "Casa Pia AC", [(L1, *N)]),
}
pg.article_coordinates = lambda pcm, titles: {"Estadio Municipal de Rio Maior": (39.3445, -8.9352)}
pg.club_infobox_grounds = lambda pcm, titles: {}
pg.stadiumdb_grounds = lambda pcm, args, label, probe: ([
    pg.sdb.ground("Estadio Pina Manique", "Lisboa", "Casa Pia", 2574)], "por", [], [])
grows3 = pg.propose(pc, A, {"infos": ginfos3, "roster": roster3, "twin_of": {}, "country_label": "Portugal"}, [], [])
gd3 = {(r["kind"], r["clubQid"]): r["detail"] for r in grows3}
more4 = [
    ("Alverca: no P115, no article - the ground's own Wikidata item found by name gives the position",
     "proposed_position=38.898800" in gd3[("ground-proposal", "Q107")] and "found by searching" in gd3[("ground-proposal", "Q107")]),
    ("Porto B: the map's 8500 is the capacity of another ground: CLEAR, and nothing is proposed",
     "CLEAR the map's 8500" in gd3[("capacity-proposal", "Q108")] and "proposed=BLANK" in gd3[("capacity-proposal", "Q108")]),
    ("Casa Pia: StadiumDB's 2574 is another ground, not a disagreement - single source, blank",
     "verdict=single-source" in gd3[("capacity-proposal", "Q109")] and "different ground" in gd3[("capacity-proposal", "Q109")]),
]
for name, ok in more4:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)

# --- the Overpass client: only 429 and 504 wait and retry; every request counts against the cap
import io
import json as _json
import urllib.error as _ue
import urllib.request as _ur

_real_open, _real_sleep, _real_gap = _ur.urlopen, pg.time.sleep, pc.MIN_GAP
slept = []
pg.time.sleep = lambda secs: slept.append(secs)
pc.MIN_GAP = 0


class _Resp:
    def __init__(self, text): self.text = text
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self.text.encode("utf-8")


def _scripted(*answers):
    seq = list(answers)

    def opener(req, timeout=None):
        a = seq.pop(0)
        if isinstance(a, int):
            raise _ue.HTTPError(req.full_url, a, "x", {"Retry-After": "7"} if a == 429 else {}, io.BytesIO(b""))
        if isinstance(a, Exception):
            raise a
        return _Resp(a)
    return opener


ok_json = _json.dumps({"elements": [{"type": "way", "id": 9, "center": {"lat": 1.0, "lon": 2.0},
                                     "tags": {"name": "Estadio X", "leisure": "stadium"}}]})
pg._overpass_used[0] = 0
_ur.urlopen = _scripted(504, 429, 502, ok_json)
els, err = REAL_OVERPASS_ELEMENTS(pc, [(1.0, 2.0), (1.0, 2.0)])
used_504_429 = pg._overpass_used[0]
pg._overpass_used[0] = 0
_ur.urlopen = _scripted(500)
els500, err500 = REAL_OVERPASS_ELEMENTS(pc, [(1.0, 2.0)])
used_500 = pg._overpass_used[0]
pg._overpass_used[0] = 0
_ur.urlopen = _scripted(TimeoutError("The read operation timed out"), ok_json)
_els_to, err_to = REAL_OVERPASS_ELEMENTS(pc, [(1.0, 2.0)])
used_to = pg._overpass_used[0]
pg._overpass_used[0] = 0
_ur.urlopen = _scripted(_ue.URLError("reset"))
_els_n, err_net = REAL_OVERPASS_ELEMENTS(pc, [(1.0, 2.0)])
used_net = pg._overpass_used[0]
pg._overpass_used[0] = pg.OVERPASS_MAX_REQUESTS
_ur.urlopen = _scripted(ok_json)
_els_cap, err_cap = REAL_OVERPASS_ELEMENTS(pc, [(1.0, 2.0)])
used_cap = pg._overpass_used[0]
pg._overpass_used[0] = 0
_ur.urlopen = _scripted(ok_json, ok_json, ok_json, ok_json, ok_json)
REAL_OVERPASS_ELEMENTS(pc, [(40.0 + i / 100, -8.0) for i in range(85)])       # 85 centres = 5 requests of up to 20
used_chunks = pg._overpass_used[0]
_ur.urlopen, pg.time.sleep, pc.MIN_GAP = _real_open, _real_sleep, _real_gap
pg._overpass_used[0] = 0

more5 = [
    ("Overpass: 504, 429, 502 then a good answer = 4 requests, each wait at least 30 s (Retry-After 7 does not shorten it)",
     err is None and ("way", 9) in els and used_504_429 == 4 and slept[:3] == [30, 30, 30]),
    ("Overpass: a 500 is not retried", err500 == "HTTP 500" and used_500 == 1),
    ("Overpass: a read timeout is retried like a 504", err_to is None and used_to == 2),
    ("Overpass: another network error is not retried", err_net and err_net.startswith("network error") and used_net == 1),
    ("Overpass: at the cap of 60 requests nothing more is asked", err_cap and "cap of 60" in err_cap and used_cap == 60),
    ("Overpass: 85 centres go in 5 requests of at most 20", used_chunks == 5),
]
for name, ok in more5:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)

# --- an Overpass failure is a warning, not a run failure: the rest of the evidence is written
pg.overpass_elements = lambda pcm, centres: (None, "HTTP 502")
fail_f = []
fail_rows = pg.propose(pc, A, {"infos": ginfos2, "roster": roster2, "twin_of": {}, "country_label": "Portugal"}, [], fail_f)
fd = {(r["kind"], r["clubQid"]): r["detail"] for r in fail_rows}
more6 = [
    ("Overpass failed: not a run failure, the rows are still written and say so",
     not fail_f and len(fail_rows) == 6 and "osm=asked and failed: HTTP 502" in fd[("ground-proposal", "Q105")]),
]
for name, ok in more6:
    bad += not ok
    print(("ok   " if ok else "FAIL ") + name)
print("FAILED" if bad else "all passed")
sys.exit(1 if bad else 0)
