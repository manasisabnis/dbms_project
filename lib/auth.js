import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

const key = () => new TextEncoder().encode(process.env.JWT_SECRET);

export const signToken = (payload) =>
  new SignJWT(payload).setProtectedHeader({ alg: 'HS256' }).setExpirationTime('2h').sign(key());

export async function getSession() {
  const t = cookies().get('token')?.value;
  if (!t) return null;
  try { return (await jwtVerify(t, key())).payload; } catch { return null; }
}

// Authorization guard: roles = ['admin'] etc. (omit = any logged-in user)
export async function requireRole(roles) {
  const s = await getSession();
  if (!s) return { error: Response.json({ error: 'Not logged in' }, { status: 401 }) };
  if (roles && !roles.includes(s.role)) return { error: Response.json({ error: 'Forbidden: admin role required' }, { status: 403 }) };
  return { session: s };
}
