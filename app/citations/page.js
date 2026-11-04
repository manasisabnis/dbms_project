'use client';
import { useEffect, useState, useCallback } from 'react';
import { api, useMe } from '@/lib/client';
import { Pager } from '@/components/Charts';

const blank = { citing_case_id: '', cited_case_id: '', citation_date: '', page_number: '', treatment: 'followed', context_text: '' };

export default function Citations() {
  const me = useMe(), admin = me?.role === 'admin';
  const [rows, setRows] = useState([]), [cases, setCases] = useState([]), [f, setF] = useState(blank), [msg, setMsg] = useState(null), [page, setPage] = useState(1);
  const load = useCallback(() => { api('/api/citations').then(d => setRows(d.citations)).catch(e => setMsg({ e: e.message })); }, []);
  useEffect(() => { load(); api('/api/meta').then(d => setCases(d.cases)).catch(() => {}); }, [load]);
  const run = async (fn, ok) => { try { await fn(); setMsg({ ok }); load(); } catch (e) { setMsg({ e: e.message }); } };
  const opts = <>{<option value="">Select case…</option>}{cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_name} ({c.judgment_date})</option>)}</>;

  const pages = Math.ceil(rows.length / 10), view = rows.slice((page - 1) * 10, page * 10);
  return (<>
    <h1>Citations</h1>
    {admin && <div className="card"><h3>Record a citation (admin)</h3>
      <p className="muted">Runs the sp_add_citation stored procedure (transaction); DB triggers reject citations of later judgments and update citation counts. A MongoDB event is also recorded.</p>
      <div className="row">
        <select value={f.citing_case_id} onChange={e => setF({ ...f, citing_case_id: e.target.value })}>{opts}</select>
        <span>cites</span>
        <select value={f.cited_case_id} onChange={e => setF({ ...f, cited_case_id: e.target.value })}>{opts}</select>
        <input type="date" value={f.citation_date} onChange={e => setF({ ...f, citation_date: e.target.value })} />
        <input type="number" min="1" placeholder="Page" value={f.page_number} onChange={e => setF({ ...f, page_number: e.target.value })} style={{ width: 80 }} />
        <select value={f.treatment} onChange={e => setF({ ...f, treatment: e.target.value })}>{['followed','referred','distinguished','overruled'].map(t => <option key={t}>{t}</option>)}</select>
      </div>
      <input placeholder="Context text" value={f.context_text} onChange={e => setF({ ...f, context_text: e.target.value })} style={{ width: '100%', marginBottom: 8 }} />
      <button onClick={() => run(async () => { await api('/api/citations', { method: 'POST', body: JSON.stringify(f) }); setF(blank); }, 'Citation recorded')}>Add citation</button>
    </div>}
    {msg && <p className={msg.e ? 'err' : 'ok'}>{msg.e || msg.ok}</p>}
    <div className="card"><h3>Latest citations</h3>
      <table><thead><tr><th>Date</th><th>Citing case</th><th>Cited case</th><th>Context</th><th>Pg</th><th></th></tr></thead>
        <tbody>{view.map(r => (
          <tr key={r.citation_id}><td>{r.citation_date}</td><td>{r.citing_case}</td><td>{r.cited_case}</td><td>{r.context_text}</td><td>{r.page_number}</td>
            <td>{admin && <button className="danger" onClick={() => confirm('Delete citation?') && run(() => api('/api/citations/' + r.citation_id, { method: 'DELETE' }), 'Citation deleted')}>Delete</button>}</td></tr>))}</tbody></table>
      <Pager page={page} pages={pages} setPage={setPage} />
    </div>
  </>);
}
