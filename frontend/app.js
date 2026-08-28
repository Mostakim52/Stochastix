/* Stochastix Terminal — App */

const API = '/api';
const PAL = ['#5FD4E8','#F5B84B','#35D07F','#B78CFF','#F0564C','#FFB3C7','#8FA5FF','#FFD98A','#7BE0C8','#C9A66F'];
const G = '#1E2638', TK = '#6B7A94', TF = {family:"'JetBrains Mono',monospace",size:10};

const S = {
  tickers:[], bench:'SPY', meta:{},
  prices:{dates:[],tickers:{}},
  fc:{}, portfolio:null, corr:null,
  horizon:21, scheme:'max_sharpe', ticker:null, view:'overview',
  charts:{}
};

const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];

/* ── Util ── */
const pct=v=>v==null||!isFinite(v)?'\u2014':`${v>=0?'+':''}${v.toFixed(2)}%`;
const money=v=>v==null||!isFinite(v)?'\u2014':`$${v.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
const money0=v=>v==null||!isFinite(v)?'\u2014':`$${Math.round(v).toLocaleString()}`;
const cls=v=>v>0?'up':v<0?'down':'';
const arr=v=>v>0?'\u25B2':v<0?'\u25BC':'\u25C6';

function killChart(k){if(S.charts[k]){S.charts[k].destroy();S.charts[k]=null;}}

/* ── API ── */
async function api(p){const r=await fetch(API+p);if(!r.ok)throw Error(r.status);return r.json();}
async function post(p,b){const r=await fetch(API+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});if(!r.ok)throw Error(r.status);return r.json();}

/* ── Load ── */
async function loadAll(){
  try{
    const[tRes,h]=await Promise.all([api('/tickers'),api('/health').catch(()=>({}))]);
    S.tickers=tRes.tickers||[]; S.bench=tRes.benchmark||'SPY'; S.meta=h;
    const[prices,f1,f5,f21,corr]=await Promise.all([
      api('/prices?days=252').catch(()=>({dates:[],tickers:{}})),
      api('/forecast/1').catch(()=>({forecasts:[]})),
      api('/forecast/5').catch(()=>({forecasts:[]})),
      api('/forecast/21').catch(()=>({forecasts:[]})),
      api('/correlations?days=120').catch(()=>null)
    ]);
    S.prices=prices;
    S.fc={1:f1.forecasts||[],5:f5.forecasts||[],21:f21.forecasts||[]};
    S.corr=corr;
    try{S.portfolio=await post('/portfolio',{capital:100000,schemes:['max_sharpe','min_variance','risk_parity','hrp','equal_weight']});}catch{S.portfolio=null;}
    return true;
  }catch(e){console.error(e);return false;}
}

/* ── Tape ── */
function renderTape(){
  const el=$('#tape-track'); if(!el) return;
  const f=S.fc[1]; if(!f?.length) return;
  const chips=f.map(r=>{
    const p=r.expected_return_pct??0,c=cls(p);
    return `<span class="chip"><span class="chip__sym">${r.ticker}</span><span class="chip__val">${r.last_close?'$'+r.last_close.toFixed(2):''}</span><span class="chip__chg ${c}">${pct(p)} ${arr(p)}</span></span>`;
  });
  el.innerHTML=chips.concat(chips).join('');
}

/* ── Nav ── */
function initNav(){
  $$('.sidebar__btn').forEach(b=>b.addEventListener('click',()=>{
    S.view=b.dataset.view;
    $$('.sidebar__btn').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    $$('.view').forEach(v=>v.classList.remove('active'));
    $(`#view-${S.view}`)?.classList.add('active');
    render(S.view);
    if(window.innerWidth<=900) closeNav();
  }));
}

