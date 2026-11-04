'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api, useMe } from '@/lib/client';
import { Pager } from '@/components/Charts';

const TYPES = ['Constitutional','Criminal','Civil','Contract','Property','Tax','Labour','Family'];
const blank = { case_name: '', case_number: '', judgment_date: '', case_type: 'Civil', court_id: '', decision: '' };
const PER = 10;

export default function Cases() {
  const me = useMe(), admin = me?.role === 'admin';
  const [rows, setRows] = useState([]), [courts, setCourts] = useState([]), [page, setPage] = useState(1);
  const [fl, setFl] = useState({ q: '', court_id: '', type: '' });
  const [form, setForm] = useState(blank), [msg, setMsg] = useState(null);

  const load = useCallback(() => {
    const p = new URLSearchParams(Object.entries(fl).filter(([, v]) => v));
    api('/api/cases?' + p).then(d => { setRows(d.cases); setPage(1); }).catch(e => setMsg({ e: e.message }));
  }, [fl]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { api('/api/meta').then(d => setCourts(d.courts)).catch(() => {}); }, []);
  const run = async (fn, ok) => { try { await fn(); setMsg({ ok }); load(); } catch (e) { setMsg({ e: e.message }); } };
  const pages = Math.ceil(rows.length / PER), view = rows.slice((page - 1) * PER, page * PER);

  return (<>
    <h1>Cases</h1>
    <p className="muted" style={{ marginTop: 0 }}>{rows.length} case(s). Click a case name to open its analysis.</p>
    <div className="card">
      <div className="row">
        <input placeholder="🔍 Search name or decision text…" value={fl.q} onChange={e => setFl({ ...fl, q: e.target.value })} style={{ flex: 1, minWidth: 220 }} />
        <select value={fl.court_id} onChange={e => setFl({ ...fl, court_id: e.target.value })}><option value="">All courts</option>{courts.map(c => <option key={c.court_id} value={c.court_id}>{c.court_name}</option>)}</select>
        <select value={fl.type} onChange={e => setFl({ ...fl, type: e.target.value })}><option value="">All types</option>{TYPES.map(t => <option key={t}>{t}</option>)}</select>
        <button className="sec" onClick={() => setFl({ q: '', court_id: '', type: '' })}>Reset</button>
      </div>
      {msg && <p className={msg.e ? 'err' : 'ok'}>{msg.e || msg.ok}</p>}
      <table><thead><tr><th>Case</th><th>Court</th><th>Date</th><th>Type</th><th>Cited</th><th></th></tr></thead>
        <tbody>{view.map(r => (
          <tr key={r.case_id}>
            <td><Link className="link" href={`/cases/${r.case_id}`}>{r.case_name}</Link><div className="muted">{r.case_number}</div></td>
            <td>{r.court_name}</td><td>{r.judgment_date}</td><td><span className="badge neutral">{r.case_type}</span></td><td><b>{r.citation_count}</b></td>
            <td style={{ whiteSpace: 'nowrap' }}>
              <Link href={`/cases/${r.case_id}`}><button className="sec">Analyze</button></Link>{' '}
              {admin && <>
                <button className="sec" onClick={() => { const d = prompt('New decision text', r.decision || ''); if (d !== null) run(() => api(`/api/cases/${r.case_id}`, { method: 'PUT', body: JSON.stringify({ decision: d }) }), 'Case updated'); }}>Edit</button>{' '}
                <button className="danger" onClick={() => confirm(`Delete "${r.case_name}"?\n\nIts citations (made by or to this case) will also be removed and counts recalculated.`) && run(() => api(`/api/cases/${r.case_id}?cascade=1`, { method: 'DELETE' }), 'Case and its citations deleted')}>Delete</button>
              </>}
            </td>
          </tr>))}</tbody></table>
      <Pager page={page} pages={pages} setPage={setPage} />
    </div>

    {admin ? (
      <div className="card"><h3>➕ Add a case</h3>
        <div className="row">
          <input placeholder="Case name" value={form.case_name} onChange={e => setForm({ ...form, case_name: e.target.value })} style={{ flex: 2, minWidth: 200 }} />
          <input placeholder="Case number" value={form.case_number} onChange={e => setForm({ ...form, case_number: e.target.value })} />
          <input type="date" value={form.judgment_date} onChange={e => setForm({ ...form, judgment_date: e.target.value })} />
          <select value={form.court_id} onChange={e => setForm({ ...form, court_id: e.target.value })}><option value="">Court…</option>{courts.map(c => <option key={c.court_id} value={c.court_id}>{c.court_name}</option>)}</select>
          <select value={form.case_type} onChange={e => setForm({ ...form, case_type: e.target.value })}>{TYPES.map(t => <option key={t}>{t}</option>)}</select>
        </div>
        <textarea placeholder="Decision (optional)" rows={2} style={{ width: '100%', marginBottom: 8 }} value={form.decision} onChange={e => setForm({ ...form, decision: e.target.value })} />
        <button onClick={() => run(async () => { await api('/api/cases', { method: 'POST', body: JSON.stringify(form) }); setForm(blank); }, 'Case added')}>Add case</button>
      </div>
    ) : me && <p className="muted">👁 Analyst role: read-only. Log in as admin to add, edit or delete.</p>}
  </>);
}
