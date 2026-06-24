const READINESS_LABELS: Record<string, string> = {
  ready: "Pronto",
  needs_review: "Requer revisão",
  not_ready: "Não pronto"
};

const CONFIDENCE_LABELS: Record<string, string> = {
  high: "Alta",
  medium: "Média",
  low: "Baixa"
};

const TECHNICAL_LABELS: Record<string, string> = {
  blank_strings: "Textos em branco",
  boolean: "Booleano",
  dimension_candidate: "Dimensão/cadastro candidato",
  fact_or_event_candidate: "Fato/evento candidato",
  categorical: "Categórica",
  constant_column: "Coluna constante",
  date: "Data",
  drop_from_modeling: "Remover da modelagem",
  empty_strings: "Strings vazias",
  feature_candidate: "Feature candidata",
  fix_dates: "Corrigir datas",
  fix_type_consistency: "Corrigir tipo",
  high: "Alta",
  high_cardinality: "Alta cardinalidade",
  inconsistent_values: "Valores inconsistentes",
  info: "Informativo",
  invalid_dates: "Datas inválidas",
  join_or_identifier: "Chave ou identificador",
  keep: "Manter",
  long_text: "Texto longo",
  low: "Baixa",
  mask_or_exclude: "Mascarar ou excluir",
  medium: "Média",
  mixed_types: "Mistura de tipos",
  missing_values: "Valores ausentes",
  near_constant_column: "Coluna quase constante",
  normal: "Normal",
  numeric: "Numérica",
  numeric_outliers: "Outliers numéricos",
  possible_encoding_issue: "Possível problema de encoding",
  possible_id: "Possível identificador",
  possible_join: "Possível join",
  possible_primary_key: "Possível chave primária",
  possible_sensitive_field: "Possível campo sensível",
  primary_candidate: "Tabela principal candidata",
  sensitive_candidate: "Campo sensível candidato",
  shared_schema: "Schema compartilhado",
  target_candidate: "Target candidato",
  text: "Texto",
  treat_missing_values: "Tratar ausentes",
  unknown: "Desconhecido",
  use_as_key: "Usar como chave",
  validate_cardinality: "Validar cardinalidade",
  validate_target: "Validar target",
  warning: "Atenção",
  whitespace_only_strings: "Texto só com espaços"
};

const SOURCE_LABELS: Record<string, string> = {
  api: "API",
  file: "Arquivo",
  multi_dataset: "Múltiplas bases",
  sql: "Banco SQL",
  upload: "Upload"
};

const TEXT_REPLACEMENTS: Array<[RegExp, string]> = [
  [/Possible target column detected\./g, "Possível coluna target detectada."],
  [/Confirm this target with the business owner before supervised modeling\./g, "Confirme esse target com a área de negócio antes da modelagem supervisionada."],
  [/Column looks like an identifier or key\./g, "A coluna parece ser identificador ou chave."],
  [/Use for joins, deduplication or lineage; avoid direct predictive use\./g, "Use para joins, deduplicação ou rastreabilidade; evite uso preditivo direto."],
  [/Column is constant\./g, "A coluna é constante."],
  [/Remove from modeling unless it is useful metadata\./g, "Remova da modelagem, exceto se for metadado útil."],
  [/Column may contain sensitive data\./g, "A coluna pode conter dados sensíveis."],
  [/Mask, hash or remove before external sharing or modeling\./g, "Mascare, aplique hash ou remova antes de compartilhamento externo ou modelagem."],
  [/missing values\./g, "de valores ausentes."],
  [/High cardinality detected\./g, "Alta cardinalidade detectada."],
  [/Numeric outliers detected\./g, "Outliers numéricos detectados."],
  [/Mixed value types detected\./g, "Mistura de tipos detectada."],
  [/Invalid dates detected\./g, "Datas inválidas detectadas."],
  [/No major issue detected for this column\./g, "Nenhum problema relevante detectado nesta coluna."],
  [/Keep as candidate feature and validate with the modeling objective\./g, "Mantenha como feature candidata e valide com o objetivo da modelagem."],
  [/\bProntidao\b/g, "Prontidão"],
  [/\bproximas acoes\b/gi, "próximas ações"],
  [/\bProximas acoes\b/g, "Próximas ações"],
  [/\bacoes\b/g, "ações"],
  [/\bAcoes\b/g, "Ações"],
  [/\bacao\b/g, "ação"],
  [/\bAcao\b/g, "Ação"],
  [/\banalise\b/g, "análise"],
  [/\bAnalise\b/g, "Análise"],
  [/\brelatorio\b/g, "relatório"],
  [/\bRelatorio\b/g, "Relatório"],
  [/\bprovavel\b/g, "provável"],
  [/\bProvavel\b/g, "Provável"],
  [/\bnao\b/g, "não"],
  [/\bNao\b/g, "Não"],
  [/\bestrategias\b/g, "estratégias"],
  [/\bEstrategias\b/g, "Estratégias"],
  [/\bpossiveis\b/g, "possíveis"],
  [/\bPossiveis\b/g, "Possíveis"],
  [/\bsensiveis\b/g, "sensíveis"],
  [/\bSensiveis\b/g, "Sensíveis"],
  [/\bneeds_review\b/g, "requer revisão"],
  [/\bnot_ready\b/g, "não pronto"],
  [/\bready\b/g, "pronto"]
];

export function formatTechnicalLabel(value: unknown) {
  const key = String(value ?? "").trim();
  if (!key) return "-";
  return TECHNICAL_LABELS[key] ?? key.replaceAll("_", " ");
}

export function formatReadinessLabel(value: unknown) {
  const key = String(value ?? "").trim();
  return READINESS_LABELS[key] ?? formatTechnicalLabel(key);
}

export function formatConfidenceLabel(value: unknown) {
  const key = String(value ?? "").trim();
  return CONFIDENCE_LABELS[key] ?? formatTechnicalLabel(key);
}

export function formatSourceType(value: unknown) {
  const key = String(value ?? "").trim();
  return SOURCE_LABELS[key] ?? formatTechnicalLabel(key || "desconhecida");
}

export function formatInsightText(value: unknown) {
  let text = String(value ?? "");
  for (const [pattern, replacement] of TEXT_REPLACEMENTS) {
    text = text.replace(pattern, replacement);
  }
  return text;
}
