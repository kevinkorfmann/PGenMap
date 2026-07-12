"""HTML templates for the PGenMap dashboard. Two pages share one CSS block:
  MAIN_TEMPLATE       -> docs/index.html      (figures, methods, topics, network, pivotal)
  SCIENTISTS_TEMPLATE -> docs/scientists.html (the searchable researcher directory)
Each has a /*__DATA__*/ placeholder that build_dashboard.py fills with JSON.
Vanilla JS only: SVG for time-series, Canvas for the collaboration graph."""

CSS = r"""
  :root{
    --ink:#0d1417; --surface:#141d21; --surface2:#1b262b; --line:#26343a;
    --text:#e9f1f2; --muted:#8fa5ab; --faint:#5f767d;
    --teal:#37c9b8; --amber:#e0a458; --grid:#202c31;
  }
  @media (prefers-color-scheme: light){
    :root{ --ink:#f5f7f6; --surface:#ffffff; --surface2:#eef2f1; --line:#dbe3e1;
      --text:#132025; --muted:#4d6169; --faint:#82969d; --teal:#0f8f80; --amber:#a9680c; --grid:#e6ecea; }
  }
  :root[data-theme="dark"]{ --ink:#0d1417; --surface:#141d21; --surface2:#1b262b; --line:#26343a;
    --text:#e9f1f2; --muted:#8fa5ab; --faint:#5f767d; --teal:#37c9b8; --amber:#e0a458; --grid:#202c31; }
  :root[data-theme="light"]{ --ink:#f5f7f6; --surface:#ffffff; --surface2:#eef2f1; --line:#dbe3e1;
    --text:#132025; --muted:#4d6169; --faint:#82969d; --teal:#0f8f80; --amber:#a9680c; --grid:#e6ecea; }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--ink);color:var(--text);
    font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1080px;margin:0 auto;padding:0 1.3rem;}
  a{color:var(--teal);text-decoration:none}
  a:hover{text-decoration:underline}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  header{border-bottom:1px solid var(--line);background:linear-gradient(180deg,var(--surface),var(--ink));}
  .head{display:flex;flex-wrap:wrap;align-items:flex-end;gap:1rem 1.4rem;padding:2.4rem 0 1.6rem;}
  .eyebrow{font-family:ui-monospace,monospace;font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--teal);margin:0 0 .5rem;}
  h1{font-family:ui-serif,Georgia,serif;font-weight:600;font-size:clamp(1.7rem,4vw,2.6rem);line-height:1.06;margin:0;letter-spacing:-.01em;text-wrap:balance;}
  h1 em{font-style:italic;color:var(--teal)}
  .head .grow{flex:1 1 320px}
  .navlink{display:inline-flex;align-items:center;gap:.4rem;background:var(--surface2);border:1px solid var(--line);
    border-radius:999px;padding:.5rem 1rem;font-size:.9rem;color:var(--text);font-weight:500}
  .navlink:hover{border-color:var(--teal);text-decoration:none}
  .pill{display:inline-flex;align-items:center;gap:.5rem;background:var(--surface2);border:1px solid var(--line);border-radius:999px;padding:.4rem .8rem;font-size:.8rem;color:var(--muted)}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--amber)}
  .dot.live{animation:pulse 2s infinite}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(224,164,88,.5)}70%{box-shadow:0 0 0 8px rgba(224,164,88,0)}100%{box-shadow:0 0 0 0 rgba(224,164,88,0)}}
  @media (prefers-reduced-motion: reduce){.dot.live{animation:none}}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:1.4rem 0 2rem;}
  .tile{background:var(--surface);padding:1rem 1.1rem}
  .tile .k{font-family:ui-monospace,monospace;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin:0 0 .35rem}
  .tile .v{font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums;color:var(--text)}
  .tile .v small{font-size:.8rem;color:var(--muted);font-weight:400}
  section{padding:2.2rem 0;border-top:1px solid var(--line)}
  .sec-h{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-bottom:.3rem}
  h2{font-family:ui-serif,Georgia,serif;font-weight:600;font-size:1.5rem;margin:0;letter-spacing:-.01em}
  .sub{color:var(--muted);margin:.2rem 0 1.3rem;max-width:70ch}
  .building{background:var(--surface);border:1px dashed var(--line);border-radius:10px;padding:1.4rem;color:var(--faint);font-size:.9rem;display:flex;align-items:center;gap:.6rem}
  .card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1.1rem}
  .chart-wrap{overflow-x:auto}
  svg{display:block;max-width:100%}
  .legend{display:flex;flex-wrap:wrap;gap:.4rem .8rem;margin-top:.8rem}
  .lg{display:inline-flex;align-items:center;gap:.4rem;font-size:.82rem;color:var(--muted);cursor:pointer;border:1px solid transparent;border-radius:6px;padding:.15rem .35rem}
  .lg:hover{border-color:var(--line)}
  .lg.off{opacity:.35}
  .sw{width:11px;height:11px;border-radius:3px;flex:none}
  .btns{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem}
  .btn{background:var(--surface2);border:1px solid var(--line);color:var(--muted);border-radius:999px;padding:.32rem .8rem;font-size:.82rem;cursor:pointer;font-family:inherit}
  .btn.active{background:var(--teal);color:#04110f;border-color:var(--teal);font-weight:600}
  .gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem}
  .gfig{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}
  .gfig a{display:block;background:#fff}
  .gfig img{width:100%;display:block}
  .gfig .cap{padding:.7rem .9rem;font-size:.85rem;color:var(--muted)}
  .gfig .cap b{color:var(--text);font-weight:600}
  .gfig.wide{grid-column:1/-1}
  .tlist{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:.7rem;margin-top:1rem}
  .titem{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.75rem .9rem}
  .titem .tl{font-weight:600;font-size:.92rem;margin:0 0 .25rem;display:flex;justify-content:space-between;gap:.5rem}
  .trend{font-size:.72rem;font-family:ui-monospace,monospace;padding:.05rem .35rem;border-radius:5px}
  .trend.rising{color:var(--teal);background:color-mix(in srgb,var(--teal) 15%,transparent)}
  .trend.declining{color:var(--amber);background:color-mix(in srgb,var(--amber) 15%,transparent)}
  .trend.stable{color:var(--faint)}
  .titem .kw{font-size:.78rem;color:var(--muted);margin:0}
  #netcanvas{width:100%;height:520px;display:block;border-radius:12px;background:var(--surface);border:1px solid var(--line);touch-action:none}
  #nettip{position:fixed;pointer-events:none;background:var(--surface2);border:1px solid var(--line);border-radius:8px;padding:.45rem .6rem;font-size:.82rem;color:var(--text);display:none;z-index:9;max-width:240px;box-shadow:0 6px 24px rgba(0,0,0,.3)}
  .search{width:100%;background:var(--surface);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:.7rem .9rem;font-size:.95rem;font-family:inherit;margin-bottom:1rem}
  .search:focus{outline:2px solid var(--teal);outline-offset:1px}
  .people{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.7rem}
  .person{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.8rem .95rem}
  .person .nm{font-weight:600;display:flex;align-items:center;gap:.4rem}
  .person .nm .seed{font-size:.62rem;background:var(--teal);color:#04110f;border-radius:4px;padding:.03rem .3rem;font-family:ui-monospace,monospace}
  .person .in{color:var(--muted);font-size:.83rem;margin:.15rem 0 .4rem}
  .person .meta{font-size:.76rem;color:var(--faint);font-family:ui-monospace,monospace;display:flex;gap:.8rem;flex-wrap:wrap}
  .chips{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.5rem}
  .chip{font-size:.72rem;background:var(--surface2);border:1px solid var(--line);border-radius:999px;padding:.1rem .5rem;color:var(--muted)}
  .more{color:var(--faint);text-align:center;margin-top:1rem;font-size:.85rem}
  table{width:100%;border-collapse:collapse;font-size:.86rem}
  th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
  th{font-family:ui-monospace,monospace;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
  td .num{font-variant-numeric:tabular-nums;color:var(--muted)}
  footer{border-top:1px solid var(--line);padding:2rem 0 3rem;color:var(--faint);font-size:.85rem;display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}
  .axis{font-size:10px;fill:var(--faint);font-family:ui-monospace,monospace}
  .gridline{stroke:var(--grid);stroke-width:1}
  .disclaimer{border-radius:12px;padding:1rem 1.15rem;margin:1.4rem 0 0;display:flex;gap:.85rem;align-items:flex-start;font-size:.9rem;line-height:1.5}
  .disclaimer.warn{background:color-mix(in srgb,var(--amber) 14%,var(--surface));border:1px solid color-mix(in srgb,var(--amber) 55%,var(--line));color:var(--text)}
  .disclaimer.note{background:var(--surface);border:1px solid var(--line);color:var(--muted);font-size:.82rem}
  .disclaimer .ic{font-size:1.15rem;line-height:1;flex:none}
  .disclaimer b{color:var(--amber)}
  .disclaimer.note b{color:var(--muted)}
  .atlas-shell{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 18px 48px color-mix(in srgb,var(--ink) 22%,transparent)}
  .atlas-toolbar{display:flex;flex-wrap:wrap;gap:.55rem;align-items:center;padding:.8rem;border-bottom:1px solid var(--line);background:var(--surface2)}
  .atlas-toolbar select,.atlas-toolbar input{background:var(--surface);border:1px solid var(--line);border-radius:8px;color:var(--text);font:inherit;padding:.42rem .58rem;min-width:150px}
  .atlas-toolbar input{flex:1 1 190px}.atlas-toolbar label{font-size:.76rem;color:var(--muted);display:flex;gap:.35rem;align-items:center}
  #atlascanvas{width:100%;height:min(68vw,620px);min-height:420px;display:block;touch-action:none;cursor:grab;background:radial-gradient(circle at 50% 45%,color-mix(in srgb,var(--teal) 8%,transparent),transparent 54%)}
  .atlas-foot{padding:.65rem .9rem;color:var(--muted);font-size:.78rem;display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}
  .atlas-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;align-items:stretch}.atlas-detail{border-left:1px solid var(--line);padding:1rem;max-height:620px;overflow:auto;background:var(--surface)}
  .atlas-detail h3{font-family:ui-serif,Georgia,serif;line-height:1.15;margin:.1rem 0 .5rem;font-size:1.12rem}.atlas-detail p{font-size:.85rem;color:var(--muted)}
  .score{font:600 2rem ui-monospace,monospace;color:var(--teal);line-height:1}.score small{font-size:.72rem;color:var(--muted);font-weight:400}.meters{display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;margin:1rem 0}.meter{font-size:.7rem;color:var(--faint)}.meter i{display:block;height:4px;background:var(--line);margin-top:.2rem;border-radius:4px;overflow:hidden}.meter b{display:block;height:100%;background:var(--teal)}
  .opps{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:.75rem}.opp{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:.9rem;cursor:pointer}.opp:hover{border-color:var(--teal)}.opp h3{font-size:.95rem;margin:0 0 .35rem}.opp p{font-size:.78rem;color:var(--muted);margin:.3rem 0}.opp .tag{font:.68rem ui-monospace,monospace;color:var(--amber);text-transform:uppercase;letter-spacing:.08em}
  .primer{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;margin:1.15rem 0 0}.primer .card{padding:1rem}.primer h3{font-size:.98rem;margin:.05rem 0 .4rem}.primer p{font-size:.86rem;color:var(--muted);margin:0}.primer .num{font:600 .72rem ui-monospace,monospace;color:var(--teal);letter-spacing:.09em}
  .case-studies{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:.8rem;margin-top:1rem}.case{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1rem}.case h3{font-family:ui-serif,Georgia,serif;font-size:1.08rem;margin:.1rem 0 .4rem}.case p{font-size:.85rem;color:var(--muted);margin:.3rem 0 .75rem}.case a{display:inline-block;background:var(--teal);border:0;border-radius:999px;padding:.4rem .75rem;color:#04110f;font:600 .78rem system-ui,sans-serif;cursor:pointer}.case a:hover{filter:brightness(1.08);text-decoration:none}
  @media(max-width:760px){.atlas-layout{grid-template-columns:1fr}.atlas-detail{border-left:0;border-top:1px solid var(--line);max-height:none}#atlascanvas{min-height:360px}.primer{grid-template-columns:1fr}}
"""

