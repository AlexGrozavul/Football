"""Throwaway probe, removed in the same branch: read the Baden-Wuerttemberg
ministry's school holiday page and print its footnotes. Reads, writes nothing."""
import html, re, sys, urllib.request

UA = "Mozarella-free probe (football planner; github.com/alexgrozavul/football)"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) football-planner-probe"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.headers.get("content-type"), r.read().decode("utf-8", "replace")

for url in ["https://km.baden-wuerttemberg.de/robots.txt"]:
    try:
        s, ct, body = get(url)
        print("ROBOTS", s, ct); print(body[:3000])
    except Exception as e:
        print("ROBOTS failed", e)

url = "https://km.baden-wuerttemberg.de/de/service/ferien"
s, ct, body = get(url)
print("PAGE", s, ct, len(body))
main = body
m = re.search(r"<main.*?</main>", body, re.S)
if m: main = m.group(0)
main = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", main, flags=re.S)
main = re.sub(r"<sup[^>]*>(.*?)</sup>", r"[sup:\1]", main, flags=re.S)
main = re.sub(r"</(p|div|tr|li|h\d|table|caption)>", "\n", main)
main = re.sub(r"<(td|th)[^>]*>", " | ", main)
text = html.unescape(re.sub(r"<[^>]+>", " ", main))
text = "\n".join(re.sub(r"[ \t ]+", " ", l).strip() for l in text.splitlines())
text = re.sub(r"\n{2,}", "\n", text)
print("=== TEXT START ===")
print(text[:12000])
print("=== TEXT END ===")
for k in ["Herbstferien", "Osterferien", "Fußnote", "[sup:", "1)", "2)", "¹", "²", "*"]:
    for mm in re.finditer(re.escape(k), text):
        print("HIT", k, "::", text[max(0, mm.start()-200):mm.start()+400].replace("\n", " / "))
        break
