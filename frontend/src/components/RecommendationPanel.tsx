import type { Recommendation } from "@/types/profile";
import { formatConfidenceLabel, formatInsightText } from "@/lib/labels";

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3>{title}</h3>
      <ul className="section-list">
        {items.map((item) => (
          <li key={item}>{formatInsightText(item)}</li>
        ))}
      </ul>
    </div>
  );
}

export function RecommendationPanel({ recommendation }: { recommendation: Recommendation }) {
  return (
    <section className="recommendation">
      <div className="recommendation-main">
        <span className="eyebrow">confiança: {formatConfidenceLabel(recommendation.confidence)}</span>
        <h2>{formatInsightText(recommendation.recommended_approach)}</h2>
        <p>Modelos e técnicas sugeridas:</p>
        <div>
          {recommendation.suggested_models.map((model) => (
            <span className="pill" key={model}>{formatInsightText(model)}</span>
          ))}
        </div>
      </div>
      <div className="card">
        <ListSection title="Justificativa" items={recommendation.why} />
        <ListSection title="Riscos" items={recommendation.risks} />
        <ListSection title="Próximos passos" items={recommendation.next_steps} />
        <ListSection title="Não recomendado" items={recommendation.not_recommended} />
      </div>
    </section>
  );
}
