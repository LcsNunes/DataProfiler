import type { ProfileReport } from "@/types/profile";

function value(value: unknown) {
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  return String(value ?? "-");
}

export function MultiDatasetPanel({ report }: { report: ProfileReport }) {
  if (report.report_type !== "multi_dataset" || !report.datasets?.length) return null;

  const relationships = report.relationships;

  return (
    <section className="card">
      <span className="eyebrow">visão multi-base</span>
      <h3>Bases analisadas em conjunto</h3>
      <p className="muted">
        Esta visão ajuda a entender granularidade, chaves candidatas e possíveis joins antes de escolher uma tabela principal.
      </p>

      <div className="dataset-grid">
        {report.datasets.map((dataset) => (
          <article className="dataset-card" key={dataset.dataset_id}>
            <strong>{dataset.dataset_name}</strong>
            <span>{value(dataset.summary.row_count)} linhas</span>
            <span>{value(dataset.summary.column_count)} colunas</span>
            <span>target: {value(dataset.target.column ?? "não detectado")}</span>
            <span>{value(dataset.problems.length)} alertas</span>
          </article>
        ))}
      </div>

      <div className="relationship-grid">
        <div>
          <h3>Colunas compartilhadas</h3>
          <ul className="section-list">
            {(relationships?.common_columns ?? []).slice(0, 12).map((item) => (
              <li key={item.column}>
                <strong>{item.column}</strong> em {item.datasets.length} bases
              </li>
            ))}
            {!relationships?.common_columns?.length && <li>Nenhuma coluna compartilhada detectada.</li>}
          </ul>
        </div>
        <div>
          <h3>Possíveis joins</h3>
          <ul className="section-list">
            {(relationships?.possible_joins ?? []).slice(0, 12).map((item) => (
              <li key={item.column}>
                <strong>{item.column}</strong> parece chave em pelo menos uma base
              </li>
            ))}
            {!relationships?.possible_joins?.length && <li>Nenhuma chave compartilhada confiável detectada.</li>}
          </ul>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Base A</th>
              <th>Base B</th>
              <th>Overlap de schema</th>
              <th>Colunas comuns</th>
            </tr>
          </thead>
          <tbody>
            {(relationships?.schema_overlap ?? []).slice(0, 12).map((item) => (
              <tr key={`${item.left}-${item.right}`}>
                <td>{item.left}</td>
                <td>{item.right}</td>
                <td>{item.overlap_pct}%</td>
                <td>{item.shared_columns.join(", ") || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
