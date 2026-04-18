import sys
from connect import get_connection, create_table

def search_by_pattern():
    pattern = input("  search (name, surname or phone): ").strip()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM search_contacts(%s);", (pattern,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        print("  No contacts found.")
        return

    print(f"\n  {'ID':<5} {'Username':<15} {'First':<12} {'Last':<12} {'Phone'}")
    print("  " + "-" * 58)
    for r in rows:
        print(f"  {r[0]:<5} {r[1]:<15} {str(r[2] or ''):<12} {str(r[3] or ''):<12} {r[4]}")
    print(f"\n  {len(rows)} result(s)")

# 2. Upsert contact (calls SQL procedure)
def upsert_contact():
    print("\nAdd or update contact")
    username   = input("  username   : ").strip()
    first_name = input("  first name : ").strip()
    last_name  = input("  last name  : ").strip()
    phone      = input("  phone      : ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "CALL upsert_contact(%s, %s, %s, %s);",
        (username, first_name, last_name, phone)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("Done.")

# 3. Bulk insert with validation (calls SQL procedure)
def bulk_insert():
    print("\nBulk insert contacts")
    print("Enter contacts one by one. Type 'done' as username to finish.\n")

    usernames, first_names, last_names, phones = [], [], [], []

    while True:
        username = input("  username (or 'done'): ").strip()
        if username.lower() == "done":
            break
        first_name = input("  first name : ").strip()
        last_name  = input("  last name  : ").strip()
        phone      = input("  phone      : ").strip()
        usernames.append(username)
        first_names.append(first_name)
        last_names.append(last_name)
        phones.append(phone)

    if not usernames:
        print("  Nothing to insert.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "CALL bulk_insert_contacts(%s::varchar[], %s::varchar[], %s::varchar[], %s::varchar[]);",
        (usernames, first_names, last_names, phones)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("Bulk insert done. Check notices above for any invalid phones.")

# 4. Paginated query (calls SQL function)
def paginated_query():
    print("\nView contacts (paginated)")
    try:
        limit  = int(input("  contacts per page : ").strip())
        page   = int(input("  page number (1, 2, ...): ").strip())
    except ValueError:
        print("  Error: enter a number.")
        return

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM get_contacts_page(%s, %s);", (limit, offset))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        print("  No contacts on this page.")
        return

    print(f"\n  Page {page}  (showing {len(rows)} record(s))")
    print(f"\n  {'ID':<5} {'Username':<15} {'First':<12} {'Last':<12} {'Phone'}")
    print("  " + "-" * 58)
    for r in rows:
        print(f"  {r[0]:<5} {r[1]:<15} {str(r[2] or ''):<12} {str(r[3] or ''):<12} {r[4]}")

# 5. Delete contact (calls SQL procedure)
def delete_contact():
    print("\nDelete contact")
    print("  1 - by username")
    print("  2 - by phone")
    choice = input("  choice : ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if choice == "1":
        val = input("  username : ").strip()
        cursor.execute("CALL delete_contact(p_username => %s);", (val,))
    elif choice == "2":
        val = input("  phone : ").strip()
        cursor.execute("CALL delete_contact(p_phone => %s);", (val,))
    else:
        print("  Invalid choice.")
        cursor.close()
        conn.close()
        return

    conn.commit()
    cursor.close()
    conn.close()
    print("Done.")

def main_menu():
    create_table()

    while True:
        print("\nPhoneBook – Functions & Procedures")
        print("  1. search by pattern")
        print("  2. add / update contact (upsert)")
        print("  3. bulk insert with validation")
        print("  4. view contacts (paginated)")
        print("  5. delete contact")
        print("  0. exit")

        choice = input("\n> ").strip()

        if choice == "1":
            search_by_pattern()
        elif choice == "2":
            upsert_contact()
        elif choice == "3":
            bulk_insert()
        elif choice == "4":
            paginated_query()
        elif choice == "5":
            delete_contact()
        elif choice == "0":
            print("Bye!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main_menu()
