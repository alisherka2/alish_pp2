-- Function: search contacts by pattern (name, surname, or phone)
CREATE OR REPLACE FUNCTION search_contacts(pattern TEXT)
RETURNS TABLE(id INT, username VARCHAR, first_name VARCHAR, last_name VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.username, c.first_name, c.last_name, c.phone
    FROM contacts c
    WHERE c.first_name ILIKE '%' || pattern || '%'
       OR c.last_name  ILIKE '%' || pattern || '%'
       OR c.phone      ILIKE '%' || pattern || '%';
END;
$$;


-- 2. Procedure: insert user; if username exists — update phone
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_username   VARCHAR,
    p_first_name VARCHAR,
    p_last_name  VARCHAR,
    p_phone      VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE username = p_username) THEN
        UPDATE contacts SET phone = p_phone WHERE username = p_username;
        RAISE NOTICE 'Updated phone for %', p_username;
    ELSE
        INSERT INTO contacts (username, first_name, last_name, phone)
        VALUES (p_username, p_first_name, p_last_name, p_phone);
        RAISE NOTICE 'Inserted new contact %', p_username;
    END IF;
END;
$$;


-- 3. Procedure: insert many users from arrays; validate phone, return invalid ones
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_usernames   VARCHAR[],
    p_first_names VARCHAR[],
    p_last_names  VARCHAR[],
    p_phones      VARCHAR[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    i       INT;
    total   INT := array_length(p_usernames, 1);
    ph      VARCHAR;
BEGIN
    FOR i IN 1..total LOOP
        ph := p_phones[i];

        -- Validate: phone must start with + and have at least 7 digits
        IF ph IS NULL OR ph !~ '^\+?[0-9\-\s]{7,}$' THEN
            RAISE NOTICE 'Invalid phone for user %: "%"', p_usernames[i], ph;
        ELSE
            INSERT INTO contacts (username, first_name, last_name, phone)
            VALUES (p_usernames[i], p_first_names[i], p_last_names[i], ph)
            ON CONFLICT (username) DO NOTHING;
        END IF;
    END LOOP;
END;
$$;


-- 4. Function: paginated query (LIMIT + OFFSET)
CREATE OR REPLACE FUNCTION get_contacts_page(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, username VARCHAR, first_name VARCHAR, last_name VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.username, c.first_name, c.last_name, c.phone
    FROM contacts c
    ORDER BY c.username
    LIMIT p_limit OFFSET p_offset;
END;
$$;


-- 5. Procedure: delete contact by username OR phone
CREATE OR REPLACE PROCEDURE delete_contact(
    p_username VARCHAR DEFAULT NULL,
    p_phone    VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INT;
BEGIN
    IF p_username IS NOT NULL THEN
        DELETE FROM contacts WHERE username = p_username;
    ELSIF p_phone IS NOT NULL THEN
        DELETE FROM contacts WHERE phone = p_phone;
    ELSE
        RAISE EXCEPTION 'Provide either username or phone.';
    END IF;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % contact(s)', deleted_count;
END;
$$;
