-- 存量库升级：为 filter_task 增加滤波方法与参数快照（JSONB）。
-- 在已有库上执行一次，例如：psql -U pcfps -d pcfps -f db/schema/upgrade_add_filter_task_config.sql

ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS filter_method VARCHAR(16);
ALTER TABLE filter_task ADD COLUMN IF NOT EXISTS filter_params_json JSONB;

CREATE INDEX IF NOT EXISTS idx_filter_task_filter_method ON filter_task (filter_method);
