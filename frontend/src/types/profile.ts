export type AnyRecord = Record<string, unknown>;

export type Recommendation = {
  recommended_approach: string;
  suggested_models: string[];
  confidence: string;
  why: string[];
  risks: string[];
  next_steps: string[];
  not_recommended: string[];
  required_preprocessing: string[];
  matched_rules?: string[];
  signals?: Record<string, boolean>;
};

export type ChartDefinition = {
  id: string;
  title: string;
  kind: string;
  description: string;
  option: AnyRecord;
};

export type ColumnProfile = {
  name: string;
  dtype: string;
  semantic_type: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
  unique_rate: number;
  possible_sensitive: boolean;
  problems: string[];
};

export type ExecutiveSummary = {
  headline: string;
  verdict: string;
  decision?: {
    status: string;
    title: string;
    reason: string;
  };
  top_findings: string[];
  immediate_actions: string[];
  primary_action?: string;
  risk_summary?: string;
  top_problem_types?: string[];
  recommended_approach?: string;
};

export type Readiness = {
  data_quality_score: number;
  data_quality_label: string;
  modeling_readiness_score: number;
  modeling_readiness_label: string;
  join_readiness_score?: number | null;
  join_readiness_label?: string | null;
  score_explanations?: Record<string, Array<{ label: string; impact: number }>>;
  drivers: AnyRecord;
};

export type ColumnAction = {
  column: string;
  semantic_type: string;
  recommended_action: string;
  role: string;
  priority: string;
  reasons: string[];
  strategies: string[];
};

export type CleaningPlan = {
  checklist: string[];
  high_priority_actions: ColumnAction[];
  polars_script: string;
  notes: string[];
};

export type DataDictionaryEntry = {
  column: string;
  dataset?: string | null;
  original_column?: string | null;
  dtype: string;
  semantic_type: string;
  role: string;
  recommended_action: string;
  null_pct: number;
  unique_count: number;
  unique_rate: number;
  possible_sensitive: boolean;
  problems: string[];
  example_values: unknown[];
  notes: string[];
};

export type SmartPreview = {
  sample_rows: AnyRecord[];
  issue_examples: Array<{ column: string; type: string; examples: AnyRecord[] }>;
};

export type TableMap = {
  nodes: Array<{ id: string; label: string; row_count: number; column_count: number; target?: string | null }>;
  edges: Array<{ source: string; target: string; shared_columns: string[]; overlap_pct: number; relationship_hint: string }>;
};

export type MultiDatasetInsights = {
  suggested_primary_dataset: string;
  dataset_roles: Array<{
    dataset: string;
    role: string;
    reason: string;
    row_count: number;
    column_count: number;
    has_target: boolean;
    candidate_key_count: number;
  }>;
  join_plan: Array<{
    left: string;
    right: string;
    shared_columns: string[];
    candidate_keys: string[];
    overlap_pct: number;
    risk: string;
    advice: string;
  }>;
  warnings: string[];
};

export type Problem = {
  column: string;
  type: string;
  severity: string;
  details: unknown;
  explanation?: IssueExplanation;
};

export type IssueExplanation = {
  type: string;
  title: string;
  meaning: string;
  why_it_matters: string;
  cautions: string[];
  strategies: string[];
};

export type ProfileReport = {
  id: string;
  created_at: string;
  report_type?: "single_dataset" | "multi_dataset";
  source: AnyRecord;
  analysis_context?: AnyRecord;
  executive_summary?: ExecutiveSummary;
  readiness?: Readiness;
  column_actions?: ColumnAction[];
  cleaning_plan?: CleaningPlan;
  data_dictionary?: DataDictionaryEntry[];
  smart_preview?: SmartPreview;
  summary: AnyRecord;
  schema: {
    columns: ColumnProfile[];
    type_counts: Record<string, number>;
    type_percentages: Record<string, number>;
  };
  quality: AnyRecord;
  statistics: AnyRecord;
  target: AnyRecord;
  problems: Problem[];
  charts: ChartDefinition[];
  recommendation: Recommendation;
  datasets?: ProfileDataset[];
  relationships?: MultiDatasetRelationships;
  multi_dataset_insights?: MultiDatasetInsights;
  table_map?: TableMap;
  report_path?: string;
  markdown_path?: string;
  cleaning_plan_path?: string;
  cleaning_script_path?: string;
};

export type ProfileDataset = Omit<ProfileReport, "datasets" | "relationships"> & {
  dataset_id: string;
  dataset_name: string;
};

export type MultiDatasetRelationships = {
  common_columns: Array<{ column: string; datasets: Array<Record<string, unknown>> }>;
  possible_joins: Array<{ column: string; datasets: Array<Record<string, unknown>> }>;
  schema_overlap: Array<{ left: string; right: string; shared_columns: string[]; overlap_pct: number }>;
  compatible_schema_groups: Array<{ datasets: string[]; column_count: number }>;
};

export type ReportSummary = {
  id: string;
  created_at: string;
  source: AnyRecord;
  summary: AnyRecord;
  recommendation: Recommendation;
};
