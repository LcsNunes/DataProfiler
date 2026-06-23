"use client";

import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { DataSourceForm } from "@/components/DataSourceForm";
import type { ProfileReport } from "@/types/profile";

export default function HomePage() {
  const router = useRouter();

  function handleReport(report: ProfileReport) {
    router.push(`/profile/${report.id}`);
  }

  return (
    <main className="shell">
      <AppNav />
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Perfilamento automático para bases reais</span>
          <h1>Diagnóstico de dados antes do modelo.</h1>
          <p>
            Carregue arquivo, API ou banco SQL. O backend detecta schema, problemas,
            target provável, gráficos úteis e recomenda uma abordagem técnica com regras
            interpretáveis.
          </p>
          <div className="signal-strip">
            <div className="signal">
              <strong>01 / qualidade</strong>
              Nulos, brancos, duplicados, cardinalidade, outliers e tipos mistos.
            </div>
            <div className="signal">
              <strong>02 / modelagem</strong>
              Target provável, desbalanceamento e próximos passos recomendados.
            </div>
            <div className="signal">
              <strong>03 / rastreio</strong>
              Relatórios salvos localmente com JSON e Markdown exportável.
            </div>
          </div>
        </div>
        <DataSourceForm onReport={handleReport} />
      </section>
    </main>
  );
}

