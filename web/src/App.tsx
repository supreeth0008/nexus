import React, { useEffect, useState } from 'react'

type Incident = {id:string; type:string; target:string; status:string; severity:string; mttr?:number}
type Metric = {label:string; value:string; delta?:string; good?:boolean}

const mockIncidents: Incident[] = [
  {id:'inc-42a7f91e', type:'scaling_bottleneck', target:'demo-k8s', status:'resolved', severity:'high', mttr:47},
  {id:'inc-91bd03c4', type:'security_drift', target:'demo-aws', status:'fix_ready', severity:'critical'},
  {id:'inc-33f19a22', type:'cost_spike', target:'demo-aws', status:'resolved', severity:'medium', mttr:122},
  {id:'inc-a71e5d09', type:'reliability_degradation', target:'demo-prom', status:'verifying', severity:'high'},
]

export default function App(){
  const [apiStatus,setApiStatus] = useState<'checking'|'ok'|'offline'>('checking')
  const [autonomy,setAutonomy] = useState(2)
  const [cycleRunning,setCycleRunning] = useState(false)

  useEffect(()=>{
    fetch('http://localhost:8080/health').then(r=>r.json()).then(()=>setApiStatus('ok')).catch(()=>setApiStatus('offline'))
  },[])

  const metrics: Metric[] = [
    {label:'Cycles (24h)', value:'42', delta:'+8'},
    {label:'Incidents detected', value:'17', delta:'+3'},
    {label:'Auto-resolved', value:'14', delta:'+2', good:true},
    {label:'MTTR', value:'47s', delta:'-12s', good:true},
    {label:'Success rate', value:'82%', delta:'+5%', good:true},
    {label:'Policy denies', value:'3', delta:'0'},
  ]

  const runCycle = ()=>{
    setCycleRunning(true)
    setTimeout(()=>setCycleRunning(false), 2200)
  }

  return (
    <div style={{fontFamily:'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto', background:'#f6f7fb', minHeight:'100vh', color:'#111827'}}>
      {/* Topbar */}
      <header style={{background:'#0f172a', color:'white', padding:'14px 28px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <div style={{display:'flex', alignItems:'center', gap:12}}>
          <div style={{width:32,height:32,borderRadius:8,background:'linear-gradient(135deg,#6366f1,#8b5cf6)', display:'flex',alignItems:'center',justifyContent:'center', fontWeight:700}}>N</div>
          <div>
            <div style={{fontWeight:700, letterSpacing:0.3}}>Nexus</div>
            <div style={{fontSize:11, opacity:0.8}}>Autonomous Infrastructure Control Plane – v0.6.1</div>
          </div>
        </div>
        <div style={{display:'flex', gap:16, alignItems:'center', fontSize:13}}>
          <span style={{opacity:0.9}}>API: <b style={{color: apiStatus==='ok' ? '#4ade80' : '#fbbf24'}}>{apiStatus}</b></span>
          <span>Autonomy: <b>L{autonomy}</b></span>
          <button onClick={()=>setAutonomy(a=> (a+1)%5)} style={{background:'#1e293b', color:'white', border:'1px solid #334155', padding:'6px 10px', borderRadius:6, cursor:'pointer', fontSize:12}}>Change level</button>
        </div>
      </header>

      <main style={{maxWidth:1100, margin:'0 auto', padding:'28px 24px'}}>
        {/* KPI grid */}
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:14, marginBottom:22}}>
          {metrics.map(m=>(
            <div key={m.label} style={{background:'white', border:'1px solid #e5e7eb', borderRadius:12, padding:16, boxShadow:'0 1px 2px rgba(0,0,0,0.04)'}}>
              <div style={{fontSize:12, color:'#6b7280', marginBottom:6}}>{m.label}</div>
              <div style={{display:'flex', alignItems:'baseline', gap:8}}>
                <div style={{fontSize:26, fontWeight:700}}>{m.value}</div>
                {m.delta && <div style={{fontSize:12, color: m.good ? '#059669' : '#6b7280'}}>{m.delta}</div>}
              </div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div style={{background:'white', border:'1px solid #e5e7eb', borderRadius:12, padding:16, marginBottom:22, display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:12}}>
          <div>
            <div style={{fontWeight:600, marginBottom:4}}>Closed-loop cycle</div>
            <div style={{fontSize:13, color:'#4b5563'}}>I run: Observe → Detect → Diagnose → Generate → Validate → Policy → Apply → Verify → Learn</div>
          </div>
          <div style={{display:'flex', gap:8}}>
            <button onClick={runCycle} disabled={cycleRunning} style={{background: cycleRunning ? '#9ca3af' : '#4f46e5', color:'white', border:'none', padding:'9px 14px', borderRadius:8, cursor: cycleRunning ? 'not-allowed':'pointer', fontWeight:600}}>
              {cycleRunning ? 'Running…' : 'Run cycle'}
            </button>
            <button style={{background:'white', border:'1px solid #d1d5db', padding:'9px 14px', borderRadius:8, cursor:'pointer'}}>Observe</button>
            <button style={{background:'white', border:'1px solid #d1d5db', padding:'9px 14px', borderRadius:8, cursor:'pointer'}}>Detect</button>
          </div>
        </div>

        <div style={{display:'grid', gridTemplateColumns:'2fr 1fr', gap:16}}>
          {/* Incidents */}
          <div style={{background:'white', border:'1px solid #e5e7eb', borderRadius:12, overflow:'hidden'}}>
            <div style={{padding:'14px 16px', borderBottom:'1px solid #f0f0f0', fontWeight:600, display:'flex', justifyContent:'space-between'}}>
              <span>Active incidents – I detected these automatically</span>
              <span style={{fontSize:12, fontWeight:500, color:'#6b7280'}}>4 total • 2 resolved today</span>
            </div>
            <table style={{width:'100%', borderCollapse:'collapse', fontSize:14}}>
              <thead>
                <tr style={{background:'#f9fafb', color:'#6b7280', textAlign:'left'}}>
                  <th style={{padding:'10px 16px'}}>ID</th><th>Type</th><th>Target</th><th>Severity</th><th>Status</th><th>MTTR</th>
                </tr>
              </thead>
              <tbody>
                {mockIncidents.map(inc=>(
                  <tr key={inc.id} style={{borderTop:'1px solid #f1f5f9'}}>
                    <td style={{padding:'12px 16px', fontFamily:'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize:12}}>{inc.id.slice(0,10)}</td>
                    <td>{inc.type}</td>
                    <td>{inc.target}</td>
                    <td><span style={{
                      padding:'3px 8px', borderRadius:999, fontSize:11, fontWeight:600,
                      background: inc.severity==='critical' ? '#fee2e2' : inc.severity==='high' ? '#ffedd5' : '#e0f2fe',
                      color: inc.severity==='critical' ? '#b91c1c' : inc.severity==='high' ? '#9a3412' : '#075985'
                    }}>{inc.severity}</span></td>
                    <td><span style={{
                      padding:'3px 8px', borderRadius:6, fontSize:11,
                      background: inc.status==='resolved' ? '#ecfdf5' : inc.status==='verifying' ? '#eff6ff' : '#fffbeb',
                      color: inc.status==='resolved' ? '#065f46' : inc.status==='verifying' ? '#1e40af' : '#92400e',
                      border:'1px solid #e5e7eb'
                    }}>{inc.status}</span></td>
                    <td>{inc.mttr ? `${inc.mttr}s` : '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{padding:'10px 16px', fontSize:12, color:'#6b7280', borderTop:'1px solid #f0f0f0'}}>
              I enforce: every incident → diagnosis with confidence score → IaC fix → OPA policy gate → GitOps PR → verify → learn
            </div>
          </div>

          {/* Right column */}
          <div style={{display:'flex', flexDirection:'column', gap:16}}>
            <div style={{background:'white', border:'1px solid #e5e7eb', borderRadius:12, padding:16}}>
              <div style={{fontWeight:600, marginBottom:8}}>Policy gate – OPA</div>
              <div style={{fontSize:13, lineHeight:1.5, color:'#374151'}}>
                • Level {autonomy}: {['Observe only','Recommend via PR','Auto-fix low risk','Auto-fix with policy gate','Full autonomy'][autonomy]}<br/>
                • I evaluate every action in OPA before apply<br/>
                • I sign audit entries with HMAC-SHA256<br/>
                • I redact secrets in all API responses
              </div>
            </div>

            <div style={{background:'white', border:'1px solid #e5e7eb', borderRadius:12, padding:16}}>
              <div style={{fontWeight:600, marginBottom:10}}>MTTR trend – I am improving</div>
              {/* Simple inline SVG sparkline */}
              <svg viewBox="0 0 300 80" width="100%" height="80" style={{overflow:'visible'}}>
                <polyline fill="none" stroke="#4f46e5" strokeWidth="2.5"
                  points="0,60 40,55 80,50 120,48 160,38 200,34 240,28 280,22" />
                {[0,40,80,120,160,200,240,280].map((x,i)=> [x,[60,55,50,48,38,34,28,22][i]]).map(([x,y],i)=>
                  <circle key={i} cx={x} cy={y} r="3" fill="#4f46e5" />
                )}
                <text x="0" y="78" fontSize="10" fill="#6b7280">-7d</text>
                <text x="260" y="78" fontSize="10" fill="#6b7280">now</text>
              </svg>
              <div style={{fontSize:12, color:'#059669', marginTop:4}}>↓ 38% vs last week – I learned 3 new patterns</div>
            </div>

            <div style={{background:'#0f172a', color:'white', borderRadius:12, padding:16}}>
              <div style={{fontWeight:600, marginBottom:6}}>Security – hardened</div>
              <ul style={{margin:0, paddingLeft:18, fontSize:13, lineHeight:1.6, opacity:0.95}}>
                <li>API key + Bearer OIDC – I verify with constant-time HMAC</li>
                <li>RBAC: reader / operator / admin</li>
                <li>Rate limit: 120 req/min/IP – I throttle</li>
                <li>Audit ledger: HMAC-SHA256 signed</li>
                <li>Secrets redaction in all logs</li>
                <li>TLS ready, SOPS+Age recommended</li>
              </ul>
            </div>
          </div>
        </div>

        <footer style={{marginTop:28, color:'#6b7280', fontSize:12, display:'flex', justifyContent:'space-between', flexWrap:'wrap', gap:8}}>
          <span>Nexus v0.6.1 – Python • Typer • Pydantic • SQLAlchemy • FastAPI – I heal your cloud autonomously</span>
          <span><a href="https://github.com/supreeth0008/nexus" style={{color:'#4f46e5', textDecoration:'none'}}>github.com/supreeth0008/nexus</a></span>
        </footer>
      </main>
    </div>
  )
}
