import { pool, mongo } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError, bad } from '@/lib/http';
export const dynamic = 'force-dynamic';

export async function GET(_req, { params }) {
  const { error } = await requireRole(); if (error) return error;
  try {
    const [[c]] = await pool.execute(
      `SELECT lc.*, co.court_name, co.court_level, co.location FROM Legal_Case lc JOIN Court co ON co.court_id = lc.court_id WHERE lc.case_id = ?`, [+params.id]);
    if (!c) return Response.json({ error: 'Not found' }, { status: 404 });
    const [judges] = await pool.execute(
      `SELECT j.judge_name, j.designation, j.appointed_date, j.retired_date, cj.role_in_case
       FROM Case_Judge cj JOIN Judge j ON j.judge_id = cj.judge_id WHERE cj.case_id = ?`, [+params.id]);
    const [statutes] = await pool.execute('SELECT act_name, section, description, enactment_year FROM Statute WHERE case_id = ?', [+params.id]);
    return Response.json({ ...c, judges, statutes });
  } catch (e) { return dbError(e); }
}

export async function PUT(req, { params }) {
  const { error } = await requireRole(['admin']); if (error) return error;
  const { decision } = await req.json().catch(() => ({}));
  if (typeof decision !== 'string' || decision.length > 5000) return bad('Invalid decision text');
  try {
    const [r] = await pool.execute('UPDATE Legal_Case SET decision = ? WHERE case_id = ?', [decision, +params.id]);
    return r.affectedRows ? Response.json({ ok: true }) : Response.json({ error: 'Not found' }, { status: 404 });
  } catch (e) { return dbError(e); }
}

// DELETE /api/cases/:id?cascade=1  -> removes the case AND its citations in one transaction.
// Without cascade, the FK (RESTRICT) blocks deletion of cases that still have citations.
export async function DELETE(req, { params }) {
  const { error } = await requireRole(['admin']); if (error) return error;
  const id = +params.id, cascade = new URL(req.url).searchParams.get('cascade') === '1';
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    if (cascade) await conn.execute('DELETE FROM Citation WHERE citing_case_id = ? OR cited_case_id = ?', [id, id]); // triggers fix counts
    const [r] = await conn.execute('DELETE FROM Legal_Case WHERE case_id = ?', [id]);
    if (!r.affectedRows) { await conn.rollback(); return Response.json({ error: 'Not found' }, { status: 404 }); }
    await conn.commit();
    if (cascade) await (await mongo()).collection('citation_events').deleteMany({ $or: [{ cited_case_id: id }, { citing_case_id: id }] });
    return Response.json({ ok: true });
  } catch (e) { await conn.rollback(); return dbError(e); }
  finally { conn.release(); }
}
