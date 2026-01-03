-- Создание типов для audit_log
CREATE TYPE entity_type AS ENUM ('debt', 'payment', 'invite');
CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'close');

-- Создание таблицы audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    entity_type entity_type NOT NULL,
    entity_id INTEGER NOT NULL,
    action audit_action NOT NULL,
    actor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    before JSONB,
    after JSONB
);

-- Индекс для audit_log (entity_type, entity_id, occurred_at desc)
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_type_entity_id_occurred_at 
    ON audit_log(entity_type, entity_id, occurred_at DESC);

