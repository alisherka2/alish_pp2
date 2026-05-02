"""
phonebook.py  –  PhoneBook TSIS 1
Extends Practice 8 with:
  • filter by group, search by email, sort, paginated navigation
  • JSON export / import with duplicate handling
  • Extended CSV import (email, birthday, group, phone type)
  • add_phone, move_to_group procedures
  • search_contacts covering all phones + email
"""
import sys
import csv
import json
from datetime import date, datetime
from connect import get_connection, create_table

# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────

def _header():
    print(f"\n  {'ID':<5} {'Username':<15} {'First':<12} {'Last':<12} "
          f"{'Email':<25} {'Birthday':<12} {'Group':<10}")
    print("  " + "─" * 95)

def _print_row(r):
    # r: (id, username, first_name, last_name, email, birthday, grp)
    bday = str(r[5]) if r[5] else ""
    print(f"  {r[0]:<5} {str(r[1] or ''):<15} {str(r[2] or ''):<12} "
          f"{str(r[3] or ''):<12} {str(r[4] or ''):<25} {bday:<12} {str(r[6] or ''):<10}")


# ─────────────────────────────────────────────────────────────
# 1. Extended search (name / email / all phones)
# ─────────────────────────────────────────────────────────────

def search_by_pattern():
    pattern = input("  Search (name, email, or phone): ").strip()
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM search_contacts(%s);", (pattern,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        print("  No contacts found.")
        return

    _header()
    for r in rows:
        _print_row(r)
    print(f"\n  {len(rows)} result(s)")


# ─────────────────────────────────────────────────────────────
# 2. Filter by group
# ─────────────────────────────────────────────────────────────

def filter_by_group():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY name;")
    groups = cur.fetchall()
    cur.close(); conn.close()

    print("\n  Groups:")
    for g in groups:
        print(f"    {g[0]}. {g[1]}")

    try:
        gid = int(input("  Enter group id: ").strip())
    except ValueError:
        print("  Invalid input."); return

    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.username, c.first_name, c.last_name,
               c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.group_id = %s
        ORDER BY c.username;
    """, (gid,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        print("  No contacts in this group."); return

    _header()
    for r in rows:
        _print_row(r)
    print(f"\n  {len(rows)} contact(s) in group.")


# ─────────────────────────────────────────────────────────────
# 3. Search by email (partial match)
# ─────────────────────────────────────────────────────────────

def search_by_email():
    fragment = input("  Email fragment (e.g. gmail): ").strip()
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.username, c.first_name, c.last_name,
               c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.email ILIKE %s
        ORDER BY c.username;
    """, (f"%{fragment}%",))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        print("  No contacts found."); return

    _header()
    for r in rows:
        _print_row(r)
    print(f"\n  {len(rows)} result(s)")


# ─────────────────────────────────────────────────────────────
# 4. Sort contacts (name / birthday / date added)
# ─────────────────────────────────────────────────────────────

def view_sorted():
    print("\n  Sort by:")
    print("    1. Name (username)")
    print("    2. Birthday")
    print("    3. Date added (created_at)")
    choice = input("  > ").strip()

    order_map = {"1": "c.username", "2": "c.birthday", "3": "c.created_at"}
    order_col = order_map.get(choice, "c.username")

    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"""
        SELECT c.id, c.username, c.first_name, c.last_name,
               c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY {order_col} NULLS LAST;
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        print("  No contacts."); return

    _header()
    for r in rows:
        _print_row(r)


# ─────────────────────────────────────────────────────────────
# 5. Paginated navigation (next / prev / quit)
# ─────────────────────────────────────────────────────────────

def paginated_navigation():
    try:
        limit = int(input("  Contacts per page: ").strip())
    except ValueError:
        print("  Invalid number."); return

    page = 1
    while True:
        offset = (page - 1) * limit
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM get_contacts_page(%s, %s);", (limit, offset))
        rows = cur.fetchall()
        cur.close(); conn.close()

        print(f"\n  ── Page {page} ──")
        if not rows:
            print("  (no contacts on this page)")
        else:
            print(f"  {'ID':<5} {'Username':<15} {'First':<12} {'Last':<12} {'Phone'}")
            print("  " + "─" * 58)
            for r in rows:
                print(f"  {r[0]:<5} {r[1]:<15} {str(r[2] or ''):<12} "
                      f"{str(r[3] or ''):<12} {r[4]}")

        print("\n  [n] next   [p] prev   [q] quit")
        nav = input("  > ").strip().lower()

        if nav == "n":
            if rows:
                page += 1
            else:
                print("  Already on last page.")
        elif nav == "p":
            if page > 1:
                page -= 1
            else:
                print("  Already on first page.")
        elif nav == "q":
            break
        else:
            print("  Invalid key.")


# ─────────────────────────────────────────────────────────────
# 6. Export to JSON
# ─────────────────────────────────────────────────────────────

def export_to_json():
    path = input("  Output file (default: contacts.json): ").strip() or "contacts.json"

    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.username, c.first_name, c.last_name,
               c.email, c.birthday::text, g.name AS grp
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY c.username;
    """)
    contacts = cur.fetchall()

    result = []
    for c in contacts:
        cid, username, first_name, last_name, email, birthday, grp = c
        cur.execute("SELECT phone, type FROM phones WHERE contact_id = %s;", (cid,))
        phones = [{"phone": row[0], "type": row[1]} for row in cur.fetchall()]
        result.append({
            "username":   username,
            "first_name": first_name,
            "last_name":  last_name,
            "email":      email,
            "birthday":   birthday,
            "group":      grp,
            "phones":     phones,
        })

    cur.close(); conn.close()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  Exported {len(result)} contact(s) to '{path}'.")


