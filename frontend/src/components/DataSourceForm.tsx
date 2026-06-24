"use client";

import { useState } from "react";
import { ApiSourceForm } from "@/components/ApiSourceForm";
import { FilePathForm } from "@/components/FilePathForm";
import { SqlSourceForm } from "@/components/SqlSourceForm";
import { ANALYSIS_PRESETS } from "@/lib/analysisPresets";
import { profileUpload, profileUploadMultiple } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

type Tab = "upload" | "path" | "api" | "sql";

const OBJECTIVE_PRESETS = [
  "Validar qualidade dos dados",
  "Prever churn",
  "Detectar fraude ou risco",
  "Explorar várias tabelas",
  "Responder perguntas sobre dados",
  "Preparar baseline de modelo"
];

export function DataSourceForm({ onReport }: { onReport: (report: ProfileReport) => void }) {
  const [tab, setTab] = useState<Tab>("upload");
  const [files, setFiles] = useState<File[]>([]);
  const [businessObjective, setBusinessObjective] = useState("");
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitUpload() {
    if (!files.length) return;
    setLoading(true);
    setError(null);
    try {
      onReport(
        files.length === 1
          ? await profileUpload(files[0], businessObjective)
          : await profileUploadMultiple(files, businessObjective)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no upload.");
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(presetId: string, objective: string) {
    setSelectedPreset(presetId);
    setBusinessObjective(objective);
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

      <div className="objective-panel">
        <div>
          <span className="eyebrow">contexto determinístico</span>
          <h3>Objetivo da análise</h3>
          <p className="muted">
            Este campo não é chat e não chama LLM. Ele só ajusta regras determinísticas para priorizar alertas,
            recomendações e próximos passos.
          </p>
        </div>
        <div className="preset-strip">
          {OBJECTIVE_PRESETS.map((preset) => (
            <button
              className={`preset-chip ${businessObjective === preset ? "active" : ""}`}
              key={preset}
              type="button"
              onClick={() => {
                setSelectedPreset(null);
                setBusinessObjective(preset);
              }}
            >
              {preset}
            </button>
          ))}
        </div>
        <div className="analysis-preset-grid">
          {ANALYSIS_PRESETS.map((preset) => (
            <button
              className={`analysis-preset-card ${selectedPreset === preset.id ? "active" : ""}`}
              key={preset.id}
              type="button"
              onClick={() => applyPreset(preset.id, preset.objective)}
            >
              <strong>{preset.title}</strong>
              <span>{preset.description}</span>
            </button>
          ))}
        </div>
        <textarea
          aria-label="Objetivo da análise"
          value={businessObjective}
          onChange={(event) => {
            setSelectedPreset(null);
            setBusinessObjective(event.target.value);
          }}
          placeholder="Ex: entender churn, validar qualidade, responder perguntas em linguagem natural, detectar fraude"
        />
        <small className="muted">Opcional. Se ficar vazio, a análise segue apenas pelos sinais detectados na base.</small>
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

      {tab === "path" && <FilePathForm onReport={onReport} businessObjective={businessObjective} />}
      {tab === "api" && <ApiSourceForm onReport={onReport} businessObjective={businessObjective} />}
      {tab === "sql" && <SqlSourceForm onReport={onReport} businessObjective={businessObjective} />}
    </section>
  );
}