/* ── Mobile nav ── */
function initMobile(){
  const burger=$('#burger'),sidebar=$('#sidebar'),ov=$('#overlay');
  if(!burger||!sidebar) return;
  burger.addEventListener('click',()=>sidebar.classList.contains('open')?closeNav():openNav());
  ov?.addEventListener('click',closeNav);
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeNav();});
  window.addEventListener('resize',()=>{if(window.innerWidth>900)closeNav();});
}
function openNav(){$('#sidebar')?.classList.add('open');$('#overlay')?.classList.add('open');}
function closeNav(){$('#sidebar')?.classList.remove('open');$('#overlay')?.classList.remove('open');}

/* ── Chart defaults ── */
function chartDefaults(){
  if(typeof Chart==='undefined')return;
  Chart.defaults.color=TK; Chart.defaults.font=TF; Chart.defaults.borderColor=G;
}

/* ══════════════════════════════════════════
   OVERVIEW
   ══════════════════════════════════════════ */
function renderOverview(){
  const h=+($('#overview-horizon')?.value||21);
  const f=S.fc[h]||S.fc[21]||[];
  const grid=$('#kpi-grid'); if(!grid) return;

  const up=f.filter(r=>(r.expected_return_pct??0)>0).length;
  const dn=f.filter(r=>(r.expected_return_pct??0)<0).length;
  const avg=f.length?f.reduce((a,r)=>a+(r.expected_return_pct??0),0)/f.length:0;

  grid.innerHTML=`
    <div class="kpi"><div class="kpi__lbl">Universe</div><div class="kpi__val">${S.tickers.length}</div><div class="kpi__tag up">tickers</div></div>
    <div class="kpi"><div class="kpi__lbl">Bullish</div><div class="kpi__val" style="color:var(--up)">${up}</div><div class="kpi__tag up">${up}/${f.length}</div></div>
    <div class="kpi"><div class="kpi__lbl">Bearish</div><div class="kpi__val" style="color:var(--down)">${dn}</div><div class="kpi__tag down">${dn}/${f.length}</div></div>
    <div class="kpi"><div class="kpi__lbl">Avg ${h}d Forecast</div><div class="kpi__val" style="color:${avg>=0?'var(--up)':'var(--down)'}">${pct(avg)}</div></div>`;

  renderOverviewChart();
  renderOverviewTable(h);
}

function renderOverviewChart(){
  killChart('ov');
  const cv=$('#overview-chart'); if(!cv) return;
  const{dates,tickers}=S.prices; if(!dates.length) return;
  const defs=['AAPL','MSFT','NVDA','SPY'].filter(t=>tickers[t]);
  if(!defs.length) return;

  const ds=defs.map((t,i)=>{
    const raw=tickers[t];
    const f0=raw.find(v=>v!=null)||1;
    return{label:t,data:raw.map(v=>v!=null?(v/f0)*100:null),borderColor:PAL[i],borderWidth:1.8,fill:false,tension:.3,pointRadius:0,pointHoverRadius:3,spanGaps:true};
  });

  S.charts.ov=new Chart(cv,{type:'line',data:{labels:dates,datasets:ds},options:{
    responsive:true,maintainAspectRatio:false,
    interaction:{mode:'index',intersect:false},
    plugins:{
      legend:{display:true,position:'top',labels:{color:TK,font:TF,boxWidth:10,padding:14}},
      tooltip:{backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,padding:10}
    },
    scales:{
      x:{grid:{color:G,drawBorder:false},ticks:{maxTicksLimit:10,maxRotation:0,font:TF},border:{display:false}},
      y:{grid:{color:G,drawBorder:false},ticks:{font:TF},border:{display:false}}
    }
  }});
}

