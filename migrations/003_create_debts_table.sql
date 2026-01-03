-- Создание типа для статуса долга
CREATE TYPE debt_status AS ENUM ('active', 'closed');

-- Создание таблицы debts
CREATE TABLE debts (
    id SERIAL PRIMARY KEY,
    debtor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    creditor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'RUB',
    monthly_payment NUMERIC(15, 2) CHECK (monthly_payment > 0),
    due_day INTEGER CHECK (due_day >= 1 AND due_day <= 31),
    status debt_status NOT NULL DEFAULT 'active',
    closed_at TIMESTAMP WITH TIME ZONE,
    close_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для debts
CREATE INDEX IF NOT EXISTS idx_debts_debtor_user_id ON debts(debtor_user_id);
CREATE INDEX IF NOT EXISTS idx_debts_creditor_user_id ON debts(creditor_user_id);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_debts_updated_at BEFORE UPDATE ON debts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

