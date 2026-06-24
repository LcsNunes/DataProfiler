import type { DataDictionaryEntry } from "@/types/profile";
import { formatTechnicalLabel } from "@/lib/labels";

function formatExamples(values: unknown[]) {
  if (!values?.length) return "-";
  return values.map((value) => String(value)).join(", ");
}

export function DataDictionaryPanel({ entries }: { entries?: DataDictionaryEntry[] }) {
  if (!entries?.length) return null;
  const visible = entries.slice(0, 80);

  return (
    <section className="card">
      <span className="eyebrow">dicionário automático</span>
      <h3>Dicionário de dados</h3>
      <p className="muted">Papel provável, tipo semântico, ação sugerida e exemplos para acelerar entendimento da base.</p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Coluna</th>
              <th>Papel provável</th>
              <th>Tipo</th>
              <th>Nulos</th>
              <th>Únicos</th>
              <th>Ação</th>
              <th>Exemplos</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((entry) => (
              <tr key={`${entry.dataset ?? "single"}-${entry.column}`}>
                <td>
                  <strong>{entry.column}</strong>
                  {entry.dataset && <span className="pill">{entry.dataset}</span>}
                </td>
                <td>{formatTechnicalLabel(entry.role)}</td>
                <td>
                  <span className="pill">{formatTechnicalLabel(entry.semantic_type)}</span>
                  <span className="pill">{entry.dtype}</span>
                </td>
                <td>{entry.null_pct}%</td>
                <td>{entry.unique_count.toLocaleString("pt-BR")}</td>
                <td>{formatTechnicalLabel(entry.recommended_action)}</td>
                <td>{formatExamples(entry.example_values)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {entries.length > visible.length && (
        <p className="muted">Mostrando {visible.length} de {entries.length} colunas. O JSON do relatório contém o dicionário completo.</p>
      )}
    </section>
  );
}