function renderOverviewTable(h){
  const w=$('#overview-table'); if(!w) return;
  const f=S.fc[h]||[];
  w.innerHTML=`<table><thead><tr><th>Ticker</th><th>Last Close</th><th>${h}d Target</th><th>Move</th><th>Direction</th></tr></thead><tbody>${
    S.tickers.map(t=>{
      const r=f.find(x=>x.ticker===t);
      const p=r?.expected_return_pct??0,c=cls(p);
      return `<tr><td class="sym">${t}</td><td>${r?.last_close!=null?'$'+r.last_close.toFixed(2):'\u2014'}</td><td>${r?.predicted_price!=null?'$'+r.predicted_price.toFixed(2):'\u2014'}</td><td class="${c}">${pct(p)} ${arr(p)}</td><td class="${c}">${r?.direction??'\u2014'}</td></tr>`;
    }).join('')
  }</tbody></table>`;
}

/* ══════════════════════════════════════════
   FORECASTS
   ══════════════════════════════════════════ */
function renderForecasts(){
  const h=+($('#forecast-horizon')?.value||S.horizon);
  S.horizon=h;
  const f=S.fc[h]||[];
  const w=$('#forecast-table'); if(!w) return;

  w.innerHTML=`<table><thead><tr><th>Ticker</th><th>Last Close</th><th>Predicted</th><th>Move</th><th>Direction</th></tr></thead><tbody>${
    f.map(r=>{
      const p=r.expected_return_pct??0,c=cls(p);
      return `<tr data-t="${r.ticker}" class="${S.ticker===r.ticker?'selected':''}"><td class="sym">${r.ticker}</td><td>${r.last_close!=null?'$'+r.last_close.toFixed(2):'\u2014'}</td><td>${r.predicted_price!=null?'$'+r.predicted_price.toFixed(2):'\u2014'}</td><td class="${c}">${pct(p)} ${arr(p)}</td><td class="${c}">${r.direction??'\u2014'}</td></tr>`;
    }).join('')
  }</tbody></table>`;

  $$('#forecast-table tbody tr').forEach(tr=>tr.addEventListener('click',()=>{
    S.ticker=tr.dataset.t;
    renderForecasts();
    renderDetail(S.ticker);
  }));

  if(!S.ticker&&f.length) renderDetail(f[0].ticker);
  else if(S.ticker) renderDetail(S.ticker);
}

function renderDetail(ticker){
  S.ticker=ticker;
  const h=+($('#forecast-horizon')?.value||S.horizon);
  const f=(S.fc[h]||[]).find(r=>r.ticker===ticker);
  $('#detail-ticker').textContent=ticker;
  $('#detail-horizon').textContent=h+'d';

  const m=$('#detail-meta');
  if(f) m.innerHTML=`<div>Last: <b>${f.last_close!=null?'$'+f.last_close.toFixed(2):'\u2014'}</b></div><div>Target: <b>${f.predicted_price!=null?'$'+f.predicted_price.toFixed(2):'\u2014'}</b></div><div>Return: <b style="color:${(f.expected_return_pct??0)>=0?'var(--up)':'var(--down)'}">${pct(f.expected_return_pct)}</b></div>`;
  else m.innerHTML='';

  renderFan(ticker,h,f);
}

