import type { IssueExplanation, Problem } from "@/types/profile";
import { formatInsightText, formatTechnicalLabel } from "@/lib/labels";

function uniqueExplanations(problems: Problem[]) {
  const seen = new Set<string>();
  return problems
    .map((problem) => problem.explanation)
    .filter((explanation): explanation is IssueExplanation => {
      if (!explanation || seen.has(explanation.type)) return false;
      seen.add(explanation.type);
      return true;
    });
}

export function ProblemsTable({ problems }: { problems: Problem[] }) {
  const explanations = uniqueExplanations(problems);
  const visibleProblems = problems.slice(0, 40);

  return (
    <>
      <section className="card">
        <h3>Legenda dos alertas</h3>
        <p className="muted">O que cada problema significa, cuidados e estratégias possíveis.</p>
        <div className="issue-legend">
          {explanations.map((item) => (
            <article className="issue-card" key={item.type}>
              <span className="pill">{formatTechnicalLabel(item.type)}</span>
              <h3>{item.title}</h3>
              <p>{formatInsightText(item.meaning)}</p>
              <p className="muted">{formatInsightText(item.why_it_matters)}</p>
              <strong>Cuidados</strong>
              <ul>
                {item.cautions.map((caution) => (
                  <li key={caution}>{formatInsightText(caution)}</li>
                ))}
              </ul>
              <strong>Estratégias</strong>
              <ul>
                {item.strategies.map((strategy) => (
                  <li key={strategy}>{formatInsightText(strategy)}</li>
                ))}
              </ul>
            </article>
          ))}
          {!explanations.length && <div className="muted">Nenhum alerta com legenda para este relatório.</div>}
        </div>
      </section>

      <section className="card">
        <h3>Principais problemas</h3>
        <p className="muted">
          Alertas gerados automaticamente pelo backend. Mostrando {visibleProblems.length} de {problems.length}.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Coluna</th>
                <th>Tipo</th>
                <th>Severidade</th>
                <th>Detalhes</th>
              </tr>
            </thead>
            <tbody>
              {visibleProblems.map((problem, index) => (
                <tr key={`${problem.column}-${problem.type}-${index}`}>
                  <td>{problem.column}</td>
                  <td>{problem.explanation?.title ?? formatTechnicalLabel(problem.type)}</td>
                  <td>{formatTechnicalLabel(problem.severity)}</td>
                  <td>{JSON.stringify(problem.details)}</td>
                </tr>
              ))}
              {!problems.length && (
                <tr>
                  <td colSpan={4}>Nenhum problema relevante encontrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