# --- shared JS preamble (helpers used by every section) ---------------------
PREAMBLE_JS = r"""
const DATA = JSON.parse(document.getElementById('data').textContent);
const PAL = ['#37c9b8','#e0a458','#6ea8fe','#e86a92','#9d7be0','#8bc34a','#f2c14e','#4dd0e1','#f4845f','#a3b18a','#c78ee0','#5fb3a3','#d98880','#7fb3d5'];
const $ = s => document.querySelector(s);
const el = (t,c,h)=>{const e=document.createElement(t); if(c)e.className=c; if(h!=null)e.innerHTML=h; return e;};
const fmt = n => n==null?'—':n.toLocaleString();
function css(v){return getComputedStyle(document.body).getPropertyValue(v).trim();}
function building(id,msg){ const n=$(id); if(!n)return; n.innerHTML=''; n.appendChild(el('div','building','<span class="dot live"></span>'+msg)); }
function svgEl(t,attrs){const e=document.createElementNS('http://www.w3.org/2000/svg',t); for(const k in attrs)e.setAttribute(k,attrs[k]); return e;}
function lineChart(container, years, series, opts){
  opts=opts||{}; container.innerHTML='';
  const W=Math.max(680, years.length*16), H=opts.h||330, P={l:44,r:16,t:14,b:26};
  const iw=W-P.l-P.r, ih=H-P.t-P.b;
  let maxY=opts.max|| Math.max(...series.flatMap(s=>s.vals.filter(v=>v!=null)),0.001); maxY*=1.08;
  const x=i=>P.l+ iw*(i/(years.length-1)); const y=v=>P.t+ ih*(1-(v/maxY));
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img'});
  const yt=(opts.yticks||4);
  for(let i=0;i<=yt;i++){const v=maxY*i/yt; const yy=y(v);
    svg.appendChild(svgEl('line',{x1:P.l,x2:W-P.r,y1:yy,y2:yy,class:'gridline'}));
    const lab=opts.pct?(v*100).toFixed(v<0.02?1:0)+'%':Math.round(v);
    const tx=svgEl('text',{x:P.l-6,y:yy+3,'text-anchor':'end',class:'axis'}); tx.textContent=lab; svg.appendChild(tx);}
  years.forEach((yr,i)=>{ if(yr%5===0){ const tx=svgEl('text',{x:x(i),y:H-8,'text-anchor':'middle',class:'axis'}); tx.textContent=yr; svg.appendChild(tx);} });
  series.forEach(s=>{ if(s.off) return; let d='';
    s.vals.forEach((v,i)=>{ if(v==null)return; d+=(d?'L':'M')+x(i).toFixed(1)+' '+y(v).toFixed(1)+' ';});
    svg.appendChild(svgEl('path',{d,fill:'none',stroke:s.color,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round',opacity:.95}));
    let li=s.vals.length-1; while(li>=0&&s.vals[li]==null)li--;
    if(li>=0) svg.appendChild(svgEl('circle',{cx:x(li),cy:y(s.vals[li]),r:2.6,fill:s.color})); });
  container.appendChild(svg);
}
"""

