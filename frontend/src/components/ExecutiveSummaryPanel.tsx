import type { ProfileReport } from "@/types/profile";

function scoreClass(score?: number | null) {
  if (score == null) return "score-neutral";
  if (score >= 80) return "score-good";
  if (score >= 55) return "score-warn";
  return "score-bad";
}

export function ExecutiveSummaryPanel({ report }: { report: ProfileReport }) {
  const summary = report.executive_summary;
  const readiness = report.readiness;

  if (!summary || !readiness) return null;

  const scores = [
    ["Qualidade", readiness.data_quality_score, readiness.data_quality_label],
    ["Modelagem", readiness.modeling_readiness_score, readiness.modeling_readiness_label],
    ["Joins", readiness.join_readiness_score, readiness.join_readiness_label]
  ].filter(([, score]) => score !== null && score !== undefined);

  return (
    <section className="executive-grid">
      <article className="executive-brief">
        <span className="eyebrow">resumo executivo</span>
        <h2>{summary.headline}</h2>
        <p>{summary.verdict}</p>
        {summary.recommended_approach && <span className="pill">{summary.recommended_approach}</span>}
      </article>

      <article className="card">
        <h3>Prontidao</h3>
        <div className="score-strip">
          {scores.map(([label, score, status]) => (
            <div className={`score-card ${scoreClass(Number(score))}`} key={String(label)}>
              <span>{label}</span>
              <strong>{score}/100</strong>
              <small>{String(status)}</small>
            </div>
          ))}
        </div>
      </article>

      <article className="card">
        <h3>Achados principais</h3>
        <ul className="section-list">
          {summary.top_findings.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>

      <article className="card">
        <h3>Proximas acoes</h3>
        <ul className="section-list">
          {summary.immediate_actions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}
