import { pool } from '@/lib/db';
import { requireRole } from '@/lib/auth';
export const dynamic = 'force-dynamic';
export async function GET() {
  const { error } = await requireRole(); if (error) return error;
  const [courts] = await pool.query('SELECT court_id, court_name FROM Court ORDER BY court_name');
  const [cases] = await pool.query('SELECT case_id, case_name, judgment_date FROM Legal_Case ORDER BY case_name');
  return Response.json({ courts, cases });
}
