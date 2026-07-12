"""HTML template for the PGenMap dashboard. One big self-contained string with a
/*__DATA__*/ placeholder that build_dashboard.py replaces with the JSON payload.
Vanilla JS only (GitHub Pages is same-origin, but we inline for simplicity):
SVG for time-series/streamgraph, Canvas for the collaboration graph."""

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PGenMap — Evolution of Population Genetics</title>
<style>
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
    font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.55;
    -webkit-font-smoothing:antialiased;}
  .wrap{max-width:1080px;margin:0 auto;padding:0 1.3rem;}
  a{color:var(--teal);text-decoration:none}
  a:hover{text-decoration:underline}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}

  header{border-bottom:1px solid var(--line);background:linear-gradient(180deg,var(--surface),var(--ink));}
  .head{display:flex;flex-wrap:wrap;align-items:flex-end;gap:1rem 1.4rem;padding:2.4rem 0 1.6rem;}
  .eyebrow{font-family:ui-monospace,monospace;font-size:.72rem;letter-spacing:.2em;
    text-transform:uppercase;color:var(--teal);margin:0 0 .5rem;}
  h1{font-family:ui-serif,Georgia,serif;font-weight:600;font-size:clamp(1.7rem,4vw,2.6rem);
    line-height:1.06;margin:0;letter-spacing:-.01em;text-wrap:balance;}
  h1 em{font-style:italic;color:var(--teal)}
  .head .grow{flex:1 1 320px}
  .pill{display:inline-flex;align-items:center;gap:.5rem;background:var(--surface2);
    border:1px solid var(--line);border-radius:999px;padding:.4rem .8rem;font-size:.8rem;color:var(--muted)}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--amber)}
  .dot.live{animation:pulse 2s infinite}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(224,164,88,.5)}70%{box-shadow:0 0 0 8px rgba(224,164,88,0)}100%{box-shadow:0 0 0 0 rgba(224,164,88,0)}}
  @media (prefers-reduced-motion: reduce){.dot.live{animation:none}}

  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;
    background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:1.4rem 0 2rem;}
  .tile{background:var(--surface);padding:1rem 1.1rem}
  .tile .k{font-family:ui-monospace,monospace;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin:0 0 .35rem}
  .tile .v{font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums;color:var(--text)}
  .tile .v small{font-size:.8rem;color:var(--muted);font-weight:400}

  section{padding:2.2rem 0;border-top:1px solid var(--line)}
  .sec-h{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-bottom:.3rem}
  h2{font-family:ui-serif,Georgia,serif;font-weight:600;font-size:1.5rem;margin:0;letter-spacing:-.01em}
  .sub{color:var(--muted);margin:.2rem 0 1.3rem;max-width:70ch}
  .building{background:var(--surface);border:1px dashed var(--line);border-radius:10px;
    padding:1.4rem;color:var(--faint);font-size:.9rem;display:flex;align-items:center;gap:.6rem}

  .card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1.1rem}
  .chart-wrap{overflow-x:auto}
  svg{display:block;max-width:100%}
  .legend{display:flex;flex-wrap:wrap;gap:.4rem .8rem;margin-top:.8rem}
  .lg{display:inline-flex;align-items:center;gap:.4rem;font-size:.82rem;color:var(--muted);cursor:pointer;
    border:1px solid transparent;border-radius:6px;padding:.15rem .35rem}
  .lg:hover{border-color:var(--line)}
  .lg.off{opacity:.35}
  .sw{width:11px;height:11px;border-radius:3px;flex:none}

  .btns{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem}
  .btn{background:var(--surface2);border:1px solid var(--line);color:var(--muted);border-radius:999px;
    padding:.32rem .8rem;font-size:.82rem;cursor:pointer;font-family:inherit}
  .btn.active{background:var(--teal);color:#04110f;border-color:var(--teal);font-weight:600}

  .tlist{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:.7rem;margin-top:1rem}
  .titem{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.75rem .9rem}
  .titem .tl{font-weight:600;font-size:.92rem;margin:0 0 .25rem;display:flex;justify-content:space-between;gap:.5rem}
  .trend{font-size:.72rem;font-family:ui-monospace,monospace;padding:.05rem .35rem;border-radius:5px}
  .trend.rising{color:var(--teal);background:color-mix(in srgb,var(--teal) 15%,transparent)}
  .trend.declining{color:var(--amber);background:color-mix(in srgb,var(--amber) 15%,transparent)}
  .trend.stable{color:var(--faint)}
  .titem .kw{font-size:.78rem;color:var(--muted);margin:0}

  #netcanvas{width:100%;height:520px;display:block;border-radius:12px;background:var(--surface);border:1px solid var(--line);touch-action:none}
  #nettip{position:fixed;pointer-events:none;background:var(--surface2);border:1px solid var(--line);
    border-radius:8px;padding:.45rem .6rem;font-size:.82rem;color:var(--text);display:none;z-index:9;max-width:240px;box-shadow:0 6px 24px rgba(0,0,0,.3)}

  .search{width:100%;background:var(--surface);border:1px solid var(--line);border-radius:10px;
    color:var(--text);padding:.7rem .9rem;font-size:.95rem;font-family:inherit;margin-bottom:1rem}
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
  .chart-wrap.tbl{max-height:none}
  th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
  th{font-family:ui-monospace,monospace;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
  td .num{font-variant-numeric:tabular-nums;color:var(--muted)}
  footer{border-top:1px solid var(--line);padding:2rem 0 3rem;color:var(--faint);font-size:.85rem;
    display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}
  .axis{font-size:10px;fill:var(--faint);font-family:ui-monospace,monospace}
  .gridline{stroke:var(--grid);stroke-width:1}
  .disclaimer{border-radius:12px;padding:1rem 1.15rem;margin:1.4rem 0 0;
    display:flex;gap:.85rem;align-items:flex-start;font-size:.9rem;line-height:1.5}
  .disclaimer.warn{background:color-mix(in srgb,var(--amber) 14%,var(--surface));
    border:1px solid color-mix(in srgb,var(--amber) 55%,var(--line));color:var(--text)}
  .disclaimer.note{background:var(--surface);border:1px solid var(--line);color:var(--muted);font-size:.82rem}
  .disclaimer .ic{font-size:1.15rem;line-height:1;flex:none}
  .disclaimer b{color:var(--amber)}
  .disclaimer.note b{color:var(--muted)}
</style>
</head>
<body>
<script id="data" type="application/json">/*__DATA__*/</script>
<header><div class="wrap"><div class="head">
  <div class="grow">
    <p class="eyebrow">Bibliometric cartography · 1985–2025</p>
    <h1>The evolution of <em>population genetics</em></h1>
  </div>
  <div id="statuspill" class="pill"><span class="dot live"></span><span id="statustxt">building…</span></div>
</div>
<div id="disclaimer"></div>
<div id="tiles" class="tiles"></div>
</div></header>

<main class="wrap">
  <section id="sec-methods">
    <div class="sec-h"><h2>Method trajectories</h2></div>
    <p class="sub">Share of the field's yearly output that mentions each method — the adoption curves
      that mark the field's turns. Toggle a theme, or click legend entries.</p>
    <div id="methods-body"></div>
  </section>

  <section id="sec-topics">
    <div class="sec-h"><h2>Topic evolution</h2></div>
    <p class="sub">Themes discovered by clustering paper embeddings, as a share of yearly output.
      The stream shows what the field was collectively thinking about, year by year.</p>
    <div id="topics-body"></div>
  </section>

  <section id="sec-net">
    <div class="sec-h"><h2>Collaboration network</h2></div>
    <p class="sub">Co-authorship among the mapped researchers. Spatial clusters are the "schools";
      colour marks the detected community. Hover a node for who it is.</p>
    <div id="net-body"></div>
  </section>

  <section id="sec-people">
    <div class="sec-h"><h2>Researcher directory</h2></div>
    <p class="sub">Everyone in the map, ranked by in-corpus impact. Search by name, institution, or method.</p>
    <div id="people-body"></div>
  </section>

  <section id="sec-pivotal">
    <div class="sec-h"><h2>Pivotal papers</h2></div>
    <p class="sub">Works most cited <em>by other papers within this corpus</em> — the field's internal load-bearing references.</p>
    <div id="pivotal-body"></div>
  </section>
</main>

<footer><div class="wrap" style="display:flex;flex-wrap:wrap;gap:.4rem 1.4rem">
  <span>Data: <a href="https://www.crossref.org">Crossref</a> (open)</span>
  <span>Source: <a href="https://github.com/kevinkorfmann/PGenMap">github.com/kevinkorfmann/PGenMap</a></span>
  <span>Built with Claude Code</span>
</div></footer>

<div id="nettip"></div>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const PAL = ['#37c9b8','#e0a458','#6ea8fe','#e86a92','#9d7be0','#8bc34a','#f2c14e','#4dd0e1','#f4845f','#a3b18a','#c78ee0','#5fb3a3','#d98880','#7fb3d5'];
const $ = s => document.querySelector(s);
const el = (t,c,h)=>{const e=document.createElement(t); if(c)e.className=c; if(h!=null)e.innerHTML=h; return e;};
const fmt = n => n==null?'—':n.toLocaleString();
function css(v){return getComputedStyle(document.body).getPropertyValue(v).trim();}

// ---- status + tiles ----
(function(){
  const stage = DATA.stage, m = DATA.meta||{};
  const label = {seed:'initializing', universe:'universe discovered — harvesting corpus',
                 corpus:'corpus harvested — running analyses', full:'analysis complete'}[stage] || 'building…';
  $('#statustxt').textContent = label;
  if(stage==='full'){ $('#statuspill').querySelector('.dot').classList.remove('live'); }
  // disclaimer — prominent while data is provisional, a caveat note when final
  const dz = $('#disclaimer');
  if(stage!=='full'){
    dz.className='disclaimer warn';
    dz.innerHTML='<span class="ic">⚠️</span><div><b>Work in progress — numbers are provisional.</b> '
      +'The corpus is still being harvested and per-researcher publication and citation counts are '
      +'being recomputed from the retrieved papers. Some counts shown now are preliminary discovery-stage '
      +'estimates and are undercounted for authors whose names carry diacritics or appear as initials '
      +'(a known limitation of name-based Crossref attribution). Figures will update automatically as the '
      +'pipeline completes.</div>';
  } else {
    dz.className='disclaimer note';
    dz.innerHTML='<span class="ic">ℹ️</span><div><b>About the data.</b> Built from '
      +'<a href="https://www.crossref.org">Crossref</a> (open metadata). Author identity is inferred from a '
      +'normalized name key with venue/keyword relevance filtering — disambiguation and coverage are '
      +'heuristic, so counts for authors with name variants or common names may be under- or over-stated, '
      +'and abstract coverage is partial. Treat figures as field-scale signal, not exact bibliometrics.</div>';
  }
  const tiles = [
    ['Researchers', fmt(m.researchers)],
    ['Publications', m.works!=null?fmt(m.works):'<small>harvesting…</small>'],
    ['With abstracts', m.works_with_abstract!=null?fmt(m.works_with_abstract):'<small>—</small>'],
    ['Span', (m.year_min?`${m.year_min}–${m.year_max}`:'1985–2025')],
    ['Countries', m.countries!=null?fmt(m.countries):'<small>—</small>'],
    ['Schools', m.communities!=null?fmt(m.communities):'<small>—</small>'],
  ];
  const box=$('#tiles');
  tiles.forEach(([k,v])=>{const t=el('div','tile'); t.appendChild(el('p','k',k)); t.appendChild(el('p','v',v)); box.appendChild(t);});
})();

function building(id,msg){ $(id).innerHTML=''; const b=el('div','building','<span class="dot live"></span>'+msg); $(id).appendChild(b); }

// ---- helpers for SVG line/area charts ----
function svgEl(t,attrs){const e=document.createElementNS('http://www.w3.org/2000/svg',t); for(const k in attrs)e.setAttribute(k,attrs[k]); return e;}
function lineChart(container, years, series, opts){
  opts=opts||{}; container.innerHTML='';
  const W=Math.max(680, years.length*16), H=opts.h||330, P={l:44,r:16,t:14,b:26};
  const iw=W-P.l-P.r, ih=H-P.t-P.b;
  let maxY=opts.max|| Math.max(...series.flatMap(s=>s.vals.filter(v=>v!=null)),0.001);
  maxY*=1.08;
  const x=i=>P.l+ iw*(i/(years.length-1));
  const y=v=>P.t+ ih*(1-(v/maxY));
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img'});
  // gridlines + y labels
  const ticks=opts.pct?[0,0.25,0.5,0.75,1]:[0,0.5,1];
  const yt=(opts.yticks||4);
  for(let i=0;i<=yt;i++){const v=maxY*i/yt; const yy=y(v);
    svg.appendChild(svgEl('line',{x1:P.l,x2:W-P.r,y1:yy,y2:yy,class:'gridline'}));
    const lab=opts.pct?(v*100).toFixed(v<0.02?1:0)+'%':Math.round(v);
    const tx=svgEl('text',{x:P.l-6,y:yy+3,'text-anchor':'end',class:'axis'}); tx.textContent=lab; svg.appendChild(tx);}
  // x labels every ~5 yrs
  years.forEach((yr,i)=>{ if(yr%5===0){ const tx=svgEl('text',{x:x(i),y:H-8,'text-anchor':'middle',class:'axis'}); tx.textContent=yr; svg.appendChild(tx);} });
  series.forEach((s,si)=>{
    if(s.off) return;
    let d='';
    s.vals.forEach((v,i)=>{ if(v==null)return; d+=(d?'L':'M')+x(i).toFixed(1)+' '+y(v).toFixed(1)+' ';});
    svg.appendChild(svgEl('path',{d,fill:'none',stroke:s.color,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round',opacity:.95}));
    // endpoint dot
    let li=s.vals.length-1; while(li>=0&&s.vals[li]==null)li--;
    if(li>=0) svg.appendChild(svgEl('circle',{cx:x(li),cy:y(s.vals[li]),r:2.6,fill:s.color}));
  });
  container.appendChild(svg);
}

// ---- METHODS ----
(function(){
  if(!DATA.method_share){ building('#methods-body','Method trajectories appear once the corpus is harvested and tagged.'); return; }
  const body=$('#methods-body'); body.innerHTML='';
  const years=DATA.years;
  const groups=DATA.method_groups||{};
  const SIGNATURE=['Coalescent theory','Ancient DNA','ABC (approx. Bayesian)','PSMC / MSMC','msprime / tskit / ARG','Deep learning','Selection scan (iHS/EHH)','GWAS'];
  const btns=el('div','btns'); body.appendChild(btns);
  const wrap=el('div','card'); const chart=el('div','chart-wrap'); wrap.appendChild(chart);
  const legend=el('div','legend'); wrap.appendChild(legend); body.appendChild(wrap);
  const views={'Signature':SIGNATURE}; Object.assign(views,groups);
  let current='Signature';
  function draw(){
    const names=(views[current]||[]).filter(m=>DATA.method_share[m]);
    const series=names.map((m,i)=>({name:m,color:PAL[i%PAL.length],vals:DATA.method_share[m],off:false}));
    lineChart(chart,years,series,{pct:true,h:340});
    legend.innerHTML='';
    series.forEach(s=>{ const g=el('span','lg');
      g.innerHTML=`<span class="sw" style="background:${s.color}"></span>${s.name}`;
      g.onclick=()=>{s.off=!s.off; g.classList.toggle('off',s.off); lineChart(chart,years,series,{pct:true,h:340});};
      legend.appendChild(g); });
  }
  Object.keys(views).forEach(k=>{ const b=el('button','btn'+(k===current?' active':''),k); b.onclick=()=>{current=k; [...btns.children].forEach(c=>c.classList.remove('active')); b.classList.add('active'); draw();}; btns.appendChild(b); });
  draw();
})();

// ---- TOPICS (streamgraph) ----
(function(){
  if(!DATA.topics||!DATA.topics.length){ building('#topics-body','Topic evolution appears after abstracts are embedded and clustered.'); return; }
  const body=$('#topics-body'); body.innerHTML='';
  const years=DATA.years;
  const topics=DATA.topics.slice(0,12);
  const wrap=el('div','card'); const chart=el('div','chart-wrap'); wrap.appendChild(chart); body.appendChild(wrap);
  // stacked area (streamgraph, wiggle-ish: center baseline)
  const W=Math.max(700,years.length*17), H=360, P={l:8,r:8,t:12,b:26}, iw=W-P.l-P.r, ih=H-P.t-P.b;
  const stackMax=Math.max(...years.map((_,i)=>topics.reduce((a,t)=>a+(t.share[i]||0),0)))||0.01;
  const x=i=>P.l+iw*(i/(years.length-1));
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H});
  years.forEach((yr,i)=>{ if(yr%5===0){const tx=svgEl('text',{x:x(i),y:H-8,'text-anchor':'middle',class:'axis'}); tx.textContent=yr; svg.appendChild(tx);} });
  const base=new Array(years.length).fill(0).map((_,i)=>{ const tot=topics.reduce((a,t)=>a+(t.share[i]||0),0); return (stackMax-tot)/2; });
  let acc=base.slice();
  topics.forEach((t,ti)=>{
    const top=acc.slice(); const bot=acc.map((v,i)=>v+(t.share[i]||0));
    let d='M'+x(0)+' '+(P.t+ih*(1-top[0]/stackMax));
    for(let i=1;i<years.length;i++) d+=' L'+x(i)+' '+(P.t+ih*(1-top[i]/stackMax));
    for(let i=years.length-1;i>=0;i--) d+=' L'+x(i)+' '+(P.t+ih*(1-bot[i]/stackMax));
    d+='Z';
    const path=svgEl('path',{d,fill:PAL[ti%PAL.length],opacity:.82,stroke:css('--ink'),'stroke-width':.4});
    const ttl=svgEl('title'); ttl.textContent=t.label+(t.keywords?' — '+t.keywords:''); path.appendChild(ttl);
    svg.appendChild(path); acc=bot;
  });
  chart.appendChild(svg);
  // legend + topic detail list
  const lg=el('div','legend'); topics.forEach((t,ti)=>{ lg.appendChild(el('span','lg',`<span class="sw" style="background:${PAL[ti%PAL.length]}"></span>${(t.label||'').replace(/^[-\d\s]+/,'').slice(0,42)}`)); }); wrap.appendChild(lg);
  const list=el('div','tlist');
  DATA.topics.slice(0,16).forEach(t=>{ const it=el('div','titem');
    const lbl=(t.label||'').replace(/^[-\d\s]+/,'').slice(0,48);
    it.appendChild(el('p','tl',`<span>${lbl}</span><span class="trend ${t.trend}">${t.trend==='rising'?'▲':t.trend==='declining'?'▼':'—'} ${t.peak_year||''}</span>`));
    it.appendChild(el('p','kw',(t.keywords||'').split(',').slice(0,6).join(', ')));
    list.appendChild(it); });
  body.appendChild(list);
})();

// ---- NETWORK ----
(function(){
  if(!DATA.net||!DATA.net.nodes||!DATA.net.nodes.length){ building('#net-body','The collaboration graph appears after the co-authorship network is built.'); return; }
  const body=$('#net-body'); body.innerHTML='';
  const cv=el('canvas'); cv.id='netcanvas'; body.appendChild(cv);
  const tip=$('#nettip');
  const nodes=DATA.net.nodes, edges=DATA.net.edges;
  const comms=[...new Set(nodes.map(n=>n.community))];
  const cidx=Object.fromEntries(comms.map((c,i)=>[c,i]));
  // deterministic community-clustered layout
  const NC=comms.length;
  const pos={};
  const byC={}; nodes.forEach(n=>{(byC[n.community]=byC[n.community]||[]).push(n);});
  comms.forEach((c,ci)=>{
    const ang=2*Math.PI*ci/NC, cx=Math.cos(ang), cy=Math.sin(ang);
    const mem=byC[c].sort((a,b)=>b.degree-a.degree);
    mem.forEach((n,i)=>{ const r=0.16+0.16*Math.sqrt(i/mem.length);
      const a2=i*2.399963; // golden angle
      pos[n.id]={x:cx*0.62+Math.cos(a2)*r*0.42, y:cy*0.62+Math.sin(a2)*r*0.42};
    });
  });
  let VW,VH,DPR=Math.min(2,window.devicePixelRatio||1),tx=0,ty=0,scale=1;
  const maxDeg=Math.max(...nodes.map(n=>n.degree),1);
  function resize(){ VW=cv.clientWidth; VH=cv.clientHeight; cv.width=VW*DPR; cv.height=VH*DPR; draw(); }
  function P2S(p){ const s=Math.min(VW,VH)*0.46*scale; return {x:VW/2+p.x*s+tx, y:VH/2+p.y*s+ty}; }
  function draw(){
    const ctx=cv.getContext('2d'); ctx.setTransform(DPR,0,0,DPR,0,0); ctx.clearRect(0,0,VW,VH);
    ctx.globalAlpha=0.10; ctx.strokeStyle=css('--faint'); ctx.lineWidth=0.5;
    edges.forEach(e=>{ const a=pos[e.s],b=pos[e.t]; if(!a||!b)return; const pa=P2S(a),pb=P2S(b);
      ctx.beginPath(); ctx.moveTo(pa.x,pa.y); ctx.lineTo(pb.x,pb.y); ctx.stroke(); });
    ctx.globalAlpha=1;
    nodes.forEach(n=>{ const p=P2S(pos[n.id]); const r=2+3.4*Math.sqrt(n.degree/maxDeg);
      ctx.beginPath(); ctx.arc(p.x,p.y,r*(n.seed?1.5:1),0,7); ctx.fillStyle=PAL[cidx[n.community]%PAL.length];
      ctx.globalAlpha=n.seed?1:0.85; ctx.fill();
      if(n.seed){ctx.globalAlpha=1;ctx.lineWidth=1.2;ctx.strokeStyle=css('--text');ctx.stroke();} });
    ctx.globalAlpha=1;
  }
  function nearest(mx,my){ let best=null,bd=1e9; nodes.forEach(n=>{const p=P2S(pos[n.id]); const d=(p.x-mx)**2+(p.y-my)**2; if(d<bd){bd=d;best=n;}}); return bd<220?best:null; }
  cv.addEventListener('mousemove',ev=>{ const r=cv.getBoundingClientRect(); const n=nearest(ev.clientX-r.left,ev.clientY-r.top);
    if(n){ tip.style.display='block'; tip.style.left=(ev.clientX+12)+'px'; tip.style.top=(ev.clientY+12)+'px';
      tip.innerHTML=`<b>${n.name||n.id}</b>${n.inst?'<br>'+n.inst:''}<br><span class="mono" style="color:var(--faint)">deg ${n.degree} · ${fmt(n.cites)} cites</span>`; }
    else tip.style.display='none'; });
  cv.addEventListener('mouseleave',()=>tip.style.display='none');
  let drag=null;
  cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,tx,ty};});
  window.addEventListener('pointerup',()=>drag=null);
  window.addEventListener('pointermove',e=>{ if(!drag)return; tx=drag.tx+(e.clientX-drag.x); ty=drag.ty+(e.clientY-drag.y); draw(); });
  cv.addEventListener('wheel',e=>{e.preventDefault(); const f=e.deltaY<0?1.1:0.9; scale=Math.max(0.4,Math.min(6,scale*f)); draw();},{passive:false});
  new ResizeObserver(resize).observe(cv); resize();
  // community legend
  if(DATA.net.communities&&DATA.net.communities.length){
    const lg=el('div','legend',''); DATA.net.communities.forEach(c=>{
      const nm=(c.top_members&&c.top_members[0]?c.top_members[0].name:'').split(' ').slice(-1)[0];
      const meth=(c.top_methods||[]).slice(0,2).join(', ');
      lg.appendChild(el('span','lg',`<span class="sw" style="background:${PAL[cidx[c.community]%PAL.length]}"></span>${c.size} · ${meth||nm||'community'}`));
    }); body.appendChild(lg);
  }
})();