# ─────────────────────────────────────────────────────────────
# 7. Import from JSON (with duplicate handling)
# ─────────────────────────────────────────────────────────────

def _get_or_create_group(cur, name):
    if not name:
        return None
    cur.execute("INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (name,))
    cur.execute("SELECT id FROM groups WHERE name = %s;", (name,))
    return cur.fetchone()[0]


def _normalize_phones(raw_phones):
    """
    Accept phones in any of these formats and return
    a list of {"phone": str, "type": str} dicts:
      - [{"phone": "...", "type": "..."}]   ← new format
      - ["0771234567"]                       ← list of strings
      - [8771234567]                         ← list of ints
      - "0771234567"                         ← bare string
      - 8771234567                           ← bare int
    """
    if raw_phones is None:
        return []
    if not isinstance(raw_phones, list):
        raw_phones = [raw_phones]
    result = []
    for ph in raw_phones:
        if isinstance(ph, dict):
            result.append({"phone": str(ph.get("phone", "")), "type": ph.get("type", "mobile")})
        else:
            result.append({"phone": str(ph), "type": "mobile"})
    return result


def import_from_json():
    path = input("  JSON file path: ").strip()
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Error reading file: {e}"); return

    conn = get_connection(); cur = conn.cursor()
    inserted = skipped = overwritten = 0

    for rec in records:
        username = rec.get("username", "").strip()
        if not username:
            print("  Skipping record with no username."); skipped += 1; continue

        cur.execute("SELECT id FROM contacts WHERE username = %s;", (username,))
        existing = cur.fetchone()

        if existing:
            print(f"  Duplicate: '{username}'")
            action = input("    [s]kip / [o]verwrite: ").strip().lower()
            if action != "o":
                skipped += 1; continue

            # Overwrite
            group_id = _get_or_create_group(cur, rec.get("group"))
            cur.execute("""
                UPDATE contacts
                SET first_name=%s, last_name=%s, email=%s,
                    birthday=%s, group_id=%s
                WHERE username=%s;
            """, (rec.get("first_name"), rec.get("last_name"),
                  rec.get("email"), rec.get("birthday"),
                  group_id, username))
            cid = existing[0]
            cur.execute("DELETE FROM phones WHERE contact_id = %s;", (cid,))
            for ph in _normalize_phones(rec.get("phones")):
                cur.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                            (cid, ph["phone"], ph["type"]))
            overwritten += 1
        else:
            group_id = _get_or_create_group(cur, rec.get("group"))
            phones = _normalize_phones(rec.get("phones"))
            primary_phone = phones[0]["phone"] if phones else ""
            cur.execute("""
                INSERT INTO contacts (username, first_name, last_name, phone,
                                      email, birthday, group_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                RETURNING id;
            """, (username, rec.get("first_name"), rec.get("last_name"),
                  primary_phone, rec.get("email"), rec.get("birthday"), group_id))
            cid = cur.fetchone()[0]
            for ph in phones:
                cur.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                            (cid, ph["phone"], ph["type"]))
            inserted += 1

    conn.commit(); cur.close(); conn.close()
    print(f"\n  Done. Inserted: {inserted}  Overwritten: {overwritten}  Skipped: {skipped}")


# ─────────────────────────────────────────────────────────────
# 8. Extended CSV import (email, birthday, group, phone type)
# ─────────────────────────────────────────────────────────────

