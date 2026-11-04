import { pool } from '@/lib/db';
import { requireRole } from '@/lib/auth';
import { dbError } from '@/lib/http';
export const dynamic = 'force-dynamic';

export async function GET() {
  const { error } = await requireRole(); if (error) return error;
  try {
    const [[stats]] = await pool.query(
      `SELECT (SELECT COUNT(*) FROM Legal_Case) AS cases, (SELECT COUNT(*) FROM Citation) AS citations,
              (SELECT COUNT(*) FROM Court) AS courts, (SELECT COUNT(*) FROM Judge) AS judges,
              (SELECT COUNT(*) FROM Legal_Case WHERE case_id NOT IN (SELECT cited_case_id FROM Citation)) AS never_cited`);
    const [landmarks] = await pool.query('SELECT * FROM Landmark_Cases ORDER BY citation_count DESC LIMIT 10'); // VIEW
    const [courts] = await pool.query(                                                                         // JOIN + GROUP BY + HAVING
      `SELECT co.court_name, co.court_level, COUNT(lc.case_id) AS cases, SUM(lc.citation_count) AS total_citations
       FROM Court co JOIN Legal_Case lc ON lc.court_id = co.court_id
       GROUP BY co.court_id, co.court_name, co.court_level HAVING COUNT(lc.case_id) >= 1
       ORDER BY total_citations DESC`);
    const [aboveAvg] = await pool.query(                                                                        // subquery
      `SELECT case_id, case_name, citation_count FROM Legal_Case
       WHERE citation_count > (SELECT AVG(citation_count) FROM Legal_Case) ORDER BY citation_count DESC LIMIT 10`);
    const [byLevel] = await pool.query(                                                                        // citing court level
      `SELECT co.court_level AS label, COUNT(*) AS value FROM Citation c
       JOIN Legal_Case lc ON lc.case_id = c.citing_case_id JOIN Court co ON co.court_id = lc.court_id
       GROUP BY co.court_level ORDER BY value DESC`);
    const [byType] = await pool.query(
      'SELECT case_type AS label, COUNT(*) AS cases, SUM(citation_count) AS citations FROM Legal_Case GROUP BY case_type ORDER BY citations DESC');
    return Response.json({ stats, landmarks, courts, aboveAvg, byLevel, byType });
  } catch (e) { return dbError(e); }
}
