/* Competitive Mobility Project — this season's tables, provisional (D293). Results: openfootball (public domain). */
(function(){
const FEEDS={ENG:['1','2'],ESP:['1'],ITA:['1'],GER:['1'],FRA:['1']};
const ord=n=>n+(n%100>=11&&n%100<=13?'th':({1:'st',2:'nd',3:'rd'}[n%10]||'th'));
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function getJSON(u){const r=await fetch(u,{cache:'no-cache'});if(!r.ok)throw new Error(u);return r.json();}
async function load(){
  const meta=await getJSON('/data/ceilings.json');let live=null,src='live';
  try{live=await getJSON('/api/live');}catch(e){try{live=await getJSON('/data/live_snapshot.json');src='snapshot';}catch(e2){}}
  return {meta,live,src};
}
function table(ms){const t={};for(const [d,a,b,x,y] of ms){for(const [m,f,g] of [[a,x,y],[b,y,x]]){const r=t[m]||(t[m]={team:m,P:0,W:0,D:0,L:0,GF:0,GA:0,Pts:0});r.P++;r.GF+=f;r.GA+=g;if(f>g){r.W++;r.Pts+=3}else if(f==g){r.D++;r.Pts++}else r.L++;}}
  return Object.values(t).sort((p,q)=>q.Pts-p.Pts||(q.GF-q.GA)-(p.GF-p.GA)||q.GF-p.GF||p.team.localeCompare(q.team));}
function band(tier,pos,N){if(tier==1){if(pos==1)return'1';if(pos<=4)return'2-4';if(pos<=7)return'5-7';if(pos>N-(N<=18?2:3))return'rel';return pos<=12?'8-12':'13+';}
  if(pos<=2)return'prom';if(pos>N-3)return'rel';return pos<=N/2?'top':'bot';}
function phrase(s,n,h){if(n<30)return h+' of '+n;if(h==0)return'none of '+n;if(s>=0.95)return'almost all';if(s>=0.25)return'about '+Math.round(s*10)+' in 10';if(s<1/30)return h+' of '+n;return'about 1 in '+Math.round(1/s);}
const normN=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/&/g,' and ').replace(/[^a-z0-9 ]/g,' ').split(' ').filter(w=>w&&!['fc','afc','cf','ac','sc','ssc','as','us','rc','cd','ud','sd','rcd','acf','cfc','club','de','calcio','the','1846','1899','1900','1901','1904','1905','1907','1909','1910','1913','1919'].includes(w)).join(' ');
function finder(meta,c){const F=meta.feed[c]||{};const idx={};for(const [team,v] of Object.entries(F)){idx[normN(team)]=v;idx[normN(v[1])]=v;}
  return (name,short)=>F[name]||idx[normN(name)]||idx[normN(short||'')]||null;}
function leagues(live,meta){const out=[];if(!live)return out;
  if(live.standings){for(const c in FEEDS)for(const t of FEEDS[c]){const S=(live.standings[c]||{})[t];if(!S||!S.rows||!S.rows.length)continue;const find=finder(meta,c);
      const T=S.rows.map(([pos,name,short,P,GF,GA,Pts])=>({team:name,short,P,GF,GA,Pts,m:find(name,short)}));const N=T.length;const played=T.reduce((a,r)=>a+r.P,0)/N;
      out.push({c,t:+t,T,N,played,last:(live.fetched||'').slice(0,10),matchday:S.matchday,mid:played>=N-1,fresh:true});}
    return out;}
  for(const c in FEEDS)for(const t of FEEDS[c]){const ms=(live.leagues[c]||{})[t];if(!ms||!ms.length)continue;const find=finder(meta,c);
  const T=table(ms).map(r=>Object.assign(r,{m:find(r.team)}));const N=T.length;const played=T.reduce((a,r)=>a+r.P,0)/N;const last=ms.reduce((a,m)=>m[0]>a?m[0]:a,'');out.push({c,t:+t,T,N,played,last,mid:played>=N-1});}return out;}
function when(d){const x=new Date(d+'T12:00:00Z');return x.toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'});}
function stale(d,L){if(L&&L.fresh)return false;return (Date.now()-new Date(d+'T12:00:00Z'))/864e5>10;}
function ceilHTML(meta,c,tier,b,lead){const rows=((meta.ceilings[c]||{})[tier]||{})[b];if(!rows)return'';const [g,lab,n,h,s,f,l]=rows[0];const big=phrase(s,n,h);
  let on=Math.round(s*10),ic='<span class="icons">'+Array.from({length:10},(_,i)=>'<span class="'+(i<on?'on':'')+'"></span>').join('')+'</span>';
  return '<div class="ceiling"><p class="q"><span class="live">Provisional</span> '+esc(lead)+'</p><p class="headline">'+esc(big[0].toUpperCase()+big.slice(1))+'</p>'+ic+
    '<p>Of the '+n+' times a club '+esc(meta.labels[c][tier][b])+', '+h+' '+esc(lab)+'.</p>'+
    (rows.length>1?'<table class="goals">'+rows.slice(1).map(r=>'<tr><td>'+esc(r[1][0].toUpperCase()+r[1].slice(1))+'</td><td class="v">'+esc(phrase(r[4],r[2],r[3]))+'</td></tr>').join('')+'</table>':'')+'</div>';}
async function club(box){const {meta,live,src}=await load();const c=box.dataset.c,k=box.dataset.k;
  for(const L of leagues(live,meta)){if(L.c!==c)continue;const i=L.T.findIndex(r=>r.m&&r.m[2]===k);if(i<0)continue;
    const r=L.T[i],pos=i+1,name=meta.the[c][L.t];
    let h='<h3>This season so far <span class="live">Provisional</span></h3><p>'+ord(pos)+' in '+esc(name)+' after '+r.P+' games ('+r.Pts+' points). '+(L.fresh?'Table as of '+when(L.last)+' (football-data.org).':'Results up to '+when(L.last)+'.'+(stale(L.last,L)?' The public results file this page uses has not been updated since then.':''))+'</p>';
    if(L.mid){h+=ceilHTML(meta,c,L.t,band(L.t,pos,L.N),'If the season ended now: based on '+ord(pos)+' in '+name)+'<p class="note">From the halfway point of the season the figure follows the live position. '+(L.fresh?'The table is provisional until the league publishes its final table.':'Tables here use points, goal difference and goals scored only; point deductions and the league\'s own tie-breaks are applied when the final table is published.')+'</p>';}
    else h+='<p class="note">Until the halfway point of the season, the figure above uses last season\'s final position.</p>';
    box.innerHTML=h;return;}
}
async function page(root){const {meta,live,src}=await load();const Ls=leagues(live,meta);if(!Ls.length){root.innerHTML='<p class="muted">This season\'s results could not be loaded just now.</p>';return;}
  let h='';for(const L of Ls){const name=meta.tiers[L.c][L.t];
    h+='<h2>'+esc(name)+'</h2><p class="note">'+esc(meta.country[L.c])+' · '+Math.round(L.played)+' of '+(2*(L.N-1))+' games played · '+(L.fresh?'table as of '+when(L.last)+' · source: football-data.org':'results up to '+when(L.last)+(stale(L.last,L)?' · <strong>the public results file has not been updated since then</strong>':''))+'</p>';
    h+='<div class="scroll"><table class="t"><tr><th class="n">#</th><th>Club</th><th class="n">P</th><th class="n">GD</th><th class="n">Pts</th><th>What happened to clubs that finished here</th></tr>';
    L.T.forEach((r,i)=>{const m=r.m;const b=band(L.t,i+1,L.N);const rows=((meta.ceilings[L.c]||{})[L.t]||{})[b];
      const pre={rel:'Relegated: ',prom:'Promoted: ','1':'Champions: '}[b]||'';const ce=rows?pre+esc(phrase(rows[0][4],rows[0][2],rows[0][3]))+' '+esc(rows[0][1]):'';
      h+='<tr><td class="n">'+(i+1)+'</td><td>'+(m?'<a href="/clubs/'+m[0]+'.html">'+esc(m[1])+'</a>':esc(r.short||r.team))+'</td><td class="n">'+r.P+'</td><td class="n">'+(r.GF-r.GA>0?'+':'')+(r.GF-r.GA)+'</td><td class="n">'+r.Pts+'</td><td class="small">'+ce+'</td></tr>';});
    h+='</table></div>';}
  root.innerHTML=h+(src==='snapshot'?'<p class="note">Showing the copy saved when the site was built; the live file could not be reached.</p>':'');}
const box=document.getElementById('livebox');if(box)club(box).catch(()=>{});
const root=document.getElementById('liveroot');if(root)page(root).catch(()=>{root.innerHTML='<p class="muted">This season\'s results could not be loaded just now.</p>';});
})();
