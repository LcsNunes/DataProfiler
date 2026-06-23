import { AppNav } from "@/components/AppNav";

export default function SettingsPage() {
  return (
    <main className="shell">
      <AppNav />
      <section className="card">
        <span className="eyebrow">runtime</span>
        <h2>Configuracao</h2>
        <p className="muted">
          Em desenvolvimento, o frontend usa `http://localhost:8000` quando `NEXT_PUBLIC_API_BASE_URL`
          nao esta definido. Em producao, defina `NEXT_PUBLIC_API_BASE_URL` ou use proxy no mesmo dominio.
        </p>
        <p className="muted">
          As recomendacoes vem do catalogo editavel em `backend/config/model_catalog.yaml`.
        </p>
      </section>
    </main>
  );
}
