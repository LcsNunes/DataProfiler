"use client";

import { useState } from "react";
import { profileSql } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

export function SqlSourceForm({ onReport }: { onReport: (report: ProfileReport) => void }) {
  const [connectionString, setConnectionString] = useState("sqlite:///./examples/example.db");
  const [table, setTable] = useState("customers");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      onReport(
        await profileSql({
          connection_string: connectionString,
          table: query.trim() ? null : table,
          query: query.trim() || null,
          limit
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao analisar SQL.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-grid">
      <div className="field">
        <label>Connection string</label>
        <input type="password" value={connectionString} onChange={(event) => setConnectionString(event.target.value)} />
      </div>
      <div className="field">
        <label>Tabela</label>
        <input value={table} onChange={(event) => setTable(event.target.value)} />
      </div>
      <div className="field">
        <label>Query SQL opcional</label>
        <textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="SELECT * FROM customers" />
      </div>
      <div className="field">
        <label>Limite de linhas</label>
        <input type="number" value={limit} onChange={(event) => setLimit(Number(event.target.value))} />
      </div>
      <div className="actions">
        <button className="button" disabled={loading || !connectionString || (!table && !query)} onClick={submit}>
          {loading ? "Analisando..." : "Analisar SQL"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
