-- Добавление поля name в таблицу debts
ALTER TABLE debts ADD COLUMN IF NOT EXISTS name VARCHAR(255);

-- Обновление существующих записей: если name NULL, устанавливаем значение по умолчанию
UPDATE debts SET name = CONCAT('Долг #', id) WHERE name IS NULL;

-- Устанавливаем NOT NULL constraint после обновления данных
ALTER TABLE debts ALTER COLUMN name SET NOT NULL;
ALTER TABLE debts ALTER COLUMN name SET DEFAULT 'Долг';

