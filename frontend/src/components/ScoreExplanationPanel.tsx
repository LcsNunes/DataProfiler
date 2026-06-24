import type { Readiness } from "@/types/profile";

const SECTIONS = [
  ["data_quality", "Qualidade dos dados"],
  ["modeling", "Prontidão para modelagem"],
  ["joins", "Prontidão de joins"]
] as const;

function formatImpact(value: number) {
  if (value > 0) return `+${value}`;
  return String(value);
}

export function ScoreExplanationPanel({ readiness }: { readiness?: Readiness }) {
  const explanations = readiness?.score_explanations;
  if (!explanations) return null;

  const sections = SECTIONS.map(([key, title]) => ({
    key,
    title,
    items: explanations[key] ?? []
  })).filter((section) => section.items.length);

  if (!sections.length) return null;

  return (
    <section className="card">
      <span className="eyebrow">como o score foi calculado</span>
      <h3>Explicação da pontuação</h3>
      <p className="muted">Cada score começa de sinais objetivos da base e aplica bônus ou penalidades determinísticas.</p>
      <div className="score-explanation-grid">
        {sections.map((section) => (
          <article className="score-explanation-card" key={section.key}>
            <h3>{section.title}</h3>
            <ul>
              {section.items.map((item) => (
                <li key={`${section.key}-${item.label}`}>
                  <span>{item.label}</span>
                  <strong className={item.impact < 0 ? "negative-impact" : "positive-impact"}>{formatImpact(item.impact)}</strong>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
