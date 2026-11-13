// TEMPORARY - capacity audit, phase 1d. Renders one page in Chromium and prints its text and links as JSON.
const { chromium } = require('playwright');
(async () => {
  const url = process.argv[2];
  const out = { status: null, final: url, title: '', text: '', links: [] };
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext({ userAgent: 'FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)', locale: 'en-GB' });
    const page = await ctx.newPage();
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    out.status = resp ? resp.status() : null;
    await page.waitForLoadState('networkidle', { timeout: 12000 }).catch(() => {});
    await page.waitForTimeout(2500);
    out.final = page.url();
    out.title = await page.title();
    out.text = (await page.evaluate(() => document.body ? document.body.innerText : '')).slice(0, 400000);
    out.links = await page.evaluate(() => Array.from(document.querySelectorAll('a[href]')).slice(0, 1500).map(a => [a.href, (a.innerText || '').trim().slice(0, 60)]));
  } catch (e) {
    out.status = out.status || ('error ' + String(e).slice(0, 80));
  }
  await browser.close();
  console.log(JSON.stringify(out));
})();
