'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/client';

export default function Login() {
  const router = useRouter();
  const [f, setF] = useState({ username: '', password: '' });
  const [err, setErr] = useState('');
  async function submit() {
    setErr('');
    try { await api('/api/auth/login', { method: 'POST', body: JSON.stringify(f) }); router.push('/'); router.refresh(); }
    catch (e) { setErr(e.message); }
  }
  return (
    <div className="card login">
      <h2>Sign in</h2>
      <p className="muted">Legal Case Citation Evolution Analyzer</p>
      <input placeholder="Username" value={f.username} onChange={e => setF({ ...f, username: e.target.value })} />
      <input type="password" placeholder="Password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} onKeyDown={e => e.key === 'Enter' && submit()} />
      <button onClick={submit} style={{ width: '100%' }}>Login</button>
      {err && <p className="err">{err}</p>}
    </div>
  );
}
