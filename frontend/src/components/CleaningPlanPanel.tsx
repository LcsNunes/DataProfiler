import type { ProfileReport } from "@/types/profile";

export function CleaningPlanPanel({ report }: { report: ProfileReport }) {
  const plan = report.cleaning_plan;
  if (!plan?.checklist?.length) return null;

  return (
    <section className="cleaning-plan card">
      <span className="eyebrow">plano exportável</span>
      <h3>Checklist de limpeza</h3>
      <p className="muted">
        Plano inicial gerado por regras determinísticas. Revise antes de aplicar em dados reais.
      </p>
      <div className="cleaning-grid">
        <div>
          <h3>Checklist</h3>
          <ul className="check-list">
            {plan.checklist.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="export-paths">
            {report.cleaning_plan_path && <span>Markdown: {report.cleaning_plan_path}</span>}
            {report.cleaning_script_path && <span>Script: {report.cleaning_script_path}</span>}
          </div>
        </div>
        <div>
          <h3>Script Polars inicial</h3>
          <pre className="code-preview">{plan.polars_script}</pre>
        </div>
      </div>
    </section>
  );
}
