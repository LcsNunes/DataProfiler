import type { ColumnAction } from "@/types/profile";
import { formatInsightText, formatTechnicalLabel } from "@/lib/labels";

export function ActionPlanPanel({ actions }: { actions?: ColumnAction[] }) {
  if (!actions?.length) return null;
  const visible = actions.slice(0, 24);

  return (
    <section className="card">
      <span className="eyebrow">plano acionável</span>
      <h3>Ações recomendadas por coluna</h3>
      <p className="muted">Uma lista objetiva para decidir o que validar, limpar, remover ou usar como chave.</p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Coluna</th>
              <th>Acao</th>
              <th>Papel</th>
              <th>Motivo</th>
              <th>Estrategia</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((action) => (
              <tr key={`${action.column}-${action.recommended_action}`}>
                <td>{action.column}</td>
                <td><span className="pill">{formatTechnicalLabel(action.recommended_action)}</span></td>
                <td>{formatTechnicalLabel(action.role)}</td>
                <td>{formatInsightText(action.reasons.join(" "))}</td>
                <td>{formatInsightText(action.strategies.join(" "))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {actions.length > visible.length && (
        <p className="muted">Mostrando {visible.length} de {actions.length} ações. Prioridades altas aparecem primeiro.</p>
      )}
    </section>
  );
}
