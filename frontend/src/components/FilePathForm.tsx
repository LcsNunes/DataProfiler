"use client";

import { useState } from "react";
import { profileFilePath, profileFilePaths } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

export function FilePathForm({ onReport }: { onReport: (report: ProfileReport) => void }) {
  const [path, setPath] = useState("./examples/customers.csv");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const paths = path
      .split(/\r?\n|,/)
      .map((item) => item.trim())
      .filter(Boolean);
    setLoading(true);
    setError(null);
    try {
      onReport(paths.length > 1 ? await profileFilePaths(paths) : await profileFilePath(paths[0] ?? path));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao analisar caminho.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-grid">
      <div className="field">
        <label>Caminhos locais acessíveis pelo backend</label>
        <textarea
          value={path}
          onChange={(event) => setPath(event.target.value)}
          placeholder={"./examples/customers.csv\n./examples/sales.xlsx"}
        />
      </div>
      <p className="muted">Informe um caminho por linha para análise multi-base, ou apenas um caminho para análise simples.</p>
      <div className="actions">
        <button className="button" disabled={!path || loading} onClick={submit}>
          {loading ? "Analisando..." : "Analisar caminho(s)"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
