import type { SmartPreview } from "@/types/profile";

export function SmartPreviewPanel({ preview }: { preview?: SmartPreview }) {
  if (!preview) return null;
  const columns = Object.keys(preview.sample_rows[0] ?? {});

  return (
    <section className="card">
      <span className="eyebrow">preview inteligente</span>
      <h3>Amostras para investigar rapido</h3>
      <p className="muted">Linhas iniciais e exemplos de problemas encontrados pelo backend.</p>

      {!!columns.length && (
        <div className="table-wrap preview-table">
          <table>
            <thead>
              <tr>
                {columns.map((column) => <th key={column}>{column}</th>)}
              </tr>
            </thead>
            <tbody>
              {preview.sample_rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="issue-example-grid">
        {preview.issue_examples.slice(0, 8).map((item) => (
          <article className="issue-card" key={`${item.column}-${item.type}`}>
            <span className="pill">{item.type}</span>
            <h3>{item.column}</h3>
            <pre>{JSON.stringify(item.examples, null, 2)}</pre>
          </article>
        ))}
        {!preview.issue_examples.length && <p className="muted">Nenhum exemplo problemático destacado nesta amostra.</p>}
      </div>
    </section>
  );
}
