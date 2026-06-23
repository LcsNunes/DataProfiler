"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppNav } from "@/components/AppNav";
import { listReports } from "@/lib/api";
import type { ReportSummary } from "@/types/profile";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listReports()
      .then(setReports)
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar histórico."));
  }, []);

  return (
    <main className="shell">
      <AppNav />
      <section className="card">
        <span className="eyebrow">histórico local</span>
        <h2>Análises executadas</h2>
        <p className="muted">Relatórios persistidos em `reports/` pelo backend.</p>
      </section>
      {error && <div className="error">{error}</div>}
      <section className="reports-list">
        {reports.map((report) => (
          <Link className="report-link" href={`/profile/${report.id}`} key={report.id}>
            <div>
              <strong>{report.id}</strong>
              <p className="muted">
                {String(report.source.type ?? "origem")} · {new Date(report.created_at).toLocaleString("pt-BR")}
              </p>
            </div>
            <span className="pill">{report.recommendation?.confidence ?? "n/a"}</span>
          </Link>
        ))}
        {!reports.length && !error && <div className="card">Nenhum relatório encontrado.</div>}
      </section>
    </main>
  );
}

