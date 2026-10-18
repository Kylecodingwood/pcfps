-- 为 filter_task 增加 Python 滤波实验指标快照（JSONB）。
-- 示例：psql -U pcfps -d pcfps -f db/schema/upgrade_add_filter_metrics_json.sql

ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS filter_metrics_json JSONB;
