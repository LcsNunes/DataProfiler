import type { ColumnAction } from "@/types/profile";

export function ActionPlanPanel({ actions }: { actions?: ColumnAction[] }) {
  if (!actions?.length) return null;
  const visible = actions.slice(0, 24);

  return (
    <section className="card">
      <span className="eyebrow">plano acionavel</span>
      <h3>Acoes recomendadas por coluna</h3>
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
                <td><span className="pill">{action.recommended_action}</span></td>
                <td>{action.role}</td>
                <td>{action.reasons.join(" ")}</td>
                <td>{action.strategies.join(" ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {actions.length > visible.length && (
        <p className="muted">Mostrando {visible.length} de {actions.length} acoes. Prioridades altas aparecem primeiro.</p>
      )}
    </section>
  );
}
