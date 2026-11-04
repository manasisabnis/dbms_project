import { pool, mongo } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError } from '@/lib/http';
export const dynamic = 'force-dynamic';

export async function DELETE(_req, { params }) {
  const { error } = await requireRole(['admin']); if (error) return error;
  try {
    const [r] = await pool.execute('DELETE FROM Citation WHERE citation_id = ?', [+params.id]); // trigger decrements count
    if (!r.affectedRows) return Response.json({ error: 'Not found' }, { status: 404 });
    await (await mongo()).collection('citation_events').deleteOne({ citation_id: +params.id });
    return Response.json({ ok: true });
  } catch (e) { return dbError(e); }
}
