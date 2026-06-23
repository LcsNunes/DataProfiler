import type { ColumnProfile } from "@/types/profile";

export function ColumnProfileTable({ columns }: { columns: ColumnProfile[] }) {
  return (
    <section className="card">
      <h3>Colunas</h3>
      <p className="muted">Tipos detectados, nulos, cardinalidade e alertas por coluna.</p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Coluna</th>
              <th>Tipo</th>
              <th>Nulos</th>
              <th>Únicos</th>
              <th>Problemas</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr key={column.name}>
                <td>{column.name}</td>
                <td>
                  <span className="pill">{column.semantic_type}</span>
                  <span className="pill">{column.dtype}</span>
                  {column.possible_sensitive && <span className="pill">sensível?</span>}
                </td>
                <td>{column.null_pct}%</td>
                <td>
                  {column.unique_count} ({Math.round(column.unique_rate * 100)}%)
                </td>
                <td>{column.problems.length ? column.problems.map((item) => <span className="pill" key={item}>{item}</span>) : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