STATUS_JS = r"""
(function(){
  const stage=DATA.stage, m=DATA.meta||{};
  const label={seed:'initializing',universe:'universe discovered — harvesting corpus',corpus:'corpus harvested — running analyses',full:'analysis complete'}[stage]||'building…';
  const st=$('#statustxt'); if(st)st.textContent=label;
  if(stage==='full'){const d=document.querySelector('#statuspill .dot'); if(d)d.classList.remove('live');}
  const dz=$('#disclaimer');
  if(dz){ if(stage!=='full'){ dz.className='disclaimer warn';
      dz.innerHTML='<span class="ic">⚠️</span><div><b>Work in progress — numbers are provisional.</b> The corpus is still being harvested and per-researcher counts are being recomputed. Some counts shown now are preliminary and undercounted for authors whose names carry diacritics or appear as initials (a known limit of name-based Crossref attribution). Figures update as the pipeline completes.</div>';
    } else { dz.className='disclaimer note';
      dz.innerHTML='<span class="ic">ℹ️</span><div><b>About the data.</b> Built from <a href="https://www.crossref.org">Crossref</a> (open metadata). Author identity is inferred from a normalized name key with venue/keyword relevance filtering — disambiguation and coverage are heuristic, so counts for authors with name variants or common names may be under- or over-stated, and abstract coverage is partial. Treat figures as field-scale signal, not exact bibliometrics.</div>'; } }
  const box=$('#tiles'); if(!box)return;
  const tiles=[['Researchers',fmt(m.researchers)],
    ['Publications',m.works!=null?fmt(m.works):'<small>harvesting…</small>'],
    ['With abstracts',m.works_with_abstract!=null?fmt(m.works_with_abstract):'<small>—</small>'],
    ['Span',(m.year_min?`${m.year_min}–${m.year_max}`:'mapped period')],
    ['Topics',(DATA.topics&&DATA.topics.length)?fmt(DATA.topics.length):'<small>—</small>'],
    ['Schools',(m.communities)?fmt(m.communities):'<small>—</small>']];
  tiles.forEach(([k,v])=>{const t=el('div','tile'); t.appendChild(el('p','k',k)); t.appendChild(el('p','v',v)); box.appendChild(t);});
})();
"""

