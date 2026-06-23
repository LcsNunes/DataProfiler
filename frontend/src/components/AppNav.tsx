import Link from "next/link";

export function AppNav() {
  return (
    <nav className="nav">
      <Link href="/" className="brand">
        <span className="brand-mark">DP</span>
        <span>Data Profiler AI</span>
      </Link>
      <div className="nav-links">
        <Link href="/">Nova análise</Link>
        <Link href="/reports">Histórico</Link>
        <Link href="/settings">Config</Link>
      </div>
    </nav>
  );
}

