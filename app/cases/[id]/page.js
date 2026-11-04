'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/client';
import { LineArea, Bars, Donut, HBars } from '@/components/Charts';

const TABS = ['Overview', 'Citation Analysis', 'Judges', 'Full Text'];

export default function CaseDetail({ params }) {
  const id = params.id;
  const [c, setC] = useState(null), [an, setAn] = useState(null), [tab, setTab] = useState('Overview'), [yrs, setYrs] = useState(3), [err, setErr] = useState('');
  useEffect(() => { api(`/api/cases/${id}`).then(setC).catch(e => setErr(e.message)); }, [id]);
  useEffect(() => { api(`/api/cases/${id}/analysis?years=${yrs}`).then(setAn).catch(e => setErr(e.message)); }, [id, yrs]);
  if (err) return <p className="err">{err}</p>;
  if (!c || !an) return <p className="muted">Loading…</p>;

  const now = new Date().getFullYear(), years = [];
  for (let y = now - yrs; y <= now; y++) years.push(y);
  const map = Object.fromEntries(an.yearly.map(d => [d._id, d.count]));
  let run = an.yearly.filter(d => d._id < years[0]).reduce((s, d) => s + d.count, 0);
  const yearly = years.map(y => ({ label: String(y), value: map[y] || 0 }));
  const running = years.map(y => { run += map[y] || 0; return { label: String(y), value: run }; });
  const change = an.change === null ? 'New' : (an.change > 0 ? '+' : '') + an.change + '%';

  return (<>
    <Link className="link" href="/cases">← Back to cases</Link>
    <div className="row" style={{ marginTop: 10 }}>
      <h1 style={{ margin: 0 }}>{c.case_name}</h1>
      <span className={`badge ${an.status}`}>{an.status}</span>
    </div>
    <p className="muted">{c.case_type} · {c.case_number} · {c.court_name} · Judgment {c.judgment_date}</p>
    <div className="tabs">{TABS.map(t => <button key={t} className={tab === t ? 'on' : ''} onClick={() => setTab(t)}>{t}</button>)}</div>

    {tab === 'Overview' && <div className="grid">
      <div className="card"><h3>Case details</h3>
        <table><tbody>
          {[['Case number', c.case_number], ['Type', c.case_type], ['Court', `${c.court_name} (${c.court_level})`], ['Location', c.location], ['Judgment date', c.judgment_date], ['Times cited', c.citation_count]].map(([k, v]) => <tr key={k}><th>{k}</th><td>{v}</td></tr>)}
        </tbody></table></div>
      <div className="card"><h3>Statutes referred to</h3>
        <table><thead><tr><th>Act</th><th>Section</th><th>Year</th></tr></thead>
          <tbody>{c.statutes.map((s, i) => <tr key={i}><td>{s.act_name}</td><td>{s.section}</td><td>{s.enactment_year}</td></tr>)}</tbody></table></div>
    </div>}

    {tab === 'Citation Analysis' && <>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="muted">Status over this window: <span className={`badge ${an.status}`}>{an.status}</span> · data as of {new Date().toISOString().slice(0, 10)}</span>
        <div className="seg">{[1, 3, 5].map(y => <button key={y} className={yrs === y ? 'on' : ''} onClick={() => setYrs(y)}>{y} Year{y > 1 ? 's' : ''}</button>)}</div>
      </div>
      <div className="kpis">
        <div className="kpi k1"><small>Total citations</small><div className="n">{an.total}</div></div>
        <div className="kpi k2"><small>Last {yrs} yr (recent window)</small><div className="n">{an.recent}</div></div>
        <div className="kpi k3"><small>Previous {yrs} yr window</small><div className="n">{an.previous}</div></div>
        <div className="kpi k4"><small>Change (recent vs previous)</small><div className="n">{change}</div></div>
      </div>
      <div className="grid">
        <div className="card"><h3>Citation trend over time (running total)</h3><LineArea data={running} yLabel="cumulative citations" /></div>
        <div className="card"><h3>Year-wise citations</h3><Bars data={yearly} color="#10b981" yLabel="citations / year" /></div>
        <div className="card"><h3>Citations by court level</h3><Donut data={an.byLevel} centerLabel="citations" /></div>
        <div className="card"><h3>How later cases treated it</h3><HBars data={an.treatments.map(t => ({ label: t._id, value: t.count }))} /></div>
      </div>
      <div className="card"><h3>Recently cited by</h3>
        <table><thead><tr><th>Date</th><th>Citing case</th><th>Context</th></tr></thead>
          <tbody>{an.citedBy.map((r, i) => <tr key={i}><td>{r.citation_date}</td><td><Link className="link" href={`/cases/${r.case_id}`}>{r.case_name}</Link></td><td>{r.context_text}</td></tr>)}</tbody></table></div>
    </>}

    {tab === 'Judges' && <div className="card"><h3>Bench</h3>
      <table><thead><tr><th>Judge</th><th>Role in case</th><th>Designation</th><th>Appointed</th><th>Retired</th></tr></thead>
        <tbody>{c.judges.map((j, i) => <tr key={i}><td>{j.judge_name}</td><td>{j.role_in_case}</td><td>{j.designation}</td><td>{j.appointed_date}</td><td>{j.retired_date || '—'}</td></tr>)}</tbody></table></div>}

    {tab === 'Full Text' && <div className="card"><h3>Decision</h3><p style={{ lineHeight: 1.7 }}>{c.decision || 'No decision text recorded.'}</p></div>}
  </>);
}