FIGURES_JS = r"""
(function(){
  const body=$('#figures-body'); if(!body)return;
  if(!DATA.figures||!DATA.figures.length){ building('#figures-body','Figures render after the analysis stage.'); return; }
  body.innerHTML=''; const g=el('div','gallery'); body.appendChild(g);
  DATA.figures.forEach(f=>{ const c=el('div','gfig'+(f.wide?' wide':''));
    c.innerHTML=`<a href="figures/${f.file}" target="_blank" rel="noopener"><img loading="lazy" alt="${f.title}" src="figures/${f.file}"></a><div class="cap"><b>${f.title}.</b> ${f.caption||''}</div>`;
    g.appendChild(c); });
})();
"""

ATLAS_JS = r"""
(function(){
  const host=$('#atlas-body'), opp=$('#opportunity-body'); if(!host)return;
  fetch('data/atlas.json').then(r=>r.ok?r.json():Promise.reject()).then(atlas=>{
    host.innerHTML=`<div class="atlas-shell"><div class="atlas-toolbar"><label>Topic <select id="atlas-topic"><option value="">All themes</option></select></label><label>From <select id="atlas-year"></select></label><input id="atlas-search" placeholder="Find a topic or paper…" aria-label="Find a topic or paper"></div><div class="atlas-layout"><div><canvas id="atlascanvas" aria-label="Interactive semantic map of population genetics papers"></canvas><div class="atlas-foot"><span id="atlas-count"></span><span>Scroll to zoom · drag to pan · click a point for evidence</span></div></div><aside id="atlas-detail" class="atlas-detail"><h3>Explore the field</h3><p>Each point is a paper. Nearby papers use similar language; colours show macro themes. Zoom in to resolve individual papers.</p></aside></div></div>`;
    const cv=$('#atlascanvas'), detail=$('#atlas-detail'), topic=$('#atlas-topic'), year=$('#atlas-year'), search=$('#atlas-search'), count=$('#atlas-count');
    const macro=new Map(atlas.macros.map(m=>[m.id,m.label])), topics=new Map(atlas.topics.map(t=>[t.id,t]));
    atlas.macros.filter(m=>m.id>=0).forEach(m=>topic.add(new Option(m.label.replace(/^[-\d_]+/,'').slice(0,54),m.id)));
    const years=[...new Set(atlas.points.map(p=>p.year).filter(Boolean))].sort((a,b)=>a-b); year.add(new Option('All years','')); years.forEach(y=>year.add(new Option(y,y)));
    const q=new URLSearchParams(location.search); topic.value=q.get('topic')||''; year.value=q.get('year')||'';
    let view={x:0,y:0,s:1}, drag, W=0,H=0,DPR=1, filtered=[];
    const color=id=>PAL[Math.abs(Number(id)||0)%PAL.length]; const screen=p=>({x:(p.x-.5)*Math.min(W,H)*.92*view.s+W/2+view.x,y:(p.y-.5)*Math.min(W,H)*.92*view.s+H/2+view.y});
    function syncUrl(){const u=new URL(location);topic.value?u.searchParams.set('topic',topic.value):u.searchParams.delete('topic');year.value?u.searchParams.set('year',year.value):u.searchParams.delete('year');history.replaceState({},'',u);}
    function filter(){const term=search.value.trim().toLowerCase(); filtered=atlas.points.filter(p=>(!topic.value||String(p.macro)===topic.value)&&(!year.value||String(p.year)===year.value)&&(!term||p.title.toLowerCase().includes(term)||(topics.get(p.fine)?.label||'').toLowerCase().includes(term)||p.methods.join(' ').toLowerCase().includes(term))); count.textContent=`${filtered.length.toLocaleString()} of ${atlas.points.length.toLocaleString()} papers · ${atlas.coverage.abstracts.toLocaleString()} with abstracts`; syncUrl();draw();}
    function draw(){const c=cv.getContext('2d');c.setTransform(DPR,0,0,DPR,0,0);c.clearRect(0,0,W,H); const density=view.s<1.25;
      if(density){const bins=new Map;filtered.forEach(p=>{const a=screen(p),x=Math.floor(a.x/8),y=Math.floor(a.y/8);if(x<0||y<0||x>W/8||y>H/8)return;const k=x+','+y;bins.set(k,(bins.get(k)||0)+1)});bins.forEach((n,k)=>{const [x,y]=k.split(',').map(Number);c.fillStyle='rgba(55,201,184,'+Math.min(.8,.12+Math.log(n)/5)+')';c.fillRect(x*8,y*8,7,7)});return}
      filtered.forEach(p=>{const a=screen(p);if(a.x<-3||a.y<-3||a.x>W+3||a.y>H+3)return;c.fillStyle=color(p.macro);c.globalAlpha=.62;c.beginPath();c.arc(a.x,a.y,view.s>2?2:1.35,0,7);c.fill()});c.globalAlpha=1;}
    function show(p){const t=topics.get(p.fine);if(!p)return;const paper=`<p><b>${p.title}</b><br>${p.year||'undated'}${p.doi?` · <a target="_blank" rel="noopener" href="https://doi.org/${p.doi}">DOI ↗</a>`:''}</p>`;if(!t){detail.innerHTML='<h3>Paper</h3>'+paper;return}detail.innerHTML=`<div class="tag">${macro.get(p.macro)||'Theme'}</div><h3>${t.label.replace(/^[-\d_]+/,'')}</h3><div class="score">${t.opportunity==null?'—':t.opportunity}<small> / 100 opportunity signal</small></div><p>${t.keywords||'No keyword summary available.'}</p><div class="meters">${Object.entries(t.components||{}).map(([k,v])=>`<span class="meter">${k} ${v}<i><b style="width:${v}%"></b></i></span>`).join('')}</div><p>${t.recent||0} papers in the latest five complete years; ${t.size} total. This is a corpus-derived signal, not a claim of field-wide neglect.</p>${paper}`}
    function resize(){DPR=Math.min(2,devicePixelRatio||1);W=cv.clientWidth;H=cv.clientHeight;cv.width=W*DPR;cv.height=H*DPR;draw()}new ResizeObserver(resize).observe(cv);
    cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};cv.setPointerCapture(e.pointerId)});cv.addEventListener('pointermove',e=>{if(!drag)return;view.x=drag.vx+e.clientX-drag.x;view.y=drag.vy+e.clientY-drag.y;draw()});cv.addEventListener('pointerup',e=>{if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<5){const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let best,dist=12;filtered.forEach(p=>{const a=screen(p),d=Math.hypot(a.x-mx,a.y-my);if(d<dist){best=p;dist=d}});show(best)}drag=null});cv.addEventListener('wheel',e=>{e.preventDefault();view.s=Math.max(.55,Math.min(8,view.s*(e.deltaY<0?1.16:.86)));draw()},{passive:false});
    topic.onchange=filter;year.onchange=filter;search.oninput=filter;filter();resize();
    document.querySelectorAll('[data-atlas-query]').forEach(b=>b.onclick=()=>{search.value=b.dataset.atlasQuery;filter();host.scrollIntoView({behavior:'smooth',block:'start'});});
    document.querySelectorAll('[data-atlas-opportunity]').forEach(b=>b.onclick=()=>$('#sec-opportunity').scrollIntoView({behavior:'smooth',block:'start'}));
    if(opp){opp.innerHTML='';atlas.topics.filter(t=>t.opportunity!=null).slice(0,9).forEach(t=>{const c=el('article','opp');c.innerHTML=`<div class="tag">${t.trend} bridge</div><h3>${t.label.replace(/^[-\d_]+/,'')}</h3><div class="score">${t.opportunity}<small> / 100</small></div><p>${t.recent} recent papers · bridge ${t.components.bridge} · growth ${t.components.growth}</p>`;c.onclick=()=>{topic.value=t.parent;filter();detail.scrollIntoView({behavior:'smooth',block:'nearest'});show(atlas.points.find(p=>p.fine===t.id))};opp.appendChild(c)})}
  }).catch(()=>{building('#atlas-body','The interactive atlas will appear after the next pipeline refresh.');if(opp)building('#opportunity-body','Opportunity signals are generated with the atlas data.');});
})();
"""