function renderFan(ticker,h,fc){
  killChart('fan');
  const cv=$('#fan-chart'); if(!cv) return;
  const raw=S.prices.tickers[ticker]; if(!raw?.length) return;

  const recent=raw.slice(-60);
  const labels=S.prices.dates.slice(-60);
  const ds=[{label:ticker,data:recent,borderColor:'#5FD4E8',borderWidth:2,fill:false,tension:.3,pointRadius:0}];

  if(fc?.predicted_price!=null&&fc?.last_close!=null){
    const li=recent.length-1,lv=recent[li];
    if(lv!=null){
      const ext=[...labels];
      for(let i=1;i<=h;i++){const d=new Date(labels[labels.length-1]);d.setDate(d.getDate()+i);ext.push(d.toISOString().split('T')[0]);}
      const pred=new Array(li+1).fill(null); pred[li]=lv;
      for(let i=1;i<=h;i++) pred.push(lv+(fc.predicted_price-lv)*(i/h));
      const up=new Array(li+1).fill(null),dn=new Array(li+1).fill(null);
      up[li]=lv; dn[li]=lv;
      for(let i=1;i<=h;i++){const sp=lv*.02*Math.sqrt(i)*1.96;up.push(pred[li+i]+sp);dn.push(pred[li+i]-sp);}
      ds.push(
        {label:'Predicted',data:pred,borderColor:'#F5B84B',borderWidth:2,borderDash:[6,3],fill:false,tension:.3,pointRadius:0},
        {label:'Upper',data:up,borderColor:'transparent',backgroundColor:'rgba(245,184,75,.08)',fill:'+1',tension:.3,pointRadius:0},
        {label:'Lower',data:dn,borderColor:'transparent',backgroundColor:'rgba(245,184,75,.08)',fill:false,tension:.3,pointRadius:0}
      );
      S.charts.fan=new Chart(cv,{type:'line',data:{labels:ext,datasets:ds},options:{
        responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{display:false},tooltip:{backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,padding:10,filter:i=>!['Upper','Lower'].includes(i.dataset.label)}},
        scales:{x:{grid:{color:G,drawBorder:false},ticks:{maxTicksLimit:6,maxRotation:0,font:TF},border:{display:false}},y:{grid:{color:G,drawBorder:false},ticks:{font:TF,callback:v=>'$'+v.toFixed(0)},border:{display:false}}}
      }});
      return;
    }
  }
  S.charts.fan=new Chart(cv,{type:'line',data:{labels,datasets:ds},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:G,drawBorder:false},ticks:{maxTicksLimit:6,maxRotation:0,font:TF},border:{display:false}},y:{grid:{color:G,drawBorder:false},ticks:{font:TF,callback:v=>'$'+v.toFixed(0)},border:{display:false}}}}});
}

/* ══════════════════════════════════════════
   PORTFOLIO
   ══════════════════════════════════════════ */
async function renderPortfolio(){
  const cap=+($('#portfolio-capital')?.value||100000);
  const bl=$('#bl-toggle')?.checked||false;
  try{S.portfolio=await post('/portfolio',{capital:cap,schemes:['max_sharpe','min_variance','risk_parity','hrp','equal_weight'],black_litterman:bl});}catch{return;}
  if(!S.portfolio?.allocations?.length) return;

  // KPIs
  const a=S.portfolio.allocations.find(x=>x.scheme===S.scheme)||S.portfolio.allocations[0];
  const kg=$('#portfolio-kpis');
  if(kg) kg.innerHTML=`
    <div class="kpi"><div class="kpi__lbl">Scheme</div><div class="kpi__val" style="color:var(--amber)">${a.scheme.replace(/_/g,' ')}</div></div>
    <div class="kpi"><div class="kpi__lbl">Exp Return</div><div class="kpi__val" style="color:${a.exp_return>=0?'var(--up)':'var(--down)'}">${pct(a.exp_return*100)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Exp Vol</div><div class="kpi__val">${pct(a.exp_vol*100)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Sharpe</div><div class="kpi__val" style="color:var(--cyan)">${a.sharpe?.toFixed(2)??'\u2014'}</div></div>
    <div class="kpi"><div class="kpi__lbl">Capital</div><div class="kpi__val">${money0(S.portfolio.capital)}</div></div>`;

  // Scheme cards
  const sg=$('#scheme-grid');
  if(sg) sg.innerHTML=S.portfolio.allocations.map(x=>`
    <div class="scheme ${x.scheme===S.scheme?'active':''}" data-s="${x.scheme}">
      <div class="scheme__name">${x.scheme.replace(/_/g,' ')}</div>
      <div class="scheme__row">
        <div class="scheme__stat"><small>Return</small><span class="${cls(x.exp_return)}">${pct(x.exp_return*100)}</span></div>
        <div class="scheme__stat"><small>Vol</small><span>${pct(x.exp_vol*100)}</span></div>
        <div class="scheme__stat"><small>Sharpe</small><span>${x.sharpe?.toFixed(2)??'\u2014'}</span></div>
      </div>
    </div>`).join('');
  $$('.scheme').forEach(c=>c.addEventListener('click',()=>{S.scheme=c.dataset.s;renderPortfolio();}));

  // Allocation doughnut
  renderAllocChart(a);
  // Weights table
  renderWeights(a);
  // Frontier
  renderFrontier();
}

