// ---------- yardımcılar ----------
const MONO='DejaVu Sans Mono, monospace', CW=6.33, LH=18.6;
function popup(x,y,items,selIdx){
  return `<rect x="${x}" y="${y}" width="190" height="${items.length*23.5+2}" fill="#fff" stroke="#475569"/>` +
    items.map((p,i)=>`<rect x="${x+1}" y="${y+1+i*23.5}" width="188" height="23" fill="${i===selIdx?'#bfdbfe':'#fff'}"/>`+t(x+10,y+17+i*23.5,p,{fs:11})).join('');
}
function consoleCable(a,b){ return `<path d="M${a[0]} ${a[1]} Q ${(a[0]+b[0])/2-120} ${(a[1]+b[1])/2} ${b[0]} ${b[1]}" stroke="#38bdf8" stroke-width="2.5" fill="none"/>`; }
// Terminal/CLI tarzı pencere. marks: [{l:satır, n:'1', from:başlangıç sütunu, len:uzunluk}]
function term(o){
  const tabs=o.tabs, X=70, Y0=126;
  let b='';
  if(o.inner){ b+=`<rect x="64" y="82" width="772" height="426" fill="#000" stroke="#64748b"/><rect x="64" y="82" width="772" height="22" fill="#e2e8f0"/>`+t(76,98,o.inner,{fs:11.5,fw:'bold'})+t(824,98,'X',{fs:11.5,a:'middle'}); }
  else { b+=t(450,96,'IOS Command Line Interface',{a:'middle',fs:12,fw:'bold'})+`<rect x="60" y="106" width="780" height="400" fill="#000"/>`; }
  const y0 = o.inner?122:Y0; const lh = Math.min(LH, 372/o.lines.length);
  o.lines.forEach((l,i)=>{ b+=t(X,y0+i*lh,l.replace(/ /g,'\u00a0'),{fs:10.5,fill:o.dim&&o.dim.includes(i)?'#94a3b8':'#e5e7eb',ff:MONO}); });
  let svg=dialog(o.title,tabs,tabs.indexOf(o.active),b);
  let m='';
  if(o.tabMark){ const tp=tabPos[o.active]; m+=mark(tp[0],tp[1],18,o.tabMark,{rx:tp[2]/2+8,ry:15}); }
  (o.marks||[]).forEach(k=>{ const line=o.lines[k.l]; const from=k.from||0; const len=k.len||(line.length-from);
    const cx=X+(from+len/2)*CW, rx=len*CW/2+16; m+=mark(cx,y0+k.l*lh-4,11,k.n,{rx,ry:Math.min(12,lh*0.62),side:true}); });
  return svg.replace('</svg>', m+'</svg>');
}
const RT=['Physical','Config','CLI','Attributes'];
const PT=['Physical','Config','Desktop','Programming','Attributes'];
function desktop(name, selIdx, n2){
  const apps=['IP Configuration','Dial-up','Terminal','Command Prompt','Web Browser','PC Wireless','VPN','Traffic Generator','MIB Browser','Cisco IP Communicator','Email','PPPoE Dialer','Text Editor','Firewall','IPv6 Firewall','Bluetooth'];
  let b='';
  apps.forEach((a,i)=>{ const cx=130+(i%6)*125, cy=130+Math.floor(i/6)*120;
    b+=`<rect x="${cx-28}" y="${cy-28}" width="56" height="56" rx="8" fill="${i===selIdx?'#dbeafe':'#f1f5f9'}" stroke="#94a3b8"/>`;
    if(i===0) b+=t(cx,cy+6,'IP',{a:'middle',fs:18,fw:'bold',fill:'#1d4ed8'});
    else if(i===2) b+=`<rect x="${cx-18}" y="${cy-14}" width="36" height="28" rx="3" fill="#1e3a5f"/>`+t(cx,cy+5,'>_',{a:'middle',fs:13,fill:'#7dd3fc',ff:MONO});
    else if(i===3) b+=`<rect x="${cx-18}" y="${cy-14}" width="36" height="28" fill="#000"/>`+t(cx-13,cy+4,'C:\\>',{fs:9,fill:'#fff',ff:MONO});
    else b+=`<circle cx="${cx}" cy="${cy}" r="14" fill="#cbd5e1"/>`;
    b+=t(cx,cy+46,a.length>18?a.slice(0,17)+'…':a,{a:'middle',fs:10.5});
  });
  const svg=dialog(name,PT,2,b); const tp=tabPos['Desktop'];
  const cx=130+(selIdx%6)*125, cy=130+Math.floor(selIdx/6)*120;
  return svg.replace('</svg>', mark(tp[0],tp[1],18,'1',{rx:40,ry:16}) + mark(cx,cy+12,44,n2,{rx:62,ry:48}) + '</svg>');
}

// IP Configuration penceresi. c: {dhcp, ip, mask, gw, dns, msg, msgColor}
function ipConf(name, c, marks=''){
  let b=`<rect x="80" y="86" width="740" height="410" fill="#fff" stroke="#64748b"/><rect x="80" y="86" width="740" height="24" fill="#e2e8f0"/>`+t(92,103,'IP Configuration',{fs:11.5,fw:'bold'})+t(808,103,'X',{fs:11.5,a:'middle'});
  b+=t(100,138,'Interface',{fs:11.5})+`<rect x="250" y="124" width="200" height="22" fill="#fff" stroke="#94a3b8"/>`+t(258,139,'FastEthernet0  ▾',{fs:11.5});
  b+=`<rect x="96" y="160" width="708" height="190" fill="none" stroke="#cbd5e1"/>`+t(104,176,'IP Configuration',{fs:11,fw:'bold'});
  b+=`<circle cx="114" cy="196" r="7" fill="#fff" stroke="#334155"/>`+(c.dhcp?`<circle cx="114" cy="196" r="3.5" fill="#111"/>`:'')+t(128,200,'DHCP',{fs:11.5});
  b+=`<circle cx="214" cy="196" r="7" fill="#fff" stroke="#334155"/>`+(c.dhcp?'':`<circle cx="214" cy="196" r="3.5" fill="#111"/>`)+t(228,200,'Static',{fs:11.5});
  if(c.msg) b+=t(520,200,c.msg,{fs:11.5,fill:c.msgColor||'#15803d',fw:'bold'});
  const f=(y,l,v)=>{ let s=field(104,y,l,v,300); if(c.dhcp) s=s.replace('fill="#fff" stroke="#94a3b8"','fill="#f1f5f9" stroke="#cbd5e1"'); return s; };
  b+=f(214,'IPv4 Address',c.ip)+f(246,'Subnet Mask',c.mask)+f(278,'Default Gateway',c.gw)+f(310,'DNS Server',c.dns);
  return dialog(name,PT,2,b).replace('</svg>', marks+'</svg>');
}
