'use strict';
const $ = id => document.getElementById(id);
const methodPage = document.body.dataset.page === 'methodology';
const mint = '#7de0cc', amber = '#e9b875', muted = '#9babb7';
const riskPurple = '#c084fc', thresholdRed = '#f87171';
const initial = new URLSearchParams(location.search);
let data, request;
let coverageMap, coverageLayers;
const number = (value, digits=1) => value === null || value === undefined || !Number.isFinite(Number(value)) ? 'Unavailable' : Number(value).toLocaleString('en-US', {maximumFractionDigits:digits, minimumFractionDigits:digits});
const dateLabel = value => new Date(value+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const pvalue = value => value == null ? 'Unavailable' : value < .0001 ? '< 0.0001' : number(value,4);
const escapeHTML = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const config = {responsive:true,displaylogo:false,modeBarButtonsToRemove:['select2d','lasso2d','autoScale2d']};
const baseLayout = () => ({paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'DM Sans, sans-serif',color:muted,size:10},margin:{l:45,r:15,t:22,b:45},hovermode:'x unified',xaxis:{gridcolor:'#1b2830',showgrid:false,zeroline:false,tickformat:'%b %Y'},yaxis:{gridcolor:'#243039',zeroline:false},legend:{orientation:'h',y:1.18,x:0,font:{size:10}},hoverlabel:{bgcolor:'#11191f',font:{color:'#e7edf1'}},dragmode:'pan'});
const plot = (id,traces,options={}) => Plotly.react(id,traces,{...baseLayout(),...options},config);
function riskTrend(){return data.trend_details[3];}
function trendLabel(t){if(t.mk_p==null)return 'Not enough observations';if(t.mk_p>=.05)return 'No significant trend';return t.mk_s>0?'Significant upward trend':'Significant downward trend';}
function status(message,error=false){$('status').hidden=false;$('status').textContent=message;$('status').className='status '+(error?'error':'loading');}
function parameters(){
  if(methodPage) return new URLSearchParams(initial.size?initial:{region:'uba',start:'2026-01-01',end:localToday()});
  const q=new URLSearchParams({region:$('region').value,start:$('start').value,end:$('end').value});
  if(q.get('region')==='custom'){q.set('lat',$('latitude').value);q.set('lon',$('longitude').value);}
  return q;
}
function localToday(){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
async function load(){
  if(request)request.abort();request=new AbortController();
  const q=parameters();
  if(!methodPage){if(q.get('start')>q.get('end')){status('Choose a start date before the end date.',true);return;}$('analyze').disabled=true;$('report').hidden=true;}
  status('Retrieving NASA data and calculating the index. Uncached periods may take a few minutes…');
  try{
    if(!window.Plotly)throw new Error('The chart library could not load. Check your internet connection and reload.');
    const response=await fetch('/api/detective?'+q,{signal:request.signal});
    const payload=await response.json();if(!response.ok)throw new Error(typeof payload.detail==='string'?payload.detail:'The analysis could not be completed. Check the dates and coordinates.');
    data=payload;if(!data.timeseries.length)throw new Error('No observations are available for this period.');
    $('status').hidden=true;
    if(methodPage)renderMethod();else renderOverview(q);
  }catch(error){if(error.name!=='AbortError')status('Analysis unavailable. '+error.message,true);}
  finally{if(!methodPage)$('analyze').disabled=false;}
}
function renderOverview(q){
  $('report').hidden=false;
  updateCoverage();
  $('report-location').textContent=`${data.region.name} · ${data.region.latitude.toFixed(2)}°, ${data.region.longitude.toFixed(2)}°`;
  $('period-label').textContent=`${dateLabel(data.period.start)} — ${dateLabel(data.period.end)}`;
  $('method-link').href='/methodology?'+q;
  const t=riskTrend();
  $('trend-preview').textContent=`Mann–Kendall: ${trendLabel(t).toLowerCase()} in the monthly index. ${t.n<24?'This short record cannot establish a long-term climate trend.':'Explore the statistical evidence and assumptions in the methodology.'}`;
  const dates=data.timeseries.map(r=>r.date);
  const events=data.validation.events;
  const shapes=[{type:'line',xref:'paper',x0:0,x1:1,y0:75,y1:75,line:{color:thresholdRed,width:2,dash:'dash'}}];
  events.forEach(e=>shapes.push({type:'rect',xref:'x',yref:'paper',x0:e.start,x1:new Date(new Date(e.end+'T00:00:00Z').getTime()+86400000).toISOString().slice(0,10),y0:0,y1:1,line:{color:amber,width:1,dash:'dot'},fillcolor:'rgba(233,184,117,.12)',layer:'below'}));
  const eventPoints=events.map(e=>({event:e,row:data.timeseries.filter(r=>r.date>=e.start&&r.date<=e.end&&r.flood_risk!=null).sort((a,b)=>b.flood_risk-a.flood_risk)[0]})).filter(e=>e.row);
  const estimates=data.estimated_signals;
  const signalTrace=(kind,name,color,symbol)=>{
    const rows=estimates.events.filter(e=>e.kind===kind);
    return {x:rows.map(e=>e.date),y:rows.map(e=>e.flood_risk),customdata:rows.map(e=>[e.precip_mm,e.precip_7d]),type:'scatter',mode:'markers',name,
      marker:{color,size:10,symbol,line:{color:'#0b1014',width:1.5}},
      hovertemplate:`${name}<br>Index: %{y:.1f} / 100<br>Daily rainfall: %{customdata[0]:.1f} mm<br>7-day rainfall: %{customdata[1]:.1f} mm<br>Exploratory signal · occurrence not confirmed<extra></extra>`};
  };
  plot('risk-chart',[
    {x:dates,y:data.timeseries.map(r=>r.flood_risk),name:'Risk index',type:'scatter',mode:'lines',line:{color:riskPurple,width:2.5},fill:'tozeroy',fillcolor:'rgba(192,132,252,.12)',connectgaps:false,hovertemplate:'%{y:.1f} points<extra>Risk index</extra>'},
    signalTrace('flood_signal','Possible flood','#facc15','diamond'),
    signalTrace('flash_flood_proxy','Possible flash flood','#fb923c','triangle-up'),
    {x:eventPoints.map(e=>e.row.date),y:eventPoints.map(e=>e.row.flood_risk),text:eventPoints.map(e=>e.event.title),type:'scatter',mode:'markers',marker:{color:'#e7edf1',size:14,symbol:'circle-open',line:{width:2}},name:'Official flood',hovertemplate:'%{text}<br>Index: %{y:.1f}<extra>Official record</extra>'}
  ],{showlegend:false,yaxis:{range:[0,106],tickvals:[0,25,50,75,100],gridcolor:'#243039',zeroline:false},shapes,annotations:[{xref:'paper',x:1,y:75,text:'Evaluation threshold · 75',showarrow:false,xanchor:'right',yanchor:'bottom',font:{size:9,color:thresholdRed}}]});
  $('signal-note').textContent=`Estimated signals: index ≥ 75 with rain that day. Orange triangles also require daily rain ≥ the wet-day 95th percentile (${number(estimates.wet_day_p95_mm)} mm). Daily data cannot confirm flood occurrence or rapid onset.`;
  $('risk-chart').removeAllListeners('plotly_click');
  $('risk-chart').on('plotly_click',e=>{const point=e.points[0];if(point?.x)location.href='/methodology?'+q+'&day='+encodeURIComponent(String(point.x).slice(0,10));});
  const v=data.validation;
  $('validation-summary').textContent=v.evaluated?`${v.matched} of ${v.evaluated} evaluated official events reached the 75-point threshold. This is a date comparison, not an accuracy score.`:'No official events can be evaluated for this location and period. The result remains unvalidated.';
  const container=$('event-results');container.replaceChildren();
  if(!events.length){const p=document.createElement('p');p.className='empty-state';p.textContent='No official records in the current register for this selection. Try Ubá with a period including February 23–24, 2026.';container.append(p);}
  events.forEach(e=>{
    const article=document.createElement('article');article.className='event';
    const labels={matched:'Threshold reached',below_threshold:'Below threshold',insufficient_data:'Insufficient data'};
    article.innerHTML=`<div class="event-title"><h4>${escapeHTML(e.title)}</h4><span class="pill ${e.result==='matched'?'':'amber'}">${labels[e.result]}</span></div><p>${e.peak_index==null?'No usable index in the documented date range.':`Peak during the official date range: ${number(e.peak_index)} / 100.`}${e.result==='below_threshold'?' The index did not reach the evaluation threshold for this event.':''}</p>`;
    const link=document.createElement('a');link.textContent=e.source+' ↗';link.href=e.url;link.target='_blank';link.rel='noopener';article.append(link);container.append(article);
  });
  const note=document.createElement('p');note.className='empty-state';note.textContent='The official event register is incomplete. Other risk peaks cannot yet be classified as false alarms.';container.append(note);
  history.replaceState(null,'','/?'+q+'#investigation');
}
function updateCoverage(){
  const {latitude:lat,longitude:lon,name}=data.region;
  $('coverage-location').textContent=`${name} · ${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
  $('coverage-coordinates').textContent=`${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
  $('coverage-size').textContent=`≈ 56 × ${Math.round(111.32 * .625 * Math.cos(lat * Math.PI / 180))} km`;
  if($('coverage').open)renderCoverageMap();
}
function renderCoverageMap(){
  if(!data || !$('coverage').open)return;
  const mapStatus=$('map-status');
  if(!window.L){mapStatus.textContent='The interactive map could not load. Coordinates and grid dimensions are shown alongside it. Check your connection and reload to retry.';mapStatus.hidden=false;return;}
  if(!coverageMap){
    coverageMap=L.map('coverage-map',{scrollWheelZoom:false,attributionControl:true});
    // Same public basemap endpoint as the original index; no token or API key.
    const tiles=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',{
      attribution:'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
      maxZoom:19,
    }).addTo(coverageMap);
    tiles.on('tileerror',()=>{mapStatus.textContent='Basemap unavailable. The location and approximate grid outline are still shown.';mapStatus.hidden=false;});
    tiles.on('tileload',()=>{mapStatus.hidden=true;});
    coverageLayers=L.layerGroup().addTo(coverageMap);
    L.control.scale({imperial:false,position:'bottomleft'}).addTo(coverageMap);
    new ResizeObserver(()=>coverageMap.invalidateSize({pan:false})).observe($('coverage-map'));
  }
  coverageLayers.clearLayers();
  const {latitude:lat,longitude:lon,name}=data.region;
  // Illustrate nominal grid dimensions around the query point, not an exact source cell.
  const bounds=[[Math.max(-90,lat-.25),lon-.3125],[Math.min(90,lat+.25),lon+.3125]];
  // A saturated blue boundary and restrained fill keep the coverage easy to locate.
  L.rectangle(bounds,{color:'#1463eb',weight:3,opacity:1,fillColor:'#1463eb',fillOpacity:.12,lineJoin:'round'}).addTo(coverageLayers).bindTooltip('Approximate grid dimensions · centered on selected location');
  const popup=document.createElement('div');popup.textContent=`${name} · ${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
  L.circleMarker([lat,lon],{radius:9,color:'#101820',weight:3,fillColor:'#ffffff',fillOpacity:1}).addTo(coverageLayers).bindPopup(popup);
  L.circleMarker([lat,lon],{radius:3,color:'#101820',weight:1,fillColor:'#101820',fillOpacity:1,interactive:false}).addTo(coverageLayers);
  requestAnimationFrame(()=>{coverageMap.invalidateSize({pan:false});coverageMap.fitBounds(bounds,{padding:[28,28],maxZoom:10,animate:false});});
}
const trendNames=['Monthly precipitation (mm)','Deseasonalized precipitation (mm/day)','Root-zone wetness (%)','Flood risk index (points)','Annual precipitation (mm)','Compound-condition days / year','Extreme-rain days / year'];
function renderMethod(){
  $('method-report').hidden=false;
  const q=parameters();q.delete('day');$('back-link').href='/?'+q+'#investigation';
  $('selected-day').replaceChildren(...data.timeseries.map(row=>{const option=document.createElement('option');option.value=row.date;option.textContent=dateLabel(row.date);return option;}));
  const selected = initial.get('day');
const validRows = data.timeseries.filter(r => r.flood_risk != null);
const targetRows = validRows.length ? validRows : data.timeseries;
const middleDate = targetRows[Math.floor(targetRows.length / 2)].date;

$('selected-day').value = data.timeseries.some(r => r.date === selected) 
  ? selected 
  : middleDate;
  const t=riskTrend();$('trend-label').textContent=trendLabel(t);$('mk-p').textContent=pvalue(t.mk_p);$('slope').textContent=t.slope_per_year==null?'Unavailable':number(t.slope_per_year,2)+' pts / year';
  $('trend-summary').textContent=`${t.n} monthly observations · α = 0.05 · ${data.region.name}`;
  $('coverage-note').textContent=t.n<24?'Short record: use multiple years to investigate long-term trends. Seasonal cycles, incomplete periods and autocorrelation can affect these basic tests.':'The basic tests do not correct for autocorrelation. Seasonal cycles and incomplete periods may affect the results.';
  $('trend-table').innerHTML=data.trend_details.map((r,i)=>`<tr><td>${trendNames[i]}<br><small>${i<4?'Monthly':'Annual'}</small></td><td>${r.n}</td><td>${number(r.slope_per_year,3)}</td><td>${pvalue(r.ols_p)}</td><td>${pvalue(r.mk_p)}</td><td>${trendLabel(r)}</td></tr>`).join('');
  $('selected-day').onchange=renderDay;renderDay();
}
function renderDay(){
  const selected=$('selected-day').value,row=data.timeseries.find(r=>r.date===selected);
  $('selected-date').textContent=dateLabel(selected);$('selected-score').textContent=number(row.flood_risk);
  $('selected-level').textContent=row.flood_risk==null?'Unavailable':row.flood_risk<=40?'Low':row.flood_risk<=60?'Moderate':row.flood_risk<=75?'High':'Critical';
  const terms=[['7-day rainfall',35,'rain_contribution'],['Root-zone soil wetness',30,'soil_contribution'],['Antecedent rainfall (API)',20,'api_contribution'],['Rainfall anomaly',15,'anomaly_contribution']];
  $('contributions').innerHTML=terms.map(([label,weight,key])=>`<tr><td>${label}</td><td>${weight}%</td><td>${number(row[key],2)}</td></tr>`).join('');$('contribution-total').textContent=number(row.flood_risk,2);
  const rows=data.timeseries,dates=rows.map(r=>r.date),shapes=[{type:'line',x0:selected,x1:selected,y0:0,y1:1,yref:'paper',line:{color:'#e7edf1',width:1,dash:'dot'}}];
  const trace=(key,name,color)=>({x:dates,y:rows.map(r=>r[key]),type:'scatter',mode:'lines',name,line:{color,width:1.7},connectgaps:false});
  plot('rain-chart',[{x:dates,y:rows.map(r=>r.precip_mm),type:'bar',name:'Daily rainfall',marker:{color:mint}},trace('precip_7d','7-day total',amber)],{shapes});
  plot('soil-chart',[trace('soil_surface_pct','Surface',mint),trace('soil_root_pct','Root zone',amber)],{shapes,yaxis:{range:[0,100],gridcolor:'#243039'}});
  plot('api-chart',[trace('api','API',mint)],{shapes,showlegend:false});
  plot('anomaly-chart',[{x:dates,y:rows.map(r=>r.precip_anomaly),type:'bar',name:'Anomaly',marker:{color:rows.map(r=>r.precip_anomaly>=0?mint:amber)}}],{shapes,showlegend:false});
  initial.set('day',selected);history.replaceState(null,'','/methodology?'+initial);
}
if(!methodPage){
  $('coverage').addEventListener('toggle',()=>{if($('coverage').open)renderCoverageMap();});
  $('end').value=initial.get('end')||localToday();$('start').value=initial.get('start')||'2026-01-01';$('start').max=$('end').max=localToday();
  if(initial.has('region')&&[...$('region').options].some(o=>o.value===initial.get('region')))$('region').value=initial.get('region');
  $('latitude').value=initial.get('lat')||'';$('longitude').value=initial.get('lon')||'';
  function coordinates(){const custom=$('region').value==='custom';document.querySelectorAll('.custom-field').forEach(e=>e.hidden=!custom);$('latitude').required=$('longitude').required=custom;}
  $('region').addEventListener('change',coordinates);coordinates();$('analysis-form').addEventListener('submit',event=>{event.preventDefault();load();});
}
load();
