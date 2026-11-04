'use client';
import { useEffect, useState } from 'react';

export async function api(url, opts = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || 'Request failed');
  return d;
}
export function useMe() {
  const [me, setMe] = useState(null);
  useEffect(() => { api('/api/auth/me').then(d => setMe(d.user)).catch(() => {}); }, []);
  return me;
}
