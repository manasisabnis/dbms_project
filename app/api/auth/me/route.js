import { getSession } from '@/lib/auth';
export const dynamic = 'force-dynamic';
export async function GET() {
  const s = await getSession();
  if (!s) return Response.json({ error: 'Not logged in' }, { status: 401 });
  return Response.json({ user: { username: s.username, role: s.role } });
}
