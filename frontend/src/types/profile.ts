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
  report_path?: string;
  markdown_path?: string;
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