function renderAllocChart(a){
  killChart('alloc');
  const cv=$('#allocation-chart'); if(!cv) return;
  const ents=Object.entries(a.weights).filter(([,w])=>w>.001).sort((a,b)=>b[1]-a[1]);
  S.charts.alloc=new Chart(cv,{type:'doughnut',data:{
    labels:ents.map(([t])=>t),
    datasets:[{data:ents.map(([,w])=>+(w*100).toFixed(1)),backgroundColor:PAL.slice(0,ents.length),borderColor:'#141922',borderWidth:2,hoverOffset:4}]
  },options:{responsive:true,maintainAspectRatio:false,cutout:'55%',plugins:{
    legend:{position:'right',labels:{color:TK,font:TF,boxWidth:8,padding:6}},
    tooltip:{backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,callbacks:{label:c=>`${c.label}: ${c.parsed}%`}}
  }}});
}

function renderWeights(a){
  const w=$('#weights-table'); if(!w) return;
  const ents=Object.entries(a.weights).filter(([,v])=>v>.001).sort((a,b)=>b[1]-a[1]);
  const cap=S.portfolio.capital;
  w.innerHTML=`<table><thead><tr><th>Ticker</th><th>Weight</th><th>Allocation</th></tr></thead><tbody>${
    ents.map(([t,v])=>`<tr><td class="sym">${t}</td><td>${(v*100).toFixed(1)}%</td><td>${money0(v*cap)}</td></tr>`).join('')
  }</tbody></table>`;
}

function renderFrontier(){
  killChart('frontier');
  const cv=$('#frontier-chart'); if(!cv||!S.portfolio) return;
  const pts=S.portfolio.allocations.map(a=>({x:(a.exp_vol??0)*100,y:(a.exp_return??0)*100,lbl:a.scheme.replace(/_/g,' ')}));
  S.charts.frontier=new Chart(cv,{type:'scatter',data:{datasets:[{
    data:pts.map(p=>({x:p.x,y:p.y})),backgroundColor:PAL.slice(0,pts.length),borderColor:PAL.slice(0,pts.length),pointRadius:7,pointHoverRadius:10
  }]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{
    backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,padding:10,
    title:i=>pts[i[0].dataIndex]?.lbl??'',label:c=>`Return: ${c.parsed.y.toFixed(1)}% | Vol: ${c.parsed.x.toFixed(1)}%`
  }},scales:{
    x:{title:{display:true,text:'Volatility (%)',color:TK,font:TF},grid:{color:G,drawBorder:false},ticks:{font:TF},border:{display:false}},
    y:{title:{display:true,text:'Return (%)',color:TK,font:TF},grid:{color:G,drawBorder:false},ticks:{font:TF},border:{display:false}}
  }}});
}

/* ══════════════════════════════════════════
   BACKTEST
   ══════════════════════════════════════════ */
