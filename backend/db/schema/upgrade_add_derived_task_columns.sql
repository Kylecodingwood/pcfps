-- 存量库：分割/分类派生任务列（与 filter_task 同表）。
-- psql -U pcfps -d pcfps -f db/schema/upgrade_add_derived_task_columns.sql

ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS task_kind VARCHAR(32) NOT NULL DEFAULT 'FILTER';
ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS parent_task_id UUID REFERENCES filter_task (id) ON DELETE CASCADE;
ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS derived_method VARCHAR(64);
ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS derived_params_json JSONB;
ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS derived_metrics_json JSONB;

CREATE INDEX IF NOT EXISTS idx_filter_task_parent ON filter_task (parent_task_id);
CREATE INDEX IF NOT EXISTS idx_filter_task_kind ON filter_task (task_kind);
