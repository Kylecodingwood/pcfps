-- 仅建表（无演示数据）。在创建库与用户后手动执行，再执行 db/seed/demo-users.sql。
-- 示例：psql -U pcfps -d pcfps -f db/schema/init_schema.sql

CREATE TABLE user_account (
    id UUID PRIMARY KEY,
    username VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE filter_task (
    id UUID PRIMARY KEY,
    version BIGINT NOT NULL DEFAULT 0,
    owner_user_id UUID NOT NULL REFERENCES user_account (id),
    status VARCHAR(32) NOT NULL,
    input_las_path TEXT NOT NULL,
    output_base_path TEXT NOT NULL,
    external_python_job_id VARCHAR(128),
    error_message TEXT,
    filter_method VARCHAR(16),
    filter_params_json JSONB,
    filter_metrics_json JSONB,
    task_kind VARCHAR(32) NOT NULL DEFAULT 'FILTER',
    parent_task_id UUID REFERENCES filter_task (id) ON DELETE CASCADE,
    derived_method VARCHAR(64),
    derived_params_json JSONB,
    derived_metrics_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_filter_task_owner ON filter_task (owner_user_id);
CREATE INDEX idx_filter_task_status ON filter_task (status);
CREATE INDEX idx_filter_task_filter_method ON filter_task (filter_method);
CREATE INDEX idx_filter_task_parent ON filter_task (parent_task_id);
CREATE INDEX idx_filter_task_kind ON filter_task (task_kind);

CREATE TABLE file_asset (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES filter_task (id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    filename VARCHAR(512) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    stored_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_file_asset_task ON file_asset (task_id);
