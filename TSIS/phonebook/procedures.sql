-- ============================================================
-- procedures.sql  –  PhoneBook TSIS 1  (new server-side objects)
-- Do NOT re-run functions.sql; this file adds NEW objects only.
-- ============================================================

-- 1. Procedure: add a phone number to an existing contact
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,   -- matches username
    p_phone        VARCHAR,
    p_type         VARCHAR    -- 'home' | 'work' | 'mobile'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id INTEGER;
BEGIN
    SELECT id INTO v_id FROM contacts WHERE username = p_contact_name;

    IF v_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Use home / work / mobile.', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact %.', p_phone, p_type, p_contact_name;
END;
$$;


-- 2. Procedure: move contact to a group (creates group if absent)
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE username = p_contact_name;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Create group if it doesn't exist
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact % moved to group %.', p_contact_name, p_group_name;
END;
$$;


-- 3. Function: extended search — covers name, email, AND all phones in phones table
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id         INT,
    username   VARCHAR,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    grp        VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.username,
        c.first_name,
        c.last_name,
        c.email,
        c.birthday,
        g.name AS grp
    FROM contacts c
    LEFT JOIN groups g  ON g.id = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE
        c.first_name ILIKE '%' || p_query || '%'
     OR c.last_name  ILIKE '%' || p_query || '%'
     OR c.email      ILIKE '%' || p_query || '%'
     OR ph.phone     ILIKE '%' || p_query || '%'
    ORDER BY c.username;
END;
$$;
