'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { api } from '@/lib/client';

export default function Nav() {
  const path = usePathname(), router = useRouter();
  const [me, setMe] = useState(null);
  useEffect(() => { api('/api/auth/me').then(d => setMe(d.user)).catch(() => setMe(null)); }, [path]);
  if (path === '/login' || !me) return null;
  const L = ([href, t]) => <Link key={href} href={href} className={(href === '/' ? path === '/' : path.startsWith(href)) ? 'on' : ''}>{t}</Link>;
  return (
    <nav>
      <b>⚖️ Citation Evolution Analyzer</b>
      {[['/', 'Dashboard'], ['/cases', 'Cases'], ['/citations', 'Citations']].map(L)}
      <span className="sp" />
      <span className="who">👤 {me.username} · {me.role}</span>
      <button className="sec" onClick={async () => { await api('/api/auth/logout', { method: 'POST' }); setMe(null); router.push('/login'); }}>Logout</button>
    </nav>
  );
}