def import_from_csv():
    path = input("  CSV file path (default: contacts.csv): ").strip() or "contacts.csv"
    try:
        f = open(path, encoding="utf-8")
    except FileNotFoundError:
        print(f"  File '{path}' not found."); return

    reader = csv.DictReader(f)
    conn = get_connection(); cur = conn.cursor()
    inserted = skipped = 0

    for row in reader:
        username = row.get("username", "").strip()
        phone    = row.get("phone", "").strip()
        if not username or not phone:
            print(f"  Skipping row (missing username or phone): {row}")
            skipped += 1; continue

        group_id = _get_or_create_group(cur, row.get("group", "").strip() or None)

        birthday = row.get("birthday", "").strip() or None
        email    = row.get("email", "").strip() or None
        p_type   = row.get("phone_type", "mobile").strip()
        if p_type not in ("home", "work", "mobile"):
            p_type = "mobile"

        cur.execute("SELECT id FROM contacts WHERE username = %s;", (username,))
        existing = cur.fetchone()

        if existing:
            print(f"  Skipping duplicate: {username}"); skipped += 1; continue

        cur.execute("""
            INSERT INTO contacts (username, first_name, last_name, phone,
                                  email, birthday, group_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            RETURNING id;
        """, (username, row.get("first_name","").strip(),
              row.get("last_name","").strip(), phone,
              email, birthday, group_id))
        cid = cur.fetchone()[0]
        cur.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                    (cid, phone, p_type))
        inserted += 1

    conn.commit(); cur.close(); conn.close(); f.close()
    print(f"  CSV import done. Inserted: {inserted}  Skipped: {skipped}")


# ─────────────────────────────────────────────────────────────
# 9. Add phone number to existing contact
# ─────────────────────────────────────────────────────────────

def add_phone():
    username = input("  Username: ").strip()
    phone    = input("  Phone number: ").strip()
    print("  Type: 1=home  2=work  3=mobile")
    t = input("  > ").strip()
    ptype = {"1": "home", "2": "work", "3": "mobile"}.get(t, "mobile")

    conn = get_connection(); cur = conn.cursor()
    cur.execute("CALL add_phone(%s, %s, %s);", (username, phone, ptype))
    conn.commit(); cur.close(); conn.close()
    print("  Phone added.")


# ─────────────────────────────────────────────────────────────
# 10. Move contact to group
# ─────────────────────────────────────────────────────────────

def move_to_group():
    username   = input("  Username: ").strip()
    group_name = input("  Group name (will be created if absent): ").strip()

    conn = get_connection(); cur = conn.cursor()
    cur.execute("CALL move_to_group(%s, %s);", (username, group_name))
    conn.commit(); cur.close(); conn.close()
    print(f"  Moved '{username}' to group '{group_name}'.")


# ─────────────────────────────────────────────────────────────
# main menu
# ─────────────────────────────────────────────────────────────

def main_menu():
    create_table()

    while True:
        print("\n╔══════════════════════════════════════╗")
        print("║     PhoneBook – TSIS 1               ║")
        print("╠══════════════════════════════════════╣")
        print("║  Search & View                       ║")
        print("║   1. Search (name / email / phone)   ║")
        print("║   2. Filter by group                 ║")
        print("║   3. Search by email                 ║")
        print("║   4. View sorted (name/bday/date)    ║")
        print("║   5. Paginated navigation            ║")
        print("╠══════════════════════════════════════╣")
        print("║  Import / Export                     ║")
        print("║   6. Export to JSON                  ║")
        print("║   7. Import from JSON                ║")
        print("║   8. Import from CSV (extended)      ║")
        print("╠══════════════════════════════════════╣")
        print("║  Manage                              ║")
        print("║   9. Add phone to contact            ║")
        print("║  10. Move contact to group           ║")
        print("╠══════════════════════════════════════╣")
        print("║   0. Exit                            ║")
        print("╚══════════════════════════════════════╝")

        choice = input("\n> ").strip()

        if   choice == "1":  search_by_pattern()
        elif choice == "2":  filter_by_group()
        elif choice == "3":  search_by_email()
        elif choice == "4":  view_sorted()
        elif choice == "5":  paginated_navigation()
        elif choice == "6":  export_to_json()
        elif choice == "7":  import_from_json()
        elif choice == "8":  import_from_csv()
        elif choice == "9":  add_phone()
        elif choice == "10": move_to_group()
        elif choice == "0":
            print("Bye!"); sys.exit(0)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main_menu()