function renderBacktest(){
  const{dates,tickers}=S.prices; if(!dates.length) return;
  const tl=Object.keys(tickers); if(!tl.length) return;

  const rets=[];
  for(let i=1;i<dates.length;i++){
    let s=0,n=0;
    for(const t of tl){const p=tickers[t][i-1],c=tickers[t][i];if(p!=null&&c!=null&&p!==0){s+=(c-p)/p;n++;}}
    rets.push(n>0?s/n:0);
  }

  let eq=100; const eqC=[100];
  for(const r of rets){eq*=(1+r);eqC.push(eq);}
  let peak=100; const dd=eqC.map(v=>{peak=Math.max(peak,v);return((v-peak)/peak)*100;});

  const days=eqC.length;
  const cagr=(Math.pow(eqC[eqC.length-1]/100,252/days)-1)*100;
  const vol=Math.sqrt(rets.reduce((a,r)=>a+r*r,0)/rets.length)*Math.sqrt(252)*100;
  const sharpe=vol>0?cagr/vol:0;
  const maxDD=Math.min(...dd);

  const kg=$('#backtest-kpis');
  if(kg) kg.innerHTML=`
    <div class="kpi"><div class="kpi__lbl">CAGR</div><div class="kpi__val" style="color:${cagr>=0?'var(--up)':'var(--down)'}">${pct(cagr)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Volatility</div><div class="kpi__val">${pct(vol)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Sharpe</div><div class="kpi__val" style="color:var(--cyan)">${sharpe.toFixed(2)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Max Drawdown</div><div class="kpi__val" style="color:var(--down)">${pct(maxDD)}</div></div>`;

  killChart('bt');
  const cv=$('#backtest-chart');
  if(cv) S.charts.bt=new Chart(cv,{type:'line',data:{labels:dates,datasets:[
    {label:'Equity',data:eqC,borderColor:'#5FD4E8',borderWidth:2,fill:false,tension:.3,pointRadius:0,yAxisID:'y'},
    {label:'Drawdown',data:dd,borderColor:'#F0564C',borderWidth:1,fill:true,backgroundColor:'rgba(240,86,76,.1)',tension:.3,pointRadius:0,yAxisID:'y1'}
  ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{
    legend:{display:true,position:'top',labels:{color:TK,font:TF,boxWidth:10}},
    tooltip:{backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,padding:10}
  },scales:{
    x:{grid:{color:G,drawBorder:false},ticks:{maxTicksLimit:10,maxRotation:0,font:TF},border:{display:false}},
    y:{position:'left',grid:{color:G,drawBorder:false},ticks:{font:TF},border:{display:false},title:{display:true,text:'Equity',color:TK,font:TF}},
    y1:{position:'right',grid:{display:false},ticks:{font:TF,callback:v=>v.toFixed(0)+'%'},border:{display:false},title:{display:true,text:'DD',color:TK,font:TF}}
  }}});

  // Table
  const tw=$('#backtest-table');
  if(tw&&S.portfolio) tw.innerHTML=`<table><thead><tr><th>Scheme</th><th>Return</th><th>Vol</th><th>Sharpe</th><th>Ret/Risk</th></tr></thead><tbody>${
    S.portfolio.allocations.map(a=>`<tr><td class="sym">${a.scheme.replace(/_/g,' ')}</td><td class="${cls(a.exp_return)}">${pct((a.exp_return??0)*100)}</td><td>${pct((a.exp_vol??0)*100)}</td><td style="color:var(--cyan)">${a.sharpe?.toFixed(2)??'\u2014'}</td><td>${a.exp_vol>0?((a.exp_return??0)/(a.exp_vol??1)).toFixed(2):'\u2014'}</td></tr>`).join('')
  }</tbody></table>`;
}

/* ══════════════════════════════════════════
   CORRELATIONS
   ══════════════════════════════════════════ */
function renderCorr(){
  const c=S.corr; if(!c) return;
  const{tickers,matrix}=c;
  killChart('corr');
  const cv=$('#corr-chart'); if(!cv) return;

  const data=[],colors=[];
  for(let i=0;i<tickers.length;i++) for(let j=0;j<tickers.length;j++){
    const v=matrix[i][j];
    data.push({x:j,y:i});
    colors.push(v>=0?`rgba(95,212,232,${v*.8})`:`rgba(240,86,76,${Math.abs(v)*.8})`);
  }

  const ptR=Math.max(6,Math.min(18,280/tickers.length));
  S.charts.corr=new Chart(cv,{type:'scatter',data:{datasets:[{data,backgroundColor:colors,pointRadius:ptR,pointStyle:'rectRounded'}]},options:{
    responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false},tooltip:{
      backgroundColor:'#141922',titleColor:'#E8ECF4',bodyColor:'#B0B8C8',borderColor:'#2A3550',borderWidth:1,padding:10,
      title:i=>{const d=data[i[0].dataIndex];return`${tickers[d.y]} \u2014 ${tickers[d.x]}`;},
      label:c=>`Correlation: ${matrix[data[c.dataIndex].y][data[c.dataIndex].x].toFixed(4)}`
    }},
    scales:{
      x:{type:'linear',min:-.5,max:tickers.length-.5,grid:{color:G,drawBorder:false},ticks:{stepSize:1,font:TF,callback:v=>tickers[v]??''},border:{display:false}},
      y:{type:'linear',min:-.5,max:tickers.length-.5,reverse:true,grid:{color:G,drawBorder:false},ticks:{stepSize:1,font:TF,callback:v=>tickers[v]??''},border:{display:false}}
    }
  }});

  // KPIs
  let mx=-2,mn=2,mxp='',mnp='';
  for(let i=0;i<tickers.length;i++) for(let j=i+1;j<tickers.length;j++){
    if(matrix[i][j]>mx){mx=matrix[i][j];mxp=`${tickers[i]}/${tickers[j]}`;}
    if(matrix[i][j]<mn){mn=matrix[i][j];mnp=`${tickers[i]}/${tickers[j]}`;}
  }
  const avg=matrix.flat().reduce((a,v,i)=>{const r=Math.floor(i/tickers.length),c=i%tickers.length;return r!==c?a+v:a;},0)/(tickers.length*(tickers.length-1));

  const kg=$('#corr-kpis');
  if(kg) kg.innerHTML=`
    <div class="kpi"><div class="kpi__lbl">Most Correlated</div><div class="kpi__val" style="color:var(--up)">${mxp}</div><div class="kpi__tag up">${mx.toFixed(3)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Least Correlated</div><div class="kpi__val" style="color:var(--down)">${mnp}</div><div class="kpi__tag down">${mn.toFixed(3)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Avg Correlation</div><div class="kpi__val">${avg.toFixed(3)}</div></div>
    <div class="kpi"><div class="kpi__lbl">Lookback</div><div class="kpi__val">${c.days}d</div></div>`;
}

