// Draws icons/icon.svg and icons/icon-maskable.svg: an original map pin with a ball in its head,
// in the page's own palette. No crest, no third-party mark. Run: node icons/draw-icon.js icons
// The PNGs beside them were rendered from these SVGs in headless Chromium (see CLAUDE.md, The installable app).
const fs = require('fs');
const out = process.argv[2];
const f = n => n.toFixed(2);
function pent(cx, cy, r, rotDeg){
  const p = [];
  for(let k=0;k<5;k++){ const a=(rotDeg+72*k)*Math.PI/180; p.push([cx+r*Math.cos(a), cy+r*Math.sin(a)]); }
  return p;
}
function svg(maskable){
  const BG='#0d1117', LINE='#1f2833', PIN='#e8543f', PIN_DARK='#b83b29', BALL='#e6edf3';
  const cx=256, cy=214, R=84;               // ball
  const head=122;                            // pin head radius
  const tipY=438;
  // pin: circle head + tapered tail meeting tangentially
  const ang = Math.asin(head/(tipY-cy));     // half-angle of tail cone
  const tx = head*Math.cos(ang), ty = head*Math.sin(ang);
  const pinPath = `M${f(cx-tx)},${f(cy+ty)} A${head},${head} 0 1 1 ${f(cx+tx)},${f(cy+ty)} L${cx},${tipY} Z`;
  const p = 0.37*R;
  const centre = pent(cx, cy, p, -90);
  let ball = `<circle cx="${cx}" cy="${cy}" r="${R}" fill="${BALL}"/>`;
  ball += `<g clip-path="url(#ballclip)" fill="#0d1117" stroke="#0d1117" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">`;
  ball += `<polygon points="${centre.map(q=>q.map(f).join(',')).join(' ')}"/>`;
  const outers = [];
  for(let k=0;k<5;k++){
    const a=(-90+72*k)*Math.PI/180;
    const ox=cx+(R*1.02)*Math.cos(a), oy=cy+(R*1.02)*Math.sin(a);
    const o = pent(ox, oy, p, -90+72*k+180);
    outers.push(o);
    ball += `<polygon points="${o.map(q=>q.map(f).join(',')).join(' ')}"/>`;
    ball += `<line x1="${f(centre[k][0])}" y1="${f(centre[k][1])}" x2="${f(o[0][0])}" y2="${f(o[0][1])}" fill="none"/>`;
  }
  for(let k=0;k<5;k++){ // hexagon seams between neighbouring outer patches
    const a=outers[k][4], b=outers[(k+1)%5][1];
    ball += `<line x1="${f(a[0])}" y1="${f(a[1])}" x2="${f(b[0])}" y2="${f(b[1])}" fill="none"/>`;
  }
  ball += `</g>`;
  // faint map roads in the background
  const roads = `<g stroke="${LINE}" stroke-width="14" fill="none" stroke-linecap="round">
    <path d="M-20,360 C120,330 180,420 300,400 S470,330 540,350"/>
    <path d="M90,-20 C110,120 60,240 120,540"/>
    <path d="M400,-20 C380,140 450,250 420,540"/></g>`;
  const bg = maskable
    ? `<rect width="512" height="512" fill="${BG}"/>`
    : `<rect x="16" y="16" width="480" height="480" rx="104" fill="${BG}"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs><clipPath id="ballclip"><circle cx="${cx}" cy="${cy}" r="${R}"/></clipPath>
${maskable ? '' : `<clipPath id="tile"><rect x="16" y="16" width="480" height="480" rx="104"/></clipPath>`}</defs>
${bg}
<g ${maskable ? '' : 'clip-path="url(#tile)"'}>${roads}</g>
<ellipse cx="${cx}" cy="${tipY+6}" rx="46" ry="12" fill="#000" opacity=".45"/>
<path d="${pinPath}" fill="${PIN}"/>
${ball}
</svg>
`;
}
fs.writeFileSync(out+'/icon.svg', svg(false));
fs.writeFileSync(out+'/icon-maskable.svg', svg(true));
