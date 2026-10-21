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
print("FAILED" if bad else "all passed")
sys.exit(1 if bad else 0)
