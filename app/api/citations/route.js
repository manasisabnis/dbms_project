import { pool, mongo } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError, bad, isDate } from '@/lib/http';
export const dynamic = 'force-dynamic';
const TREAT = ['followed', 'referred', 'distinguished', 'overruled'];

export async function GET() {
  const { error } = await requireRole(); if (error) return error;
  try {
    const [rows] = await pool.query(
      `SELECT c.citation_id, c.citation_date, c.context_text, c.page_number,
              a.case_name AS citing_case, b.case_name AS cited_case
       FROM Citation c JOIN Legal_Case a ON a.case_id = c.citing_case_id JOIN Legal_Case b ON b.case_id = c.cited_case_id
       ORDER BY c.citation_date DESC, c.citation_id DESC LIMIT 100`);
    return Response.json({ citations: rows });
  } catch (e) { return dbError(e); }
}

export async function POST(req) {
  const { error } = await requireRole(['admin']); if (error) return error;
  const b = await req.json().catch(() => ({}));
  if (!Number.isInteger(+b.citing_case_id) || !Number.isInteger(+b.cited_case_id)) return bad('Both cases are required');
  if (+b.citing_case_id === +b.cited_case_id) return bad('A case cannot cite itself');
  if (!isDate(b.citation_date)) return bad('Valid citation date required');
  if (b.page_number && !(+b.page_number > 0)) return bad('Page number must be positive');
  const treatment = TREAT.includes(b.treatment) ? b.treatment : 'referred';
  try {
    // Stored procedure runs the INSERT inside a transaction; triggers validate dates and update counts
    const [res] = await pool.query('CALL sp_add_citation(?,?,?,?,?)', [+b.citing_case_id, +b.cited_case_id, b.citation_date, b.context_text || null, b.page_number ? +b.page_number : null]);
    const id = res[0][0].citation_id;
    // NoSQL side: record the evolving citation event
    const db = await mongo();
    await db.collection('citation_events').insertOne({
      citation_id: id, cited_case_id: +b.cited_case_id, citing_case_id: +b.citing_case_id, event_type: 'CITED',
      event_date: new Date(b.citation_date), treatment, context: { text: b.context_text || null, page: b.page_number ? +b.page_number : null }, tags: [],
    });
    return Response.json({ citation_id: id }, { status: 201 });
  } catch (e) { return dbError(e); }
}
