-- Создание таблицы users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для tg_user_id (уже есть UNIQUE, но явно указываем для ясности)
CREATE INDEX IF NOT EXISTS idx_users_tg_user_id ON users(tg_user_id);

