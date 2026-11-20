"""Temporary probe (German competitions batch 7). Reads the URLs of pages.tsv
and posts each page's text and full link list as PR comments. Removed before merge.
pages.tsv: one line per entry. 'HOST <url>' = robots.txt, the landing page <url>
and the legal-notice / terms links found on it; '<url>' = one page."""
import os, sys, time, json, re, subprocess, tempfile, urllib.request, urllib.parse, urllib.robotparser
from playwright.sync_api import sync_playwright

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
TOKEN, PR, REPO = os.environ["GITHUB_TOKEN"], os.environ["PR"], os.environ["REPO"]
LABEL = os.environ.get("RUN_LABEL") or "run"
LEGAL = re.compile(r"impressum|nutzungsbedingung|rechtliche|rechtshinweis|\bagb\b|terms|legal|disclaimer|haftungsausschluss", re.I)
LIMIT = 59000
buf, out_parts, last = [], [], [0.0]
DELAY = [4.0]  # Wikipedia 429 at 1/s (PR #234); raised to a robots.txt Crawl-delay where one is set
robots, stopped = {}, {}

def wait():
    d = time.time() - last[0]
    if d < DELAY[0]: time.sleep(DELAY[0] - d)
    last[0] = time.time()

def post(body):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/{PR}/comments",
        data=json.dumps({"body": body}).encode(), method="POST",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    for i in range(4):
        try:
            urllib.request.urlopen(req, timeout=60).read(); time.sleep(2); return
        except Exception as e:
            print("post failed", e); time.sleep(20 * (i + 1))

def emit(text):
    out_parts.append(text)

