'use client';
export const PAL = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

export function Donut({ data, size = 170, centerLabel = 'total' }) {
  const tot = data.reduce((a, d) => a + d.value, 0);
  const r = 60, c = 2 * Math.PI * r;
  let off = 0;
  if (!tot) return <p className="muted">No data</p>;
  return (
    <div className="donut">
      <svg viewBox="0 0 160 160" width={size} height={size}>
        <g transform="rotate(-90 80 80)">
          {data.map((d, i) => {
            const len = (d.value / tot) * c;
            const el = <circle key={i} cx="80" cy="80" r={r} fill="none" stroke={PAL[i % PAL.length]} strokeWidth="24" strokeDasharray={`${len} ${c - len}`} strokeDashoffset={-off} />;
            off += len; return el;
          })}
        </g>
        <text x="80" y="82" textAnchor="middle" fontSize="24" fontWeight="700" fill="#1e293b">{tot}</text>
        <text x="80" y="99" textAnchor="middle" fontSize="10" fill="#64748b">{centerLabel}</text>
      </svg>
      <ul className="legend">
        {data.map((d, i) => <li key={i}><i style={{ background: PAL[i % PAL.length] }} />{d.label}<b>{d.value} ({Math.round((d.value / tot) * 100)}%)</b></li>)}
      </ul>
    </div>
  );
}

function axis(max) { const m = Math.max(4, Math.ceil(max / 4) * 4); return { m, ticks: [0, 1, 2, 3, 4].map(i => (m / 4) * i) }; }

export function LineArea({ data, color = '#4f46e5', h = 210, yLabel = '' }) {
  const W = 480, p = { l: 36, r: 12, t: 12, b: 28 };
  const { m, ticks } = axis(Math.max(0, ...data.map(d => d.value)));
  const x = i => p.l + (data.length < 2 ? (W - p.l - p.r) / 2 : (i * (W - p.l - p.r)) / (data.length - 1));
  const y = v => p.t + (h - p.t - p.b) * (1 - v / m);
  const line = data.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d.value)}`).join(' ');
  const area = `${line} L${x(data.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const step = Math.ceil(data.length / 8);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} className="chart">
      <defs><linearGradient id={'g' + color.slice(1)} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={color} stopOpacity=".35" /><stop offset="1" stopColor={color} stopOpacity="0" /></linearGradient></defs>
      {ticks.map(t => <g key={t}><line x1={p.l} x2={W - p.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" strokeDasharray="3 3" /><text x={p.l - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill="#64748b">{t}</text></g>)}
      <path d={area} fill={`url(#g${color.slice(1)})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2.5" />
      {data.map((d, i) => <g key={i}><circle cx={x(i)} cy={y(d.value)} r="3.5" fill={color}><title>{d.label}: {d.value}</title></circle>{i % step === 0 && <text x={x(i)} y={h - 8} textAnchor="middle" fontSize="10" fill="#64748b">{d.label}</text>}</g>)}
      {yLabel && <text x="4" y="10" fontSize="9" fill="#94a3b8">{yLabel}</text>}
    </svg>
  );
}

export function Bars({ data, color, h = 210, yLabel = '' }) {
  const W = 480, p = { l: 36, r: 12, t: 12, b: 28 };
  const { m, ticks } = axis(Math.max(0, ...data.map(d => d.value)));
  const bw = (W - p.l - p.r) / data.length;
  const y = v => p.t + (h - p.t - p.b) * (1 - v / m);
  const step = Math.ceil(data.length / 8);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} className="chart">
      {ticks.map(t => <g key={t}><line x1={p.l} x2={W - p.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" strokeDasharray="3 3" /><text x={p.l - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill="#64748b">{t}</text></g>)}
      {data.map((d, i) => <g key={i}>
        <rect x={p.l + i * bw + bw * 0.18} y={y(d.value)} width={bw * 0.64} height={y(0) - y(d.value)} rx="4" fill={color || PAL[i % PAL.length]}><title>{d.label}: {d.value}</title></rect>
        {i % step === 0 && <text x={p.l + i * bw + bw / 2} y={h - 8} textAnchor="middle" fontSize="10" fill="#64748b">{d.label}</text>}
      </g>)}
      {yLabel && <text x="4" y="10" fontSize="9" fill="#94a3b8">{yLabel}</text>}
    </svg>
  );
}

export function HBars({ data, unit = '' }) {
  const max = Math.max(1, ...data.map(d => d.value));
  return (
    <div className="hbars">
      {data.map((d, i) => (
        <div key={i} className="hb"><span className="hl" title={d.label}>{d.label}</span>
          <div className="ht"><div style={{ width: `${(d.value / max) * 100}%`, background: PAL[i % PAL.length] }} /></div>
          <b>{d.value}{unit}</b></div>
      ))}
    </div>
  );
}

export const Pager = ({ page, pages, setPage }) => pages > 1 && (
  <div className="row" style={{ justifyContent: 'center', alignItems: 'center', marginTop: 12 }}>
    <button className="sec" disabled={page <= 1} onClick={() => setPage(page - 1)}>‹ Prev</button>
    <span className="muted">Page {page} of {pages}</span>
    <button className="sec" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next ›</button>
  </div>
);
