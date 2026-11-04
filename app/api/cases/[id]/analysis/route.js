import { pool, mongo } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError } from '@/lib/http';
export const dynamic = 'force-dynamic';

// Per-case citation analysis: MongoDB aggregation ($facet) for time series + SQL JOIN/GROUP BY for court levels
export async function GET(req, { params }) {
  const { error } = await requireRole(); if (error) return error;
  const id = +params.id;
  const y = [1, 3, 5].includes(+new URL(req.url).searchParams.get('years')) ? +new URL(req.url).searchParams.get('years') : 3;
  const now = new Date(), rs = new Date(now), ps = new Date(now);
  rs.setFullYear(now.getFullYear() - y); ps.setFullYear(now.getFullYear() - 2 * y);
  try {
    const db = await mongo();
    const [r] = await db.collection('citation_events').aggregate([
      { $match: { cited_case_id: id } },
      { $facet: {
        yearly: [{ $group: { _id: { $year: '$event_date' }, count: { $sum: 1 } } }, { $sort: { _id: 1 } }],
        treatments: [{ $group: { _id: '$treatment', count: { $sum: 1 } } }, { $sort: { count: -1 } }],
        windows: [{ $group: { _id: null, total: { $sum: 1 },
          recent: { $sum: { $cond: [{ $gte: ['$event_date', rs] }, 1, 0] } },
          previous: { $sum: { $cond: [{ $and: [{ $gte: ['$event_date', ps] }, { $lt: ['$event_date', rs] }] }, 1, 0] } } } }],
      } },
    ]).toArray();
    const w = r.windows[0] || { total: 0, recent: 0, previous: 0 };
    let status = 'stable';
    if (w.recent >= 2 && w.recent >= 1.5 * w.previous) status = 'emerging';
    else if (w.previous >= 2 && w.recent <= 0.5 * w.previous) status = 'declining';
    const change = w.previous === 0 ? (w.recent > 0 ? null : 0) : Math.round(((w.recent - w.previous) / w.previous) * 100);
    const [byLevel] = await pool.execute(
      `SELECT co.court_level AS label, COUNT(*) AS value FROM Citation c
       JOIN Legal_Case lc ON lc.case_id = c.citing_case_id JOIN Court co ON co.court_id = lc.court_id
       WHERE c.cited_case_id = ? GROUP BY co.court_level ORDER BY value DESC`, [id]);
    const [citedBy] = await pool.execute(
      `SELECT lc.case_id, lc.case_name, c.citation_date, c.context_text FROM Citation c
       JOIN Legal_Case lc ON lc.case_id = c.citing_case_id WHERE c.cited_case_id = ? ORDER BY c.citation_date DESC LIMIT 8`, [id]);
    return Response.json({ years: y, ...w, change, status, yearly: r.yearly, treatments: r.treatments, byLevel, citedBy });
  } catch (e) { return dbError(e); }
}
