import bcrypt from 'bcryptjs';
import { cookies } from 'next/headers';
import { pool } from '@/lib/db';
import { signToken } from '@/lib/auth';

const attempts = new Map(); // basic brute-force protection (per IP, in-memory)

export async function POST(req) {
  const ip = req.headers.get('x-forwarded-for') || 'local';
  const a = attempts.get(ip) || { n: 0, t: Date.now() };
  if (Date.now() - a.t > 60000) { a.n = 0; a.t = Date.now(); }
  if (a.n >= 5) return Response.json({ error: 'Too many attempts. Try again in a minute.' }, { status: 429 });

  const { username, password } = await req.json().catch(() => ({}));
  if (typeof username !== 'string' || typeof password !== 'string' || !username || !password)
    return Response.json({ error: 'Username and password required' }, { status: 400 });

  const [rows] = await pool.execute('SELECT user_id, username, password_hash, role FROM App_User WHERE username = ?', [username]);
  const u = rows[0];
  if (!u || !(await bcrypt.compare(password, u.password_hash))) {
    a.n++; attempts.set(ip, a);
    return Response.json({ error: 'Invalid credentials' }, { status: 401 });
  }
  attempts.delete(ip);
  const token = await signToken({ id: u.user_id, username: u.username, role: u.role });
  cookies().set('token', token, { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/', maxAge: 7200 });
  return Response.json({ user: { username: u.username, role: u.role } });
}
