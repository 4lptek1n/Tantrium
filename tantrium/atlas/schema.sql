-- Tantrium Atlas schema, reference design.
-- v1 implementation stores JSONL records, but this schema fixes the product model.

CREATE TABLE kernels (
  kernel_id TEXT PRIMARY KEY,
  ell INTEGER,
  path TEXT,
  kind TEXT,
  rows INTEGER,
  created_at TEXT
);

CREATE TABLE certificates (
  certificate_id TEXT PRIMARY KEY,
  theorem_id TEXT,
  kernel_id TEXT,
  status TEXT,
  q_target INTEGER,
  model TEXT,
  sources INTEGER,
  deficits INTEGER,
  edges INTEGER,
  max_half_power INTEGER,
  uncovered_count INTEGER,
  path TEXT,
  created_at TEXT
);

CREATE TABLE obstructions (
  obstruction_id TEXT PRIMARY KEY,
  theorem_id TEXT,
  kernel_id TEXT,
  ell INTEGER,
  q_target INTEGER,
  model TEXT,
  missing_mass TEXT,
  coordinates_json TEXT,
  created_at TEXT
);

CREATE TABLE structure_reports (
  report_id TEXT PRIMARY KEY,
  kernel_id TEXT,
  ell INTEGER,
  path TEXT,
  q_values_json TEXT,
  diff_range TEXT,
  depth_range TEXT,
  suggested_model TEXT,
  created_at TEXT
);
