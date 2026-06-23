"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { ActionPlanPanel } from "@/components/ActionPlanPanel";
import { ChartsPanel } from "@/components/ChartsPanel";
import { ColumnProfileTable } from "@/components/ColumnProfileTable";
import { ExecutiveSummaryPanel } from "@/components/ExecutiveSummaryPanel";
import { MetricsCards } from "@/components/MetricsCards";
import { MultiDatasetPanel } from "@/components/MultiDatasetPanel";
import { ProblemsTable } from "@/components/ProblemsTable";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { SmartPreviewPanel } from "@/components/SmartPreviewPanel";
import { TableMapPanel } from "@/components/TableMapPanel";
import { getReport } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

export default function ProfilePage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<ProfileReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setReport(null);
    setError(null);

    getReport(params.id)
      .then((loadedReport) => {
        if (active) setReport(loadedReport);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Falha ao carregar relatorio.");
      });

    return () => {
      active = false;
    };
  }, [params.id]);

  return (
    <main className="shell">
      <AppNav />
      {error && <div className="error">{error}</div>}
      {!report && !error && <div className="card">Carregando relatorio...</div>}
      {report && (
        <div className="dashboard">
          <section className="card">
            <span className="eyebrow">relatorio {report.id}</span>
            <h2>Resultado da analise</h2>
            <p className="muted">
              Origem: {String(report.source.type ?? "desconhecida")} - criado em {new Date(report.created_at).toLocaleString("pt-BR")}
            </p>
          </section>
          <ExecutiveSummaryPanel report={report} />
          <MetricsCards report={report} />
          <MultiDatasetPanel report={report} />
          <TableMapPanel tableMap={report.table_map} />
          <ActionPlanPanel actions={report.column_actions} />
          <SmartPreviewPanel preview={report.smart_preview} />
          <RecommendationPanel recommendation={report.recommendation} />
          <ChartsPanel charts={report.charts} />
          <ColumnProfileTable columns={report.schema.columns} />
          <ProblemsTable problems={report.problems} />
        </div>
      )}
    </main>
  );
}