METHODS_JS = r"""
(function(){
  if(!DATA.method_share){ building('#methods-body','Method trajectories appear once the corpus is harvested and tagged.'); return; }
  const body=$('#methods-body'); body.innerHTML='';
  const years=DATA.years, groups=DATA.method_groups||{};
  const SIGNATURE=['Coalescent theory','Ancient DNA','ABC (approx. Bayesian)','PSMC / MSMC','msprime / tskit / ARG','Deep learning','Selection scan (iHS/EHH)','GWAS'];
  const btns=el('div','btns'); body.appendChild(btns);
  const wrap=el('div','card'); const chart=el('div','chart-wrap'); wrap.appendChild(chart);
  const legend=el('div','legend'); wrap.appendChild(legend); body.appendChild(wrap);
  const views={'Signature':SIGNATURE}; Object.assign(views,groups); let current='Signature';
  function draw(){ const names=(views[current]||[]).filter(m=>DATA.method_share[m]);
    const series=names.map((m,i)=>({name:m,color:PAL[i%PAL.length],vals:DATA.method_share[m],off:false}));
    lineChart(chart,years,series,{pct:true,h:340});
    legend.innerHTML=''; series.forEach(s=>{ const g=el('span','lg');
      g.innerHTML=`<span class="sw" style="background:${s.color}"></span>${s.name}`;
      g.onclick=()=>{s.off=!s.off; g.classList.toggle('off',s.off); lineChart(chart,years,series,{pct:true,h:340});}; legend.appendChild(g); }); }
  Object.keys(views).forEach(k=>{ const b=el('button','btn'+(k===current?' active':''),k); b.onclick=()=>{current=k;[...btns.children].forEach(c=>c.classList.remove('active'));b.classList.add('active');draw();}; btns.appendChild(b); });
  draw();
})();
"""

