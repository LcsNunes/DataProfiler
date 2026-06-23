import type { ProfileReport, ReportSummary } from "@/types/profile";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String((item as { msg: unknown }).msg);
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(formatErrorDetail(payload.detail) || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function profileFilePath(path: string, businessObjective?: string) {
  return request<ProfileReport>("/profile/file-path", {
    method: "POST",
    body: JSON.stringify({ path, business_objective: businessObjective || null })
  });
}

export function profileFilePaths(paths: string[], businessObjective?: string) {
  return request<ProfileReport>("/profile/file-paths", {
    method: "POST",
    body: JSON.stringify({ paths, business_objective: businessObjective || null })
  });
}

export function profileUpload(file: File, businessObjective?: string) {
  const form = new FormData();
  form.append("file", file);
  if (businessObjective) form.append("business_objective", businessObjective);
  return request<ProfileReport>("/profile/upload", {
    method: "POST",
    body: form
  });
}

export function profileUploadMultiple(files: File[], businessObjective?: string) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  if (businessObjective) form.append("business_objective", businessObjective);
  return request<ProfileReport>("/profile/upload-multiple", {
    method: "POST",
    body: form
  });
}

export function profileApi(payload: unknown) {
  return request<ProfileReport>("/profile/api", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function testApi(payload: unknown) {
  return request<{ columns: string[]; rows: Record<string, unknown>[]; source: Record<string, unknown> }>("/sources/api/test", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function profileSql(payload: unknown) {
  return request<ProfileReport>("/profile/sql", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listReports() {
  return request<ReportSummary[]>("/reports");
}

export function getReport(id: string) {
  return request<ProfileReport>(`/reports/${id}`);
}