// ---- PEOPLE ----
(function(){
  if(!DATA.researchers||!DATA.researchers.length){ building('#people-body','The directory appears once the universe is discovered.'); return; }
  const body=$('#people-body'); body.innerHTML='';
  const inp=el('input','search'); inp.placeholder='Search '+DATA.researchers.length+' researchers — name, institution, method…'; body.appendChild(inp);
  const grid=el('div','people'); body.appendChild(grid);
  const more=el('p','more'); body.appendChild(more);
  const R=DATA.researchers;
  function card(r){ const c=el('div','person');
    c.appendChild(el('div','nm',`${r.name||'—'}${r.seed?'<span class="seed">SEED</span>':''}`));
    if(r.inst) c.appendChild(el('div','in',r.inst));
    const span=(r.first&&r.last)?`${r.first}–${r.last}`:(r.last?('→'+r.last):'');
    c.appendChild(el('div','meta',`${fmt(r.cites)} cites · ${fmt(r.works)} works${span?' · '+span:''}`));
    const chips=(r.methods||[]).concat(r.topics||[]).slice(0,4);
    if(chips.length){ const cc=el('div','chips'); chips.forEach(m=>cc.appendChild(el('span','chip',m))); c.appendChild(cc);}
    return c;
  }
  let limit=60;
  function render(){
    const q=inp.value.toLowerCase().trim();
    const f=q? R.filter(r=>((r.name||'')+' '+(r.inst||'')+' '+(r.methods||[]).join(' ')+' '+(r.topics||[]).join(' ')).toLowerCase().includes(q)) : R;
    grid.innerHTML=''; f.slice(0,limit).forEach(r=>grid.appendChild(card(r)));
    more.textContent = f.length>limit? `showing ${limit} of ${f.length}` : (f.length?`${f.length} researchers`:'no matches');
  }
  inp.addEventListener('input',()=>{limit=60;render();});
  window.addEventListener('scroll',()=>{ if(window.innerHeight+window.scrollY>document.body.offsetHeight-400){ limit+=60; render(); }});
  render();
})();