TOPICS_JS = r"""
(function(){
  if(!DATA.topics||!DATA.topics.length){ building('#topics-body','Topic evolution appears after abstracts are embedded and clustered.'); return; }
  const body=$('#topics-body'); body.innerHTML='';
  const years=DATA.years, topics=DATA.topics.slice(0,12);
  const wrap=el('div','card'); const chart=el('div','chart-wrap'); wrap.appendChild(chart); body.appendChild(wrap);
  const W=Math.max(700,years.length*17), H=360, P={l:8,r:8,t:12,b:26}, iw=W-P.l-P.r, ih=H-P.t-P.b;
  const stackMax=Math.max(...years.map((_,i)=>topics.reduce((a,t)=>a+(t.share[i]||0),0)))||0.01;
  const x=i=>P.l+iw*(i/(years.length-1));
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H});
  years.forEach((yr,i)=>{ if(yr%5===0){const tx=svgEl('text',{x:x(i),y:H-8,'text-anchor':'middle',class:'axis'}); tx.textContent=yr; svg.appendChild(tx);} });
  const base=new Array(years.length).fill(0).map((_,i)=>{ const tot=topics.reduce((a,t)=>a+(t.share[i]||0),0); return (stackMax-tot)/2; });
  let acc=base.slice();
  topics.forEach((t,ti)=>{ const top=acc.slice(); const bot=acc.map((v,i)=>v+(t.share[i]||0));
    let d='M'+x(0)+' '+(P.t+ih*(1-top[0]/stackMax));
    for(let i=1;i<years.length;i++) d+=' L'+x(i)+' '+(P.t+ih*(1-top[i]/stackMax));
    for(let i=years.length-1;i>=0;i--) d+=' L'+x(i)+' '+(P.t+ih*(1-bot[i]/stackMax)); d+='Z';
    const path=svgEl('path',{d,fill:PAL[ti%PAL.length],opacity:.82,stroke:css('--ink'),'stroke-width':.4});
    const ttl=svgEl('title'); ttl.textContent=t.label+(t.keywords?' — '+t.keywords:''); path.appendChild(ttl);
    svg.appendChild(path); acc=bot; });
  chart.appendChild(svg);
  const lg=el('div','legend'); topics.forEach((t,ti)=>{ lg.appendChild(el('span','lg',`<span class="sw" style="background:${PAL[ti%PAL.length]}"></span>${(t.label||'').replace(/^[-\d\s]+/,'').slice(0,42)}`)); }); wrap.appendChild(lg);
  const list=el('div','tlist');
  DATA.topics.slice(0,16).forEach(t=>{ const it=el('div','titem'); const lbl=(t.label||'').replace(/^[-\d\s]+/,'').slice(0,48);
    it.appendChild(el('p','tl',`<span>${lbl}</span><span class="trend ${t.trend}">${t.trend==='rising'?'▲':t.trend==='declining'?'▼':'—'} ${t.peak_year||''}</span>`));
    it.appendChild(el('p','kw',(t.keywords||'').split(',').slice(0,6).join(', '))); list.appendChild(it); });
  body.appendChild(list);
})();
"""

NETWORK_JS = r"""
(function(){
  if(!DATA.net||!DATA.net.nodes||!DATA.net.nodes.length){ building('#net-body','The collaboration graph appears after the co-authorship network is built.'); return; }
  const body=$('#net-body'); body.innerHTML='';
  const cv=el('canvas'); cv.id='netcanvas'; body.appendChild(cv); const tip=$('#nettip');
  const nodes=DATA.net.nodes, edges=DATA.net.edges;
  const comms=[...new Set(nodes.map(n=>n.community))]; const cidx=Object.fromEntries(comms.map((c,i)=>[c,i]));
  const NC=comms.length, pos={}, byC={}; nodes.forEach(n=>{(byC[n.community]=byC[n.community]||[]).push(n);});
  comms.forEach((c,ci)=>{ const ang=2*Math.PI*ci/NC, cx=Math.cos(ang), cy=Math.sin(ang);
    const mem=byC[c].sort((a,b)=>b.degree-a.degree);
    mem.forEach((n,i)=>{ const r=0.16+0.16*Math.sqrt(i/mem.length), a2=i*2.399963;
      pos[n.id]={x:cx*0.62+Math.cos(a2)*r*0.42, y:cy*0.62+Math.sin(a2)*r*0.42}; }); });
  let VW,VH,DPR=Math.min(2,window.devicePixelRatio||1),tx=0,ty=0,scale=1;
  const maxDeg=Math.max(...nodes.map(n=>n.degree),1);
  function resize(){ VW=cv.clientWidth; VH=cv.clientHeight; cv.width=VW*DPR; cv.height=VH*DPR; draw(); }
  function P2S(p){ const s=Math.min(VW,VH)*0.46*scale; return {x:VW/2+p.x*s+tx, y:VH/2+p.y*s+ty}; }
  function draw(){ const ctx=cv.getContext('2d'); ctx.setTransform(DPR,0,0,DPR,0,0); ctx.clearRect(0,0,VW,VH);
    ctx.globalAlpha=0.10; ctx.strokeStyle=css('--faint'); ctx.lineWidth=0.5;
    edges.forEach(e=>{ const a=pos[e.s],b=pos[e.t]; if(!a||!b)return; const pa=P2S(a),pb=P2S(b); ctx.beginPath(); ctx.moveTo(pa.x,pa.y); ctx.lineTo(pb.x,pb.y); ctx.stroke(); });
    ctx.globalAlpha=1;
    nodes.forEach(n=>{ const p=P2S(pos[n.id]); const r=2+3.4*Math.sqrt(n.degree/maxDeg);
      ctx.beginPath(); ctx.arc(p.x,p.y,r*(n.seed?1.5:1),0,7); ctx.fillStyle=PAL[cidx[n.community]%PAL.length];
      ctx.globalAlpha=n.seed?1:0.85; ctx.fill();
      if(n.seed){ctx.globalAlpha=1;ctx.lineWidth=1.2;ctx.strokeStyle=css('--text');ctx.stroke();} });
    ctx.globalAlpha=1; }
  function nearest(mx,my){ let best=null,bd=1e9; nodes.forEach(n=>{const p=P2S(pos[n.id]); const d=(p.x-mx)**2+(p.y-my)**2; if(d<bd){bd=d;best=n;}}); return bd<220?best:null; }
  cv.addEventListener('mousemove',ev=>{ const r=cv.getBoundingClientRect(); const n=nearest(ev.clientX-r.left,ev.clientY-r.top);
    if(n){ tip.style.display='block'; tip.style.left=(ev.clientX+12)+'px'; tip.style.top=(ev.clientY+12)+'px';
      tip.innerHTML=`<b>${n.name||n.id}</b>${n.inst?'<br>'+n.inst:''}<br><span class="mono" style="color:var(--faint)">deg ${n.degree} · ${fmt(n.cites)} cites</span>`; } else tip.style.display='none'; });
  cv.addEventListener('mouseleave',()=>tip.style.display='none');
  let drag=null; cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,tx,ty};});
  window.addEventListener('pointerup',()=>drag=null);
  window.addEventListener('pointermove',e=>{ if(!drag)return; tx=drag.tx+(e.clientX-drag.x); ty=drag.ty+(e.clientY-drag.y); draw(); });
  cv.addEventListener('wheel',e=>{e.preventDefault(); const f=e.deltaY<0?1.1:0.9; scale=Math.max(0.4,Math.min(6,scale*f)); draw();},{passive:false});
  new ResizeObserver(resize).observe(cv); resize();
  if(DATA.net.communities&&DATA.net.communities.length){ const lg=el('div','legend','');
    DATA.net.communities.forEach(c=>{ const meth=(c.top_methods||[]).slice(0,2).join(', ');
      const nm=(c.top_members&&c.top_members[0]?c.top_members[0].name:'').split(' ').slice(-1)[0];
      lg.appendChild(el('span','lg',`<span class="sw" style="background:${PAL[cidx[c.community]%PAL.length]}"></span>${c.size} · ${meth||nm||'community'}`)); }); body.appendChild(lg); }
})();
"""

