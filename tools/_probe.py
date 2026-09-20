"""THROWAWAY probe. Remove with the temporary workflow step that runs it."""
import sys, time, urllib.parse

sys.path.insert(0, "tools")
import check_rosters as CR
import diagnose_p118_rank as RANK

OF_INTEREST = ["Q368104", "Q24884611", "Q1386940", "Q113541238", "Q1024390"]

HEAD = []


def year_of(entity, prop):
    for st in (entity.get("claims") or {}).get(prop) or []:
        v = (((st.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {})
        if isinstance(v, dict) and v.get("time"):
            return v["time"].lstrip("+")[:4]
    return None


def wbsearch(term):
    q = urllib.parse.urlencode({
        "action": "wbsearchentities", "search": term, "language": "en",
        "uselang": "en", "type": "item", "limit": "12",
        "format": "json", "formatversion": "2"})
    data, err = CR.get_json_with_retry(f"{CR.WIKIDATA_API}?{q}", f"search {term}")
    if err or not data:
        return [("SEARCH FAILED", str(err))]
    return [(r.get("id"), f"{r.get('label') or ''} -- {r.get('description') or ''}")
            for r in data.get("search") or []]


print("=" * 72)
print("PROBE: Romanian tier 1 and tier 2 -- rosters, rank, identities")
print("=" * 72)

# --------------------------------------------------------- 1. the rosters
mapped = RANK.load_tiers()
rows, problems = CR.load_config()
for p in problems:
    print(f"  ! config: {p}")

roster = {}
for row in rows:
    if row["country"] != "RO" or row["tier"] not in ("1", "2", "3"):
        continue
    tier = row["tier"]
    if tier in roster:
        continue
    print(f"\n--- ROSTER RO tier {tier}: {row['article']}")
    page, title, err = CR.fetch_article(row["article"])
    if err:
        print(f"    FETCH FAILED: {err}")
        continue
    tables, shape = CR.roster_tables(page)
    titles = []
    for table, headers in tables:
        for t, _cap in CR.rows_of(table, headers):
            if t not in titles:
                titles.append(t)
    print(f"    {title!r} via {shape}: {len(titles)} linked titles")
    found, failures = CR.qids_for_titles(titles)
    for f in failures:
        print(f"    ! {f}")
    roster[tier] = {found[t]: t for t in titles if t in found}
    if tier in ("1", "2"):
        for t in titles:
            print(f"      {found.get(t, '(no Q-id)'):<12} {t}")
    else:
        print(f"      (tier 3: {len(found)} of {len(titles)} titles resolved, not listed)")

print("\n--- ARE THE CLUBS OF INTEREST IN ANY RO ROSTER?")
for cid in OF_INTEREST:
    where = [f"RO tier {t}" for t in ("1", "2", "3") if cid in roster.get(t, {})]
    line = f"    {cid:<12} {', '.join(where) if where else 'IN NO RO ROSTER (1/2/3)'}"
    print(line)
    HEAD.append(line)

# ------------------------------------------------- 2. rank-hidden clubs
print("\n--- RANK: clubs carrying a mapped league on a statement wdt:P118 will not yield")
values = " ".join("wd:" + lid for lid in sorted(mapped))
data, err = RANK.sparql_with_retry(RANK.QUERY_HIDDEN % {"leagues": values}, "hidden")
hidden_qids = []
if err:
    print(f"    QUERY FAILED: {err}")
    HEAD.append(f"    RANK QUERY FAILED: {err}")
else:
    seen = {}
    for row in data.get("results", {}).get("bindings", []):
        cid = RANK.qid(RANK.cell(row, "club"))
        if not cid:
            continue
        entry = seen.setdefault(cid, {"label": RANK.cell(row, "clubLabel") or "", "st": set()})
        entry["st"].add((RANK.qid(RANK.cell(row, "league")),
                         (RANK.cell(row, "rank") or "").rsplit("#", 1)[-1]))
    hidden_qids = sorted(seen)
    print(f"    {len(hidden_qids)} clubs")
    for cid in hidden_qids:
        st = ", ".join(f"{l}/{r}" for l, r in sorted(seen[cid]["st"]))
        print(f"      {cid:<12} {seen[cid]['label'][:34]:<34} {st}")

# ----------------------------------------------- 3. the items themselves
print("\n--- THE ITEMS")
want = list(dict.fromkeys(OF_INTEREST + hidden_qids))
ents, failures = RANK.fetch_entities(want)
for f in failures:
    print(f"    ! {f}")
for cid in want:
    e = ents.get(cid)
    if not e:
        print(f"    {cid}: NOT READ")
        continue
    st = RANK.league_statements(e)
    truthy = RANK.truthy_leagues(st)
    novalue_pref = any(r == "preferred" and s != "value" for _v, r, s in st)
    in_roster = [t for t in ("1", "2", "3") if cid in roster.get(t, {})]
    print(f"    {cid}  {RANK.label_of(e)}  sitelinks={RANK.sitelink_count(e)}")
    print(f"        P31={RANK.first_qid(e,'P31')} P17={RANK.first_qid(e,'P17')} "
          f"P115={RANK.first_qid(e,'P115')} P625={RANK.has_claim(e,'P625')} "
          f"P576={RANK.dissolved_year(e)} P571={year_of(e,'P571')}")
    for vid, rank, snak in st:
        tier = mapped.get(vid or "")
        print(f"        P118 {rank:<10} {snak:<9} {str(vid):<12} "
              f"{'TRUTHY' if vid in truthy else 'hidden'} "
              f"{('tier %s %s %s' % tier) if tier else ''}")
    print(f"        => wdt:P118 yields {truthy or 'NOTHING'}; "
          f"preferred-novalue={novalue_pref}; roster={in_roster or 'none'}")

# ------------------------------------------------------- 4. name searches
print("\n--- SEARCHES")
for term in ("Politehnica Iasi", "FC Hermannstadt", "Bihor Oradea", "Farul Constanta"):
    print(f"    {term}:")
    for cid, desc in wbsearch(term):
        print(f"      {str(cid):<12} {desc[:74]}")
    time.sleep(1)

print("\n" + "=" * 72)
print("HEADLINES REPEATED (log tails are what get read)")
print("=" * 72)
for line in HEAD:
    print(line)
