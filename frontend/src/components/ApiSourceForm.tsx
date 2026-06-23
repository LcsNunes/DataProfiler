"use client";

import { useState } from "react";
import { profileApi, testApi } from "@/lib/api";
import type { ProfileReport } from "@/types/profile";

function parseJsonObject(text: string, fallback: unknown) {
  if (!text.trim()) return fallback;
  return JSON.parse(text);
}

export function ApiSourceForm({
  onReport,
  businessObjective
}: {
  onReport: (report: ProfileReport) => void;
  businessObjective?: string;
}) {
  const [url, setUrl] = useState("https://jsonplaceholder.typicode.com/posts");
  const [method, setMethod] = useState<"GET" | "POST">("GET");
  const [headers, setHeaders] = useState("{}");
  const [params, setParams] = useState("{}");
  const [body, setBody] = useState("{}");
  const [dataPath, setDataPath] = useState("");
  const [authType, setAuthType] = useState("none");
  const [apiKeyName, setApiKeyName] = useState("");
  const [apiKeyValue, setApiKeyValue] = useState("");
  const [bearerToken, setBearerToken] = useState("");
  const [basicUsername, setBasicUsername] = useState("");
  const [basicPassword, setBasicPassword] = useState("");
  const [paginationType, setPaginationType] = useState("none");
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function payload() {
    return {
      url,
      method,
      headers: parseJsonObject(headers, {}),
      params: parseJsonObject(params, {}),
      body: method === "POST" ? parseJsonObject(body, {}) : null,
      data_path: dataPath || null,
      auth: {
        type: authType,
        api_key_name: apiKeyName || null,
        api_key_value: apiKeyValue || null,
        bearer_token: bearerToken || null,
        basic_username: basicUsername || null,
        basic_password: basicPassword || null
      },
      timeout: 20,
      retries: 1,
      pagination: {
        type: paginationType,
        limit: 100,
        max_pages: 3
      },
      business_objective: businessObjective || null
    };
  }

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      onReport(await profileApi(payload()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao analisar API.");
    } finally {
      setLoading(false);
    }
  }

  async function test() {
    setLoading(true);
    setError(null);
    try {
      setPreview(await testApi(payload()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no teste da API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-grid">
      <div className="field">
        <label>Endpoint</label>
        <input value={url} onChange={(event) => setUrl(event.target.value)} />
      </div>
      <div className="field">
        <label>Método</label>
        <select value={method} onChange={(event) => setMethod(event.target.value as "GET" | "POST")}>
          <option>GET</option>
          <option>POST</option>
        </select>
      </div>
      <div className="field">
        <label>Headers JSON</label>
        <textarea value={headers} onChange={(event) => setHeaders(event.target.value)} />
      </div>
      <div className="field">
        <label>Query params JSON</label>
        <textarea value={params} onChange={(event) => setParams(event.target.value)} />
      </div>
      {method === "POST" && (
        <div className="field">
          <label>Body JSON</label>
          <textarea value={body} onChange={(event) => setBody(event.target.value)} />
        </div>
      )}
      <div className="field">
        <label>Chave dos dados na resposta</label>
        <input value={dataPath} onChange={(event) => setDataPath(event.target.value)} placeholder="data, items, results ou response.items" />
      </div>
      <div className="field">
        <label>Autenticação</label>
        <select value={authType} onChange={(event) => setAuthType(event.target.value)}>
          <option value="none">Nenhuma</option>
          <option value="api_key">API Key</option>
          <option value="bearer">Bearer Token</option>
          <option value="basic">Basic Auth</option>
        </select>
      </div>
      {authType === "api_key" && (
        <>
          <div className="field">
            <label>Nome da API key</label>
            <input value={apiKeyName} onChange={(event) => setApiKeyName(event.target.value)} />
          </div>
          <div className="field">
            <label>Valor da API key</label>
            <input type="password" value={apiKeyValue} onChange={(event) => setApiKeyValue(event.target.value)} />
          </div>
        </>
      )}
      {authType === "bearer" && (
        <div className="field">
          <label>Bearer token</label>
          <input type="password" value={bearerToken} onChange={(event) => setBearerToken(event.target.value)} />
        </div>
      )}
      {authType === "basic" && (
        <>
          <div className="field">
            <label>Usuário</label>
            <input value={basicUsername} onChange={(event) => setBasicUsername(event.target.value)} />
          </div>
          <div className="field">
            <label>Senha</label>
            <input type="password" value={basicPassword} onChange={(event) => setBasicPassword(event.target.value)} />
          </div>
        </>
      )}
      <div className="field">
        <label>Paginação</label>
        <select value={paginationType} onChange={(event) => setPaginationType(event.target.value)}>
          <option value="none">Sem paginação</option>
          <option value="page_limit">page/limit</option>
          <option value="offset_limit">offset/limit</option>
          <option value="next_url">next_url</option>
          <option value="next_token">next_token</option>
        </select>
      </div>
      <div className="actions">
        <button className="button secondary" disabled={loading} onClick={test}>
          Testar conexão
        </button>
        <button className="button" disabled={loading || !url} onClick={submit}>
          {loading ? "Processando..." : "Analisar API"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {preview && <pre className="preview">{JSON.stringify(preview, null, 2)}</pre>}
    </div>
  );
}