PIVOTAL_JS = r"""
(function(){
  if(!DATA.pivotal||!DATA.pivotal.length){ building('#pivotal-body','Pivotal papers appear after the in-corpus citation graph is built.'); return; }
  const body=$('#pivotal-body'); body.innerHTML='';
  const wrap=el('div','card'); const cw=el('div','chart-wrap'); wrap.appendChild(cw); body.appendChild(wrap);
  const t=el('table'); t.innerHTML='<thead><tr><th>Year</th><th>Title</th><th>In-corpus cites</th><th>Total cites</th></tr></thead>';
  const tb=el('tbody');
  DATA.pivotal.forEach(p=>{ const tr=el('tr'); tr.appendChild(el('td','',(p.year||'—')));
    const td=el('td'); td.innerHTML=p.id?`<a href="https://doi.org/${p.id}" target="_blank" rel="noopener">${(p.title||'untitled')}</a>`:(p.title||'untitled'); tr.appendChild(td);
    tr.appendChild(el('td','<span class="num">'+fmt(p.in_corpus_cites)+'</span>'));
    tr.appendChild(el('td','<span class="num">'+fmt(p.cites)+'</span>')); tb.appendChild(tr); });
  t.appendChild(tb); cw.appendChild(t);
})();
"""

PEOPLE_JS = r"""
(function(){
  const body=$('#people-body'); if(!body)return;
  if(!DATA.researchers||!DATA.researchers.length){ building('#people-body','The directory appears once the universe is discovered.'); return; }
  body.innerHTML='';
  const inp=el('input','search'); inp.placeholder='Search '+DATA.researchers.length+' researchers — name, institution, method…'; body.appendChild(inp);
  const grid=el('div','people'); body.appendChild(grid); const more=el('p','more'); body.appendChild(more);
  const R=DATA.researchers;
  function card(r){ const c=el('div','person');
    c.appendChild(el('div','nm',`${r.name||'—'}${r.seed?'<span class="seed">SEED</span>':''}`));
    if(r.inst) c.appendChild(el('div','in',r.inst));
    const span=(r.first&&r.last)?`${r.first}–${r.last}`:(r.last?('→'+r.last):'');
    c.appendChild(el('div','meta',`${fmt(r.cites)} cites · ${fmt(r.works)} works${span?' · '+span:''}`));
    const chips=(r.methods||[]).concat(r.topics||[]).slice(0,4);
    if(chips.length){ const cc=el('div','chips'); chips.forEach(m=>cc.appendChild(el('span','chip',m))); c.appendChild(cc);} return c; }
  let limit=60;
  function render(){ const q=inp.value.toLowerCase().trim();
    const f=q? R.filter(r=>((r.name||'')+' '+(r.inst||'')+' '+(r.methods||[]).join(' ')+' '+(r.topics||[]).join(' ')).toLowerCase().includes(q)) : R;
    grid.innerHTML=''; f.slice(0,limit).forEach(r=>grid.appendChild(card(r)));
    more.textContent=f.length>limit?`showing ${limit} of ${f.length}`:(f.length?`${f.length} researchers`:'no matches'); }
  inp.addEventListener('input',()=>{limit=60;render();});
  window.addEventListener('scroll',()=>{ if(window.innerHeight+window.scrollY>document.body.offsetHeight-400){ limit+=60; render(); }});
  render();
})();
"""

_FOOT = """<footer><div class="wrap" style="display:flex;flex-wrap:wrap;gap:.4rem 1.4rem">
  <span>Data: <a href="https://www.crossref.org">Crossref</a> (open)</span>
  <span>Source: <a href="https://github.com/kevinkorfmann/PGenMap">github.com/kevinkorfmann/PGenMap</a></span>
</div></footer>"""


def _page(title, head_html, body_html, js):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<script id="data" type="application/json">/*__DATA__*/</script>\n'
            + head_html + '\n<main class="wrap">\n' + body_html + '\n</main>\n'
            + _FOOT + '\n<div id="nettip"></div>\n<script>\n'
            + PREAMBLE_JS + js + '\n</script>\n</body>\n</html>\n')


_MAIN_HEAD = """<header><div class="wrap"><div class="head">
  <div class="grow"><p class="eyebrow">Bibliometric cartography · field evolution</p>
    <h1>The <em>population genetics</em> atlas</h1></div>
  <a class="navlink" href="scientists.html">Researcher directory →</a>
  <div id="statuspill" class="pill"><span class="dot live"></span><span id="statustxt">building…</span></div>
</div>
<div id="disclaimer"></div>
<div id="tiles" class="tiles"></div>
</div></header>"""

