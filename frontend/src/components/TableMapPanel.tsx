import type { TableMap } from "@/types/profile";
import { formatTechnicalLabel } from "@/lib/labels";

export function TableMapPanel({ tableMap }: { tableMap?: TableMap }) {
  if (!tableMap?.nodes?.length) return null;

  return (
    <section className="card">
      <span className="eyebrow">mapa multi-base</span>
      <h3>Tabelas e relacionamentos candidatos</h3>
      <p className="muted">Use este mapa como ponto de partida para validar joins e granularidade.</p>

      <div className="table-map">
        {tableMap.nodes.map((node) => (
          <article className="table-node" key={node.id}>
            <strong>{node.label}</strong>
            <span>{node.row_count.toLocaleString("pt-BR")} linhas</span>
            <span>{node.column_count.toLocaleString("pt-BR")} colunas</span>
            {node.target && <span>target: {node.target}</span>}
          </article>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Origem</th>
              <th>Destino</th>
              <th>Tipo</th>
              <th>Overlap</th>
              <th>Colunas comuns</th>
            </tr>
          </thead>
          <tbody>
            {tableMap.edges.map((edge) => (
              <tr key={`${edge.source}-${edge.target}`}>
                <td>{edge.source}</td>
                <td>{edge.target}</td>
                <td>{formatTechnicalLabel(edge.relationship_hint)}</td>
                <td>{edge.overlap_pct}%</td>
                <td>{edge.shared_columns.join(", ")}</td>
              </tr>
            ))}
            {!tableMap.edges.length && (
              <tr>
                <td colSpan={5}>Nenhum relacionamento candidato detectado.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
