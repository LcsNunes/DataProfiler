"use client";

import { useState } from "react";
import { ApiSourceForm } from "@/components/ApiSourceForm";
import { FilePathForm } from "@/components/FilePathForm";
import { SqlSourceForm } from "@/components/SqlSourceForm";
import { profileUpload, profileUploadMultiple } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

type Tab = "upload" | "path" | "api" | "sql";

export function DataSourceForm({ onReport }: { onReport: (report: ProfileReport) => void }) {
  const [tab, setTab] = useState<Tab>("upload");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitUpload() {
    if (!files.length) return;
    setLoading(true);
    setError(null);
    try {
      onReport(files.length === 1 ? await profileUpload(files[0]) : await profileUploadMultiple(files));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no upload.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="tabs">
        {[
          ["upload", "Upload"],
          ["path", "Caminho"],
          ["api", "API"],
          ["sql", "SQL"]
        ].map(([value, label]) => (
          <button key={value} className={`tab ${tab === value ? "active" : ""}`} onClick={() => setTab(value as Tab)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "upload" && (
        <div className="form-grid">
          <div className="field">
            <label>Um ou mais arquivos CSV, XLSX, JSON ou Parquet</label>
            <input
              type="file"
              multiple
              accept=".csv,.xlsx,.xls,.json,.parquet"
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
          </div>
          {files.length > 1 && <p className="muted">Modo multi-base: {files.length} arquivos serão analisados juntos.</p>}
          <div className="actions">
            <button className="button" disabled={!files.length || loading} onClick={submitUpload}>
              {loading ? "Analisando..." : files.length > 1 ? "Analisar bases" : "Analisar upload"}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      {tab === "path" && <FilePathForm onReport={onReport} />}
      {tab === "api" && <ApiSourceForm onReport={onReport} />}
      {tab === "sql" && <SqlSourceForm onReport={onReport} />}
    </section>
  );
}
