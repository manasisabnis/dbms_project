import { pool, mongo } from '@/lib/db';
import { requireRole } from '@/lib/auth';
export const dynamic = 'force-dynamic';

// Compares citations in the most recent window vs the window before it (MongoDB aggregation)
export async function GET(req) {
  const { error } = await requireRole(); if (error) return error;
  const w = Math.min(Math.max(+new URL(req.url).searchParams.get('window') || 90, 7), 730);
  const now = new Date(), recentStart = new Date(now - w * 864e5), prevStart = new Date(now - 2 * w * 864e5);
  const db = await mongo();
  const agg = await db.collection('citation_events').aggregate([
    { $match: { event_date: { $gte: prevStart, $lte: now } } },
    { $group: { _id: '$cited_case_id',
        recent: { $sum: { $cond: [{ $gte: ['$event_date', recentStart] }, 1, 0] } },
        previous: { $sum: { $cond: [{ $lt: ['$event_date', recentStart] }, 1, 0] } } } },
    { $addFields: { delta: { $subtract: ['$recent', '$previous'] } } },
  ]).toArray();

  const ids = agg.map(x => x._id);
  const [names] = ids.length ? await pool.query('SELECT case_id, case_name, citation_count FROM Legal_Case WHERE case_id IN (?)', [ids]) : [[]];
  const nm = Object.fromEntries(names.map(n => [n.case_id, n]));
  const items = agg.map(x => {
    let status = 'stable';
    if (x.recent >= 2 && x.recent >= 1.5 * x.previous) status = 'emerging';
    else if (x.previous >= 2 && x.recent <= 0.5 * x.previous) status = 'declining';
    return { case_id: x._id, case_name: nm[x._id]?.case_name, total: nm[x._id]?.citation_count, recent: x.recent, previous: x.previous, delta: x.delta, status };
  });
  const emerging = items.filter(i => i.status === 'emerging').sort((a, b) => b.delta - a.delta).slice(0, 8);
  const declining = items.filter(i => i.status === 'declining').sort((a, b) => a.delta - b.delta).slice(0, 8);
  const [frequent] = await pool.query('SELECT case_id, case_name, citation_count AS total FROM Legal_Case ORDER BY citation_count DESC LIMIT 8');
  // last 12 months of citation activity + treatment mix (MongoDB)
  const col = db.collection('citation_events');
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 11, 1));
  const m = await col.aggregate([{ $match: { event_date: { $gte: start } } }, { $group: { _id: { $dateToString: { format: '%Y-%m', date: '$event_date' } }, count: { $sum: 1 } } }]).toArray();
  const mm = Object.fromEntries(m.map(x => [x._id, x.count]));
  const monthly = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - i, 1));
    const k = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
    monthly.push({ key: k, value: mm[k] || 0 });
  }
  const treatments = (await col.aggregate([{ $group: { _id: '$treatment', count: { $sum: 1 } } }, { $sort: { count: -1 } }]).toArray()).map(t => ({ label: t._id, value: t.count }));
  return Response.json({ window: w, emerging, declining, frequent, monthly, treatments });
}
