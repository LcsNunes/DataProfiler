import type { ProfileReport } from "@/types/profile";
import { formatInsightText, formatReadinessLabel } from "@/lib/labels";

function scoreClass(score?: number | null) {
  if (score == null) return "score-neutral";
  if (score >= 80) return "score-good";
  if (score >= 55) return "score-warn";
  return "score-bad";
}

function formatNumber(value: unknown) {
  return typeof value === "number" ? value.toLocaleString("pt-BR") : String(value ?? "0");
}

function buildHeadline(report: ProfileReport) {
  const summary = report.summary;
  if (report.report_type === "multi_dataset") {
    return `${formatNumber(summary.dataset_count)} bases · ${formatNumber(summary.row_count)} linhas totais`;
  }
  return `${formatNumber(summary.row_count)} linhas · ${formatNumber(summary.column_count)} colunas`;
}

export function ExecutiveSummaryPanel({ report }: { report: ProfileReport }) {
  const summary = report.executive_summary;
  const readiness = report.readiness;

  if (!summary || !readiness) return null;

  const scores = [
    { label: "Qualidade", score: readiness.data_quality_score, status: readiness.data_quality_label },
    { label: "Modelagem", score: readiness.modeling_readiness_score, status: readiness.modeling_readiness_label },
    { label: "Joins", score: readiness.join_readiness_score, status: readiness.join_readiness_label }
  ].filter((item) => item.score !== null && item.score !== undefined);

  return (
    <section className="executive-grid">
      <article className="executive-brief">
        <span className="eyebrow">resumo executivo</span>
        <h2>{buildHeadline(report)}</h2>
        <p>{formatInsightText(summary.verdict)}</p>
        {summary.recommended_approach && <span className="pill">{summary.recommended_approach}</span>}
      </article>

      <article className="card">
        <h3>Prontidão</h3>
        <div className="score-strip">
          {scores.map(({ label, score, status }) => (
            <div className={`score-card ${scoreClass(Number(score))}`} key={label}>
              <span>{label}</span>
              <strong>{score}/100</strong>
              <small>{formatReadinessLabel(status)}</small>
            </div>
          ))}
        </div>
      </article>

      <article className="card">
        <h3>Achados principais</h3>
        <ul className="section-list">
          {summary.top_findings.map((item) => (
            <li key={item}>{formatInsightText(item)}</li>
          ))}
        </ul>
      </article>

      <article className="card">
        <h3>Próximas ações</h3>
        <ul className="section-list">
          {summary.immediate_actions.map((item) => (
            <li key={item}>{formatInsightText(item)}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}
