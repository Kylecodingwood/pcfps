-- 演示数据：请在执行 db/schema/init_schema.sql 建表之后再运行（与 DDL 分离）。
-- Example: psql -U pcfps -d pcfps -f db/seed/demo-users.sql
--
-- Login: username demo / password password

INSERT INTO user_account (id, username, password_hash, enabled, created_at)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'demo',
    '$2a$10$XgXudm0B4Dum9K4Jy6zMGOoWobLoFOF.as1YE0fR.1yzLuMqvF.N2',
    TRUE,
    NOW()
)
ON CONFLICT (username) DO NOTHING;
