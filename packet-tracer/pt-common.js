const RED = '#e11d48';
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function t(x,y,s,o={}){return `<text x="${x}" y="${y}" font-size="${o.fs||11}" fill="${o.fill||'#111'}" font-weight="${o.fw||'normal'}" text-anchor="${o.a||'start'}" font-family="${o.ff||'Liberation Sans, Arial'}">${esc(s)}</text>`;}
function mark(x,y,r,n,o={}){ // kırmızı yuvarlak + numara rozeti
  const rx=o.rx||r, ry=o.ry||r;
  const bx = o.side ? Math.min(x + rx + 15, 886) : Math.min(x + rx*0.78 + 4, 886), by = o.side ? y : y - ry*0.78 - 4;
  return `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="none" stroke="${RED}" stroke-width="3.5"/>
  <circle cx="${bx}" cy="${by}" r="11" fill="${RED}" stroke="#fff" stroke-width="2"/>${t(bx,by+4,n,{fs:12,fill:'#fff',fw:'bold',a:'middle'})}`;
}
function arrow(x1,y1,x2,y2){
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${RED}" stroke-width="3" stroke-dasharray="7 5" marker-end="url(#ah)"/>`;
}
const DEFS = `<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${RED}"/></marker>
<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0 L0 0 0 20" fill="none" stroke="#eef2f7" stroke-width="1"/></pattern></defs>`;

// Cihaz simgeleri (temsili)
function router(x,y,s=1,label){
  return `<g transform="translate(${x},${y}) scale(${s})">
   <ellipse cx="0" cy="8" rx="26" ry="9" fill="#1e5a8a"/><rect x="-26" y="-6" width="52" height="14" fill="#2b74b0"/>
   <ellipse cx="0" cy="-6" rx="26" ry="9" fill="#5aa3dc"/>
   <path d="M-14 -6 h10 m-4 -3 l4 3 l-4 3 M14 -6 h-10 m4 -3 l-4 3 l4 3" stroke="#fff" stroke-width="1.8" fill="none"/>
  </g>${label?t(x,y+30*s,label,{a:'middle',fs:11}):''}`;
}
function sw(x,y,s=1,label){
  return `<g transform="translate(${x},${y}) scale(${s})">
   <path d="M-28 -6 L-18 -14 L28 -14 L18 -6 Z" fill="#6bb1e6"/><rect x="-28" y="-6" width="46" height="16" fill="#2b74b0"/>
   <path d="M18 -6 L28 -14 L28 2 L18 10 Z" fill="#1e5a8a"/>
   <path d="M-20 -10 h10 m-3 -2 l3 2 l-3 2 M8 -10 h-10 m3 -2 l-3 2 l3 2" stroke="#fff" stroke-width="1.4" fill="none"/>
  </g>${label?t(x,y+28*s,label,{a:'middle',fs:11}):''}`;
}
function pc(x,y,s=1,label){
  return `<g transform="translate(${x},${y}) scale(${s})">
   <rect x="-18" y="-18" width="36" height="25" rx="2" fill="#374151"/><rect x="-15" y="-15" width="30" height="19" fill="#7dd3fc"/>
   <rect x="-4" y="7" width="8" height="5" fill="#6b7280"/><rect x="-12" y="12" width="24" height="4" rx="1" fill="#4b5563"/>
  </g>${label?t(x,y+30*s,label,{a:'middle',fs:11}):''}`;
}
function bolt(x,y,s=1){return `<path transform="translate(${x},${y}) scale(${s})" d="M3 -14 L-8 2 L-1 2 L-4 14 L8 -3 L1 -3 Z" fill="#f59e0b" stroke="#92400e" stroke-width="1"/>`;}
function laptop(x,y){return `<g transform="translate(${x},${y})"><rect x="-15" y="-14" width="30" height="19" fill="#374151"/><rect x="-12" y="-11" width="24" height="13" fill="#7dd3fc"/><path d="M-19 5 h38 l-4 6 h-30 z" fill="#4b5563"/></g>`;}
function server(x,y){return `<g transform="translate(${x},${y})"><rect x="-11" y="-17" width="22" height="32" fill="#374151"/><rect x="-8" y="-13" width="16" height="3" fill="#9ca3af"/><rect x="-8" y="-7" width="16" height="3" fill="#9ca3af"/></g>`;}
function genIcon(x,y,kind){
  switch(kind){
    case 'router': return router(x,y,0.55);
    case 'switch': return sw(x,y,0.55);
    case 'pc': return pc(x,y,0.65);
    case 'bolt': return bolt(x,y,0.9);
    case 'laptop': return laptop(x,y);
    case 'server': return server(x,y);
    case 'hub': return `<rect x="${x-14}" y="${y-6}" width="28" height="12" fill="#64748b"/>`;
    case 'wifi': return `<path d="M${x-12} ${y} q12 -12 24 0 M${x-7} ${y+4} q7 -7 14 0" stroke="#2b74b0" stroke-width="2.5" fill="none"/><circle cx="${x}" cy="${y+8}" r="2.5" fill="#2b74b0"/>`;
    case 'shield': return `<path d="M${x} ${y-12} l11 4 v6 q0 9 -11 14 q-11 -5 -11 -14 v-6 z" fill="#ef4444"/>`;
    case 'cloud': return `<path d="M${x-12} ${y+6} q-6 0 -6 -6 q0 -6 7 -6 q2 -7 10 -6 q7 0 8 7 q6 0 6 6 q0 5 -6 5 z" fill="#94a3b8"/>`;
    case 'comp': return `<rect x="${x-12}" y="${y-9}" width="24" height="18" fill="#16a34a"/><rect x="${x-8}" y="${y-5}" width="16" height="3" fill="#bbf7d0"/>`;
    case 'misc': return `<circle cx="${x}" cy="${y}" r="11" fill="#a855f7"/>`;
    case 'multi': return `<circle cx="${x-5}" cy="${y}" r="8" fill="#0ea5e9"/><circle cx="${x+6}" cy="${y}" r="8" fill="#22c55e" opacity=".85"/>`;
    case 'home': return `<path d="M${x-12} ${y+10} v-10 l12 -10 l12 10 v10 z" fill="#f97316"/>`;
    case 'iot': return `<circle cx="${x}" cy="${y}" r="10" fill="none" stroke="#14b8a6" stroke-width="3"/><circle cx="${x}" cy="${y}" r="3" fill="#14b8a6"/>`;
    case 'cable': return `<line x1="${x-14}" y1="${y+10}" x2="${x+14}" y2="${y-10}" stroke="#111" stroke-width="2.5"/>`;
    case 'cableD': return `<line x1="${x-14}" y1="${y+10}" x2="${x+14}" y2="${y-10}" stroke="#111" stroke-width="2.5" stroke-dasharray="4 3"/>`;
    case 'console': return `<path d="M${x-14} ${y+8} q14 -22 28 -16" stroke="#38bdf8" stroke-width="2.5" fill="none"/>`;
    case 'fiber': return `<line x1="${x-14}" y1="${y+10}" x2="${x+14}" y2="${y-10}" stroke="#f97316" stroke-width="2.5"/>`;
    case 'serial': return `<path d="M${x-14} ${y+10} l10 -8 l6 4 l12 -14" stroke="#dc2626" stroke-width="2.5" fill="none"/>`;
    default: return `<rect x="${x-11}" y="${y-11}" width="22" height="22" fill="#cbd5e1"/>`;
  }
}

// Ana pencere (temsili Packet Tracer 8.x düzeni). viewBox 900x560
const CATS = [['Network Devices','router'],['End Devices','pc'],['Components','comp'],['Connections','bolt'],['Miscellaneous','misc'],['Multiuser','multi']];
const SUBS = {
  net: [['Routers','router'],['Switches','switch'],['Hubs','hub'],['Wireless Devices','wifi'],['Security','shield'],['WAN Emulation','cloud']],
  end: [['End Devices','pc'],['Home','home'],['Smart City','iot'],['Industrial','comp'],['Power Grid','misc'],['Boundary','cloud']],
  con: [['Connections','bolt']]
};
const LISTS = {
  routers: [['4331','router'],['4321','router'],['1941','router'],['2901','router'],['2911','router'],['819IOX','router'],['829','router'],['1240','router']],
  switches: [['2960','switch'],['3560-24PS','switch'],['3650-24PS','switch'],['2950-24','switch'],['2950T','switch'],['Bridge-PT','switch']],
  end: [['PC','pc'],['Laptop','laptop'],['Server','server'],['Printer','comp'],['Phone','misc'],['TV','misc'],['Tablet','misc'],['Smartphone','misc']],
  con: [['Automatic','bolt'],['Console','console'],['Copper Straight-Through','cable'],['Copper Cross-Over','cableD'],['Fiber','fiber'],['Phone','cableD'],['Coaxial','fiber'],['Serial DCE','serial']]
};
// konum hesaplayıcılar (işaret koymak için)
const catPos = i => [22+i*40, 455];
const subPos = i => [22+i*40, 503];
const listPos = i => [300+i*58, 478];

function mainWin(o){
  const cat=o.cat??0, subSet=SUBS[o.subSet||'net'], sub=o.sub??0, list=LISTS[o.list||'routers'], sel=o.sel??-1;
  let s = `<svg viewBox="0 0 900 560" xmlns="http://www.w3.org/2000/svg">${DEFS}`;
  // başlık + menü + araç
  s += `<rect width="900" height="560" fill="#e5e7eb"/>`;
  s += `<rect width="900" height="26" fill="#1f3b57"/>${t(12,17,'Cisco Packet Tracer - '+(o.file||'Untitled'),{fill:'#fff',fs:11})}`;
  s += `<g>${['×','□','–'].map((c,i)=>t(885-i*24,18,c,{fill:'#fff',fs:13,a:'middle'})).join('')}</g>`;
  s += `<rect y="26" width="900" height="22" fill="#f3f4f6"/>`;
  ['File','Edit','Options','View','Tools','Extensions','Window','Help'].forEach((m,i)=>{ s+=t(12+i*62,41,m,{fs:11}); });
  s += `<rect y="48" width="900" height="30" fill="#e5e7eb" stroke="#cbd5e1"/>`;
  for(let i=0;i<16;i++){ s+=`<rect x="${10+i*28}" y="53" width="20" height="20" rx="3" fill="#cbd5e1"/>`; }
  s += `<rect y="78" width="900" height="22" fill="#d1d5db"/><rect x="6" y="80" width="70" height="20" fill="#fff"/>${t(41,94,'Logical',{a:'middle',fs:11,fw:'bold'})}${t(110,94,'Physical',{a:'middle',fs:11,fill:'#555'})}`;
  // sağ araç çubuğu
  s += `<rect x="864" y="100" width="36" height="330" fill="#f3f4f6" stroke="#cbd5e1"/>`;
  const rt = ['select','inspect','delete','resize','note','draw','pdu','cpdu'];
  rt.forEach((k,i)=>{ const yy=112+i*36; s+=`<rect x="870" y="${yy}" width="24" height="24" rx="3" fill="#e2e8f0" stroke="#94a3b8"/>`;
    if(k==='pdu') s+=`<rect x="874" y="${yy+7}" width="16" height="11" fill="#fde68a" stroke="#a16207"/><path d="M874 ${yy+7} l8 6 l8 -6" stroke="#a16207" fill="none"/>`;
    if(k==='cpdu') s+=`<rect x="874" y="${yy+7}" width="16" height="11" fill="#fff" stroke="#a16207"/><path d="M874 ${yy+7} l8 6 l8 -6" stroke="#a16207" fill="none"/>`;
    if(k==='select') s+=`<path d="M877 ${yy+4} l0 15 l4 -4 l3 6 l2 -1 l-3 -6 l5 0 z" fill="#111"/>`;
    if(k==='delete') s+=`${t(882,yy+17,'✕',{a:'middle',fs:13,fill:'#dc2626'})}`;
  });
  // çalışma alanı
  s += `<rect x="0" y="100" width="864" height="330" fill="url(#grid)"/><rect x="0" y="100" width="864" height="330" fill="none" stroke="#cbd5e1"/>`;
  s += o.ws||'';
  // alt panel
  s += `<rect x="0" y="430" width="900" height="130" fill="#d9dee5" stroke="#9ca3af"/>`;
  s += `<rect x="4" y="434" width="250" height="122" fill="#e8ecf1" stroke="#b6bec9"/>`;
  CATS.forEach((c,i)=>{ const [x,y]=catPos(i); s+=`<rect x="${x-17}" y="${y-17}" width="34" height="34" rx="4" fill="${i===cat?'#bfdbfe':'#f8fafc'}" stroke="${i===cat?'#2563eb':'#cbd5e1'}"/>`+genIcon(x,y,c[1]); });
  subSet.forEach((c,i)=>{ const [x,y]=subPos(i); s+=`<rect x="${x-17}" y="${y-17}" width="34" height="34" rx="4" fill="${i===sub?'#bfdbfe':'#f8fafc'}" stroke="${i===sub?'#2563eb':'#cbd5e1'}"/>`+genIcon(x,y,c[1]); });
  s += t(129,548,subSet[sub][0],{a:'middle',fs:10.5,fw:'bold'});
  s += `<rect x="262" y="434" width="494" height="122" fill="#f8fafc" stroke="#b6bec9"/>`;
  list.forEach((c,i)=>{ const [x,y]=listPos(i); s+=`<rect x="${x-24}" y="${y-24}" width="48" height="46" rx="4" fill="${i===sel?'#bfdbfe':'#fff'}" stroke="${i===sel?'#2563eb':'#e2e8f0'}"/>`+genIcon(x,y-3,c[1]);
    const lab=c[0].length>11?c[0].slice(0,10)+'…':c[0]; s+=t(x,y+36,lab,{a:'middle',fs:9.5}); });
  if(o.hint) s+=t(509,548,o.hint,{a:'middle',fs:10,fill:'#334155'});
  // gerçek zaman / simülasyon
  s += `<rect x="762" y="434" width="134" height="122" fill="#e8ecf1" stroke="#b6bec9"/>`;
  s += `${t(829,456,o.sim?'00:00:12':'00:01:27',{a:'middle',fs:10})}`;
  s += `<rect x="772" y="500" width="56" height="44" fill="${o.sim?'#fff':'#bfdbfe'}" stroke="#94a3b8"/>${t(800,526,'Realtime',{a:'middle',fs:9.5})}`;
  s += `<rect x="832" y="500" width="58" height="44" fill="${o.sim?'#bfdbfe':'#fff'}" stroke="#94a3b8"/>${t(861,526,'Simulation',{a:'middle',fs:9.5})}`;
  s += o.marks||'';
  return s+'</svg>';
}

// Diyalog penceresi (cihaz penceresi). viewBox 900x560
function dialog(title,tabs,active,body,marks=''){
  let s = `<svg viewBox="0 0 900 560" xmlns="http://www.w3.org/2000/svg">${DEFS}<rect width="900" height="560" fill="#cbd5e1"/>`;
  s += `<rect x="40" y="16" width="820" height="530" fill="#f3f4f6" stroke="#64748b"/>`;
  s += `<rect x="40" y="16" width="820" height="26" fill="#1f3b57"/>${t(54,33,title,{fill:'#fff',fs:11.5})}${t(845,34,'×',{fill:'#fff',fs:15,a:'middle'})}`;
  let x=50; s+=`<g>`;
  tabs.forEach((tb,i)=>{ const w=tb.length*7.2+24; s+=`<rect x="${x}" y="50" width="${w}" height="24" fill="${i===active?'#fff':'#e5e7eb'}" stroke="#94a3b8"/>${t(x+w/2,66,tb,{a:'middle',fs:11,fw:i===active?'bold':'normal'})}`; tabPos[tb]=[x+w/2,62,w]; x+=w+2; });
  s+=`</g><rect x="50" y="74" width="800" height="440" fill="#fff" stroke="#94a3b8"/>`;
  s += body;
  s += `<rect x="50" y="518" width="16" height="16" fill="#fff" stroke="#64748b"/>${t(72,531,'Top',{fs:11})}`;
  return s + marks + '</svg>';
}
const tabPos = {};
function field(x,y,label,val,w=230){ return t(x,y+15,label,{fs:11.5})+`<rect x="${x+150}" y="${y}" width="${w}" height="22" fill="#fff" stroke="#94a3b8"/>`+t(x+156,y+15,val,{fs:11.5,ff:'DejaVu Sans Mono, monospace'}); }

function fill(id,svg){ document.getElementById(id).innerHTML = svg; }