def flush():
    blob = "\n".join(out_parts); n = 0
    while blob:
        chunk, blob = blob[:LIMIT], blob[LIMIT:]
        n += 1
        post(f"<!-- probe {LABEL} part {n} -->\n```text\n{chunk.replace('```', "'''")}\n```")

def fetch_raw(url):
    wait()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        r = urllib.request.urlopen(req, timeout=40)
        return r.status, r.geturl(), r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, url, e.headers.get("Content-Type", "") if e.headers else "", e.read() if hasattr(e, "read") else b""
    except Exception as e:
        return None, url, "", str(e).encode()

def check_robots(url):
    p = urllib.parse.urlsplit(url); host = p.netloc
    if host in robots: return robots[host]
    st, fu, ct, body = fetch_raw(f"{p.scheme}://{host}/robots.txt")
    txt = body.decode("utf-8", "replace")
    emit(f"\n===== ROBOTS {host} status={st} final={fu}\n{txt[:20000]}")
    rp = urllib.robotparser.RobotFileParser(); flags = []
    if st == 200:
        rp.parse(txt.splitlines())
        cd = max([float(x) for x in (rp.crawl_delay(UA), rp.crawl_delay("ClaudeBot"), rp.crawl_delay("*")) if x] or [0])
        if cd > DELAY[0]: DELAY[0] = cd; flags.append(f"crawl-delay {cd}")
    elif st in (401, 403):
        stopped[host] = f"robots.txt answered {st}"
    if re.search(r"claude|anthropic", txt, re.I): flags.append("names Claude/Anthropic")
    if re.search(r"44b|text.?and.?data.?mining|\bTDM\b|data mining", txt, re.I): flags.append("TDM/44b notice")
    if re.search(r"challenge|captcha|cf-chl|just a moment", txt[:3000], re.I) and st != 200: stopped[host] = "challenge"
    emit(f"ROBOTS-FLAGS {host}: {', '.join(flags) or 'none'}; stop={stopped.get(host, 'no')}")
    robots[host] = (rp if st == 200 else None)
    return robots[host]

def allowed(url):
    host = urllib.parse.urlsplit(url).netloc
    rp = check_robots(url)
    if host in stopped: return False, stopped[host]
    if rp is not None and not rp.can_fetch(UA, url): return False, "robots.txt Disallow"
    return True, ""

def pdf_text(data):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "a.pdf"); open(f, "wb").write(data)
        t = subprocess.run(["pdftotext", "-layout", f, "-"], capture_output=True, text=True).stdout
        if len(t.strip()) > 200: return t, "pdftotext"
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-l", "15", f, os.path.join(d, "p")])
        o = ""
        for png in sorted(x for x in os.listdir(d) if x.endswith(".png")):
            o += subprocess.run(["tesseract", os.path.join(d, png), "-", "-l", "deu"], capture_output=True, text=True).stdout
        return o, "tesseract OCR (image-only PDF, first 15 pages)"

def read(page, url, legal_scan=False):
    ok, why = allowed(url)
    if not ok:
        emit(f"\n===== PAGE {url}\nNOT READ: {why}"); return []
    if re.search(r"\.pdf($|\?)", url, re.I) and "viewer.html" not in url:
        st, fu, ct, data = fetch_raw(url)
        t, how = pdf_text(data) if st == 200 else ("", "")
        emit(f"\n===== PDF {url} status={st} final={fu} via={how} chars={len(t)}\n{t}")
        return []
    wait()
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try: page.wait_for_load_state("networkidle", timeout=12000)
        except Exception: pass
        st = resp.status if resp else None
        ct = resp.headers.get("content-type", "") if resp else ""
        if "pdf" in ct:
            st2, fu, ct2, data = fetch_raw(url); t, how = pdf_text(data)
            emit(f"\n===== PDF {url} status={st2} final={fu} via={how}\n{t}"); return []
        for _ in range(6):
            page.mouse.wheel(0, 3000); page.wait_for_timeout(400)
        page.evaluate("""() => { for (const e of document.querySelectorAll('[id*=consent i],[class*=consent i],[id*=cookie i],[class*=cookie i],[id*=usercentrics i],#onetrust-consent-sdk,[id^=sp_message],[class*=cmp-] ,[id*=cmp i]')) { if (e !== document.body && e !== document.documentElement) e.remove(); } document.body.style.overflow='auto'; }""")
        text = page.evaluate("() => document.body ? document.body.innerText : ''")
        if "viewer.html" in url:
            try:
                page.wait_for_function("() => window.PDFViewerApplication && window.PDFViewerApplication.pdfDocument", timeout=30000)
                text = "[pdf.js viewer: text of the document the viewer loaded]\n" + page.evaluate("""async () => { const d = window.PDFViewerApplication.pdfDocument; let o = ''; for (let i = 1; i <= d.numPages; i++) { const p = await d.getPage(i); const c = await p.getTextContent(); let line = ''; let y = null; for (const it of c.items) { const yy = it.transform ? Math.round(it.transform[5]) : y; if (y !== null && yy !== y) { o += line + '\\n'; line = ''; } line += it.str + (it.hasEOL ? '' : ''); y = yy; if (it.hasEOL) { o += line + '\\n'; line=''; } } o += line + '\\n--- page ' + i + ' ---\\n'; } return o; }""")
            except Exception as e:
                text += f"\n[pdf.js text extraction failed: {e}]"
        links = page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => [(a.innerText||a.title||a.getAttribute('aria-label')||'').trim().replace(/\\s+/g,' ').slice(0,120), a.href])")
        title = page.title()
        emit(f"\n===== PAGE {url} status={st} final={page.url} title={title!r}\n{text}\n----- LINKS ({len(links)})")
        seen = set()
        for t, h in links:
            if (t, h) in seen: continue
            seen.add((t, h)); emit(f"{t} -> {h}")
        return links
    except Exception as e:
        if "Download is starting" in str(e):  # batch 5: lfvm-v.de download links
            st, fu, ct, data = fetch_raw(url)
            if data[:4] == b"%PDF" or "pdf" in ct:
                t, how = pdf_text(data)
                emit(f"\n===== PDF {url} status={st} final={fu} via={how} (download link) chars={len(t)}\n{t}"); return []
        emit(f"\n===== PAGE {url}\nERROR {e}"); return []

def main():
    lines = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_context(user_agent=UA, locale="de-DE").new_page()
        for l in lines:
            if l.startswith("HOST "):
                url = l.split()[1]
                links = read(page, url)
                legal, seenl = [], set()
                for t, h in links:
                    if LEGAL.search(t) and h.startswith("http") and h not in seenl and urllib.parse.urlsplit(h).netloc == urllib.parse.urlsplit(url).netloc:
                        seenl.add(h); legal.append(h)
                emit(f"LEGAL-LINKS {url}: {legal[:6]}")
                for h in legal[:3]: read(page, h)
            else:
                read(page, l)
        b.close()
    emit(f"\n===== STOPPED HOSTS {json.dumps(stopped)}")
    flush()

main()
