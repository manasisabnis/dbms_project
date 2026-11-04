import { pool } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError, bad, isDate } from '@/lib/http';
export const dynamic = 'force-dynamic';
const TYPES = ['Constitutional','Criminal','Civil','Contract','Property','Tax','Labour','Family'];

export async function GET(req) {
  const { error } = await requireRole(); if (error) return error;
  const p = new URL(req.url).searchParams;
  const w = [], a = [];
  const q = p.get('q')?.trim();
  if (q) { w.push('(MATCH(lc.case_name, lc.decision) AGAINST (? IN NATURAL LANGUAGE MODE) OR lc.case_name LIKE ?)'); a.push(q, `%${q}%`); }
  if (p.get('court_id')) { w.push('lc.court_id = ?'); a.push(+p.get('court_id')); }
  if (p.get('type')) { w.push('lc.case_type = ?'); a.push(p.get('type')); }
  try {
    const [rows] = await pool.query(
      `SELECT lc.case_id, lc.case_name, lc.case_number, lc.judgment_date, lc.case_type, lc.decision, lc.citation_count, co.court_name
       FROM Legal_Case lc JOIN Court co ON co.court_id = lc.court_id
       ${w.length ? 'WHERE ' + w.join(' AND ') : ''}
       ORDER BY lc.citation_count DESC, lc.judgment_date DESC LIMIT 100`, a);
    return Response.json({ cases: rows });
  } catch (e) { return dbError(e); }
}

export async function POST(req) {
  const { error } = await requireRole(['admin']); if (error) return error;
  const b = await req.json().catch(() => ({}));
  const name = String(b.case_name || '').trim();
  if (name.length < 3 || name.length > 500) return bad('Case name must be 3-500 characters');
  if (!b.case_number || String(b.case_number).length > 100) return bad('Case number required (max 100 chars)');
  if (!isDate(b.judgment_date) || new Date(b.judgment_date) > new Date()) return bad('Valid, non-future judgment date required');
  if (!Number.isInteger(+b.court_id)) return bad('Court required');
  if (!TYPES.includes(b.case_type)) return bad('Invalid case type');
  try {
    const [r] = await pool.execute(
      'INSERT INTO Legal_Case(case_name, case_number, judgment_date, case_type, decision, court_id) VALUES (?,?,?,?,?,?)',
      [name, b.case_number, b.judgment_date, b.case_type, b.decision || null, +b.court_id]);
    return Response.json({ case_id: r.insertId }, { status: 201 });
  } catch (e) { return dbError(e); }
}
