'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/client';
import { LineArea, Bars, Donut, HBars } from '@/components/Charts';

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const mlabel = k => MON[+k.slice(5) - 1] + " '" + k.slice(2, 4);
const short = s => (s.length > 34 ? s.slice(0, 32) + '…' : s);

function TrendList({ title, rows, kind }) {
  return (
    <div className="card"><h3>{title}</h3>
      <table><thead><tr><th>Case</th><th>Recent</th><th>Previous</th><th>Change</th></tr></thead>
        <tbody>{rows.length ? rows.map(r => (
          <tr key={r.case_id}><td><Link className="link" href={`/cases/${r.case_id}`}>{short(r.case_name)}</Link></td><td>{r.recent}</td><td>{r.previous}</td>
            <td className={kind === 'up' ? 'delta-up' : 'delta-down'}>{r.delta > 0 ? '▲ +' : '▼ '}{r.delta}</td></tr>
        )) : <tr><td colSpan={4} className="muted">No {kind === 'up' ? 'emerging' : 'declining'} precedents in this window — try another window.</td></tr>}</tbody></table>
    </div>
  );
}

export default function Dashboard() {
  const [a, setA] = useState(null), [t, setT] = useState(null), [w, setW] = useState(180), [err, setErr] = useState('');
  useEffect(() => { api('/api/analytics').then(setA).catch(e => setErr(e.message)); }, []);
  useEffect(() => { api('/api/trends?window=' + w).then(setT).catch(e => setErr(e.message)); }, [w]);
  if (err) return <p className="err">{err}</p>;
  if (!a || !t) return <p className="muted">Loading dashboard…</p>;
  const s = a.stats;
  return (<>
    <h1>Dashboard</h1>
    <p className="muted" style={{ marginTop: 0 }}>How Indian legal precedents are gaining or losing influence. Click any case name for its detailed analysis.</p>
    <div className="kpis">
      <div className="kpi k1"><small>📚 Total cases</small><div className="n">{s.cases}</div></div>
      <div className="kpi k2"><small>🔗 Total citations</small><div className="n">{s.citations}</div></div>
      <div className="kpi k3"><small>🏛 Courts</small><div className="n">{s.courts}</div></div>
      <div className="kpi k4"><small>⚖️ Judges</small><div className="n">{s.judges}</div></div>
      <div className="kpi k5"><small>🚫 Never-cited cases</small><div className="n">{s.never_cited}</div></div>
    </div>

    <div className="grid">
      <div className="card"><h3>Citation activity — last 12 months</h3><LineArea data={t.monthly.map(m => ({ label: mlabel(m.key), value: m.value }))} yLabel="citations / month" /></div>
      <div className="card"><h3>How cases treat precedents</h3><Donut data={t.treatments} centerLabel="citation events" /></div>
    </div>

    <div className="card row">
      <b>📈 Trend window:</b>
      <div className="seg">{[30, 90, 180, 365].map(d => <button key={d} className={w === d ? 'on' : ''} onClick={() => setW(d)}>{d} days</button>)}</div>
      <span className="muted">Compares the last {w} days with the {w} days before (MongoDB aggregation).</span>
    </div>
    <div className="grid">
      <TrendList title="🟢 Emerging precedents" rows={t.emerging} kind="up" />
      <TrendList title="🔴 Declining precedents" rows={t.declining} kind="down" />
    </div>

    <div className="grid">
      <div className="card"><h3>Most cited cases (all time)</h3><HBars data={t.frequent.map(f => ({ label: f.case_name, value: f.total }))} /></div>
      <div className="card"><h3>Citations by court level (citing case)</h3><Donut data={a.byLevel} centerLabel="citations" /></div>
    </div>
    <div className="grid">
      <div className="card"><h3>Citations received by case type</h3><Bars data={a.byType.map(b => ({ label: b.label.slice(0, 6), value: +b.citations }))} yLabel="citations" /></div>
      <div className="card"><h3>Citations by court</h3>
        <table><thead><tr><th>Court</th><th>Cases</th><th>Citations</th></tr></thead>
          <tbody>{a.courts.map(r => <tr key={r.court_name}><td>{r.court_name}<div className="muted">{r.court_level}</div></td><td>{r.cases}</td><td>{r.total_citations}</td></tr>)}</tbody></table></div>
    </div>
    <div className="grid">
      <div className="card"><h3>🏆 Landmark cases <span className="badge neutral">SQL view · ≥5 citations</span></h3>
        <table><tbody>{a.landmarks.map(r => <tr key={r.case_id}><td><Link className="link" href={`/cases/${r.case_id}`}>{short(r.case_name)}</Link></td><td>{r.citation_count}</td></tr>)}</tbody></table></div>
      <div className="card"><h3>Above-average cited <span className="badge neutral">subquery</span></h3>
        <table><tbody>{a.aboveAvg.map(r => <tr key={r.case_id}><td><Link className="link" href={`/cases/${r.case_id}`}>{short(r.case_name)}</Link></td><td>{r.citation_count}</td></tr>)}</tbody></table></div>
    </div>
  </>);
}
