import { AppNav } from "@/components/AppNav";

export default function SettingsPage() {
  return (
    <main className="shell">
      <AppNav />
      <section className="card">
        <span className="eyebrow">runtime</span>
        <h2>Configuração</h2>
        <p className="muted">
          Em desenvolvimento, o frontend usa `http://localhost:8000` quando `NEXT_PUBLIC_API_BASE_URL`
          não está definido. Em produção, defina `NEXT_PUBLIC_API_BASE_URL` ou use proxy no mesmo domínio.
        </p>
        <p className="muted">
          As recomendações vêm do catálogo editável em `backend/config/model_catalog.yaml`.
        </p>
      </section>
    </main>
  );
}
