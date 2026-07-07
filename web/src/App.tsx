import React, { useEffect, useState } from 'react'
export default function App(){
  const [status,setStatus]=useState('loading')
  useEffect(()=>{fetch('http://localhost:8080/health').then(r=>r.json()).then(d=>setStatus(d.status)).catch(()=>setStatus('offline (I am running in demo mode)'))},[])
  return (
    <div style={{fontFamily:'system-ui',padding:24, maxWidth:960, margin:'0 auto'}}>
      <h1>Nexus Dashboard</h1>
      <p><em>I am the autonomous infrastructure control plane.</em></p>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8,marginBottom:16}}>
        <strong>Control Plane Status:</strong> {status}
      </div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:12}}>
        {[
          {l:'Cycles Run',v:'42'},
          {l:'Incidents Detected',v:'17'},
          {l:'Auto-Resolved',v:'14'},
          {l:'MTTR',v:'47s'},
          {l:'Autonomy',v:'L2'},
          {l:'Success Rate',v:'82%'}
        ].map(c=>
          <div key={c.l} style={{border:'1px solid #eee',padding:12,borderRadius:6}}>
            <div style={{fontSize:12,color:'#666'}}>{c.l}</div>
            <div style={{fontSize:24,fontWeight:600}}>{c.v}</div>
          </div>
        )}
      </div>
      <h3 style={{marginTop:24}}>Recent Incidents</h3>
      <p style={{color:'#666'}}>I connect to <code>/v1/incidents</code> in production – showing mock data in Phase 5.</p>
      <table style={{width:'100%',borderCollapse:'collapse'}}>
        <thead><tr style={{textAlign:'left',borderBottom:'2px solid #ddd'}}><th>ID</th><th>Type</th><th>Target</th><th>Status</th><th>MTTR</th></tr></thead>
        <tbody>
          <tr><td>inc-42a7</td><td>scaling_bottleneck</td><td>demo-k8s</td><td>resolved</td><td>47s</td></tr>
          <tr><td>inc-91bd</td><td>security_drift</td><td>demo-aws</td><td>fix_ready</td><td>–</td></tr>
          <tr><td>inc-33f1</td><td>cost_spike</td><td>demo-aws</td><td>resolved</td><td>122s</td></tr>
        </tbody>
      </table>
      <footer style={{marginTop:32,color:'#888',fontSize:13}}>
        Nexus v0.5.0 – I learn from every incident. – <a href="https://github.com/supreeth0008/nexus">GitHub</a>
      </footer>
    </div>
  )
}
