import Link from "next/link";

export default function Navbar() {
  return (
    <header className="bg-slate-900 text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold">
          ⚖ Legal Case Citation Evolution Analyzer
        </Link>
        <nav className="flex gap-6 text-sm text-slate-300">
          <Link href="/" className="hover:text-white">Home</Link>
        </nav>
      </div>
    </header>
  );
}
