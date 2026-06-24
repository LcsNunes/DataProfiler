export type AnalysisPreset = {
  id: string;
  title: string;
  description: string;
  objective: string;
};

export const ANALYSIS_PRESETS: AnalysisPreset[] = [
  {
    id: "crm_churn",
    title: "CRM / churn",
    description: "Prioriza target, desbalanceamento, dados de clientes e risco de vazamento por IDs.",
    objective: "Prever churn em base de CRM, validar target, desbalanceamento, IDs e qualidade dos dados de clientes."
  },
  {
    id: "finance_default",
    title: "Financeiro / inadimplência",
    description: "Foco em risco, campos sensíveis, desbalanceamento e métricas adequadas.",
    objective: "Detectar inadimplência ou risco financeiro, revisar campos sensíveis, target desbalanceado e validação estratificada."
  },
  {
    id: "sales",
    title: "Vendas",
    description: "Ajuda a avaliar datas, valores extremos, granularidade e análise de performance comercial.",
    objective: "Analisar vendas, validar datas, outliers de valor, granularidade por cliente/produto e oportunidades de previsão."
  },
  {
    id: "operations",
    title: "Operações",
    description: "Foco em eventos, atrasos, status, filas, gargalos e qualidade de processos.",
    objective: "Explorar dados operacionais, identificar gargalos, status inconsistentes, atrasos, eventos raros e problemas de qualidade."
  },
  {
    id: "quality",
    title: "Qualidade de dados",
    description: "Prioriza nulos, duplicados, inconsistências, tipos mistos e plano de limpeza.",
    objective: "Validar qualidade dos dados, priorizar nulos, duplicados, inconsistências, tipos mistos e plano de limpeza."
  },
  {
    id: "api_data",
    title: "Dados de API",
    description: "Foco em paginação, schema variável, campos ausentes, JSON aninhado e limites de requisição.",
    objective: "Analisar dados vindos de API, validar paginação, consistência de schema, campos ausentes e JSON aninhado."
  }
];
