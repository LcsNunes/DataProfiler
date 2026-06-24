import type { ProfileReport } from "@/types/profile";
import { formatInsightText } from "@/lib/labels";

function format(value: unknown) {
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  return String(value ?? "-");
}

export function MetricsCards({ report }: { report: ProfileReport }) {
  const summary = report.summary;
  const target = report.target;
  const cards: Array<[string, unknown]> = report.report_type === "multi_dataset"
    ? [
        ["Bases", summary.dataset_count],
        ["Linhas totais", summary.row_count],
        ["Colunas totais", summary.column_count],
        ["Colunas comuns", summary.common_column_count],
        ["Joins candidatos", summary.relationship_candidate_count]
      ]
    : [
        ["Linhas", summary.row_count],
        ["Colunas", summary.column_count],
        ["Nulos", `${format(summary.null_cells)} (${format(summary.null_pct)}%)`],
        ["Duplicados", summary.duplicate_rows],
        ["Target provável", target.column ?? "não detectado"]
      ];

  return (
    <section className="metrics">
      {cards.map(([label, value]) => (
        <div key={label} className="metric-card">
          <span>{label}</span>
          <strong>{formatInsightText(format(value))}</strong>
        </div>
      ))}
    </section>
  );
}
