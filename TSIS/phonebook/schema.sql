-- ============================================================
-- schema.sql  –  PhoneBook TSIS 1 (extended schema)
-- Run once against your existing database.
-- ============================================================

-- 1. Groups / categories
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Seed default groups
INSERT INTO groups (name) VALUES
    ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT DO NOTHING;

-- 2. Extend contacts table (safe – uses IF NOT EXISTS idiom via DO block)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='contacts' AND column_name='email'
    ) THEN
        ALTER TABLE contacts
            ADD COLUMN email     VARCHAR(100),
            ADD COLUMN birthday  DATE,
            ADD COLUMN group_id  INTEGER REFERENCES groups(id);
    END IF;
END;
$$;

-- 3. Phones (1-to-many)
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) CHECK (type IN ('home', 'work', 'mobile'))
);