// ---- PIVOTAL ----
(function(){
  if(!DATA.pivotal||!DATA.pivotal.length){ building('#pivotal-body','Pivotal papers appear after the in-corpus citation graph is built.'); return; }
  const body=$('#pivotal-body'); body.innerHTML='';
  const wrap=el('div','card'); const cw=el('div','chart-wrap tbl'); wrap.appendChild(cw); body.appendChild(wrap);
  const t=el('table'); t.innerHTML='<thead><tr><th>Year</th><th>Title</th><th>In-corpus cites</th><th>Total cites</th></tr></thead>';
  const tb=el('tbody');
  DATA.pivotal.forEach(p=>{ const tr=el('tr');
    tr.appendChild(el('td','', (p.year||'—')));
    const td=el('td'); td.innerHTML= p.id? `<a href="https://doi.org/${p.id}" target="_blank" rel="noopener">${(p.title||'untitled')}</a>`:(p.title||'untitled'); tr.appendChild(td);
    tr.appendChild(el('td','<span class="num">'+fmt(p.in_corpus_cites)+'</span>'));
    tr.appendChild(el('td','<span class="num">'+fmt(p.cites)+'</span>'));
    tb.appendChild(tr); });
  t.appendChild(tb); cw.appendChild(t);
})();
</script>
</body>
</html>
"""