_MAIN_BODY = """  <section id="sec-intro" style="border-top:none"><div class="sec-h"><h2>How to read this atlas</h2></div>
    <p class="sub">This is a map of the field’s language and research questions—not a geographic map and not a ranking of paper quality. It places papers near one another when their titles and abstracts use similar concepts. The current corpus runs from 1921 to 2026 and is rebuilt from Crossref metadata.</p>
    <div class="primer">
      <article class="card"><div class="num">01 · DISTANCE</div><h3>Near means conceptually similar</h3><p>For example, papers about <em>ancient DNA</em>, <em>admixture</em>, and <em>human ancestry</em> tend to form nearby neighbourhoods. A paper on <em>tree sequences</em> may sit closer to simulation and inference work than to conservation genomics.</p></article>
      <article class="card"><div class="num">02 · COLOUR & ZOOM</div><h3>Start broad, then inspect a niche</h3><p>Colour identifies a large theme. Zooming reveals individual papers and smaller subtopics inside it—such as a particular organism, method, or application. Try searching “ancient DNA,” “selection,” or “simulation,” then click a point.</p></article>
      <article class="card"><div class="num">03 · OPPORTUNITY SIGNALS</div><h3>Evidence, not a verdict</h3><p>A high score combines recent growth, connections to other themes, and a still-modest share of the corpus. For example, a small fast-growing bridge between machine learning and demographic inference can score highly; it does not prove the area is objectively neglected.</p></article>
    </div>
    <div class="sec-h" style="margin-top:1.8rem"><h2>Try a case study</h2></div>
    <p class="sub">These are starting questions a researcher, student, or funder might bring to the atlas. Each button sets up the map; then zoom, inspect papers, and compare the evidence rather than relying on the first result.</p>
    <div class="case-studies">
      <article class="case"><div class="num">METHOD TRAJECTORY</div><h3>Where is deep learning connecting?</h3><p>Search the method, then inspect nearby themes. Are papers concentrated in selection scans, simulations, demographic inference, or spread across several neighbourhoods? Use the detail panel to open representative papers.</p><a href="#sec-atlas" data-atlas-query="Deep learning">Explore deep learning</a></article>
      <article class="case"><div class="num">FIELD HISTORY</div><h3>How did ancient DNA reshape the map?</h3><p>Search ancient DNA and use the year filter to compare early work with recent literature. Look for which neighbouring methods and questions appear as the area grows.</p><a href="#sec-atlas" data-atlas-query="Ancient DNA">Explore ancient DNA</a></article>
      <article class="case"><div class="num">RESEARCH DIRECTION</div><h3>Which small bridges merit a closer look?</h3><p>Open an Opportunity Lab card, then read its growth, bridge, and niche components. Treat it as a shortlist for literature review—check its papers before treating it as a research gap.</p><a href="#sec-opportunity" data-atlas-opportunity="true">Open opportunity signals</a></article>
    </div></section>
  <section id="sec-atlas"><div class="sec-h"><h2>Explore the semantic landscape</h2></div>
    <p class="sub">Each point is one paper. Scroll to zoom, drag to pan, and click a point to see its subtopic, opportunity evidence, methods, and DOI. At wide zoom, the map becomes a density view so that crowded areas remain readable.</p>
    <div id="atlas-body"></div></section>
  <section id="sec-opportunity"><div class="sec-h"><h2>Opportunity lab</h2></div>
    <p class="sub">Emerging bridges are small but established subtopics combining recent momentum with links across the field. The score is 45% recent growth, 35% cross-theme semantic bridging, and 20% modest current share. Open a card to locate it on the map and inspect the underlying evidence.</p>
    <div id="opportunity-body"></div></section>
  <section id="sec-figures"><div class="sec-h"><h2>Evidence library</h2></div>
    <p class="sub">A UMAP semantic map of the whole corpus, plus method, topic, growth and community plots. Click any figure to open it full size.</p>
    <div id="figures-body"></div></section>
  <section id="sec-methods"><div class="sec-h"><h2>Method trajectories</h2></div>
    <p class="sub">Share of the field's yearly output that mentions each method — the adoption curves that mark the field's turns. Toggle a theme, or click legend entries.</p>
    <div id="methods-body"></div></section>
  <section id="sec-topics"><div class="sec-h"><h2>Topic evolution</h2></div>
    <p class="sub">Themes discovered by clustering paper embeddings, as a share of yearly output.</p>
    <div id="topics-body"></div></section>
  <section id="sec-net"><div class="sec-h"><h2>Collaboration network</h2></div>
    <p class="sub">Co-authorship among the mapped researchers. Spatial clusters are the "schools"; colour marks the detected community. Hover a node.</p>
    <div id="net-body"></div></section>
  <section id="sec-pivotal"><div class="sec-h"><h2>Pivotal papers</h2></div>
    <p class="sub">Works most cited <em>by other papers within this corpus</em> — the field's internal load-bearing references.</p>
    <div id="pivotal-body"></div></section>"""

_SCI_HEAD = """<header><div class="wrap"><div class="head">
  <div class="grow"><p class="eyebrow">Bibliometric cartography · field evolution</p>
    <h1>Researcher <em>directory</em></h1></div>
  <a class="navlink" href="index.html">← Back to dashboard</a>
  <div id="statuspill" class="pill"><span class="dot"></span><span id="statustxt">directory</span></div>
</div>
<div id="tiles" class="tiles"></div>
</div></header>"""

_SCI_BODY = """  <section id="sec-people" style="border-top:none;padding-top:1rem">
    <p class="sub">Everyone in the map, ranked by in-corpus impact. Search by name, institution, or method. Seeds are the starting researchers; the rest were found by co-authorship expansion.</p>
    <div id="people-body"></div></section>"""

MAIN_TEMPLATE = _page("PGenMap — Population Genetics Atlas", _MAIN_HEAD, _MAIN_BODY,
                      STATUS_JS + ATLAS_JS + FIGURES_JS + METHODS_JS + TOPICS_JS + NETWORK_JS + PIVOTAL_JS)
SCIENTISTS_TEMPLATE = _page("PGenMap — Researcher Directory", _SCI_HEAD, _SCI_BODY,
                            STATUS_JS + PEOPLE_JS)

# Back-compat: build_dashboard imports HTML_TEMPLATE
HTML_TEMPLATE = MAIN_TEMPLATE