/* ══════════════════════════════════════════
   DISPATCHER
   ══════════════════════════════════════════ */
function render(v){
  switch(v){
    case 'overview':renderOverview();break;
    case 'forecasts':renderForecasts();break;
    case 'portfolio':renderPortfolio();break;
    case 'backtest':renderBacktest();break;
    case 'correlations':renderCorr();break;
  }
}

/* ══════════════════════════════════════════
   INIT
   ══════════════════════════════════════════ */
async function init(){
  chartDefaults();
  const st=$('#status-text'); if(st) st.textContent='Loading\u2026';
  const ok=await loadAll();
  if(!ok){if(st) st.textContent='Failed to load';return;}
  if(st) st.textContent='Ready';
  const mb=$('#model-badge'); if(mb) mb.textContent=S.meta.latest_run||'v1.0.0';
  const rb=$('#run-badge'); if(rb) rb.textContent=`run: ${S.meta.latest_run||'\u2014'}`;

  initNav(); initMobile();

  // Bind selects
  $('#overview-horizon')?.addEventListener('change',()=>renderOverview());
  $('#forecast-horizon')?.addEventListener('change',()=>{S.horizon=+$('#forecast-horizon').value;S.ticker=null;renderForecasts();});
  $('#portfolio-capital')?.addEventListener('change',()=>renderPortfolio());
  $('#bl-toggle')?.addEventListener('change',()=>renderPortfolio());

  renderTape();
  render('overview');
}

document.addEventListener('DOMContentLoaded',init);
