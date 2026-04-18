import csv
import sys
from connect import get_connection, create_table


def insert_from_csv(filepath="contacts.csv"):
    conn = get_connection()
    cursor = conn.cursor()
    inserted = skipped = 0

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cursor.execute("""
                INSERT INTO contacts (username, first_name, last_name, phone)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING;
            """, (row["username"], row["first_name"], row["last_name"], row["phone"]))
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Done. Inserted: {inserted}, skipped: {skipped}")


def insert_from_console():
    print("\nAdd contact")
    username   = input("  username   : ").strip()
    first_name = input("  first name : ").strip() or None
    last_name  = input("  last name  : ").strip() or None
    phone      = input("  phone      : ").strip()

    if not username or not phone:
        print("Error: username and phone are required.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO contacts (username, first_name, last_name, phone)
            VALUES (%s, %s, %s, %s);
        """, (username, first_name, last_name, phone))
        conn.commit()
        print(f"Added '{username}'.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()


def update_contact():
    print("\nUpdate contact")
    username = input("  username : ").strip()
    print("  1 - first name")
    print("  2 - phone")
    choice = input("  choice   : ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if choice == "1":
        val = input("  new first name : ").strip()
        cursor.execute("UPDATE contacts SET first_name = %s WHERE username = %s;", (val, username))
    elif choice == "2":
        val = input("  new phone : ").strip()
        cursor.execute("UPDATE contacts SET phone = %s WHERE username = %s;", (val, username))
    else:
        print("Invalid choice.")
        cursor.close()
        conn.close()
        return

    if cursor.rowcount == 0:
        print(f"No contact found: '{username}'")
    else:
        conn.commit()
        print("Updated.")

    cursor.close()
    conn.close()


def search_contacts():
    print("\nSearch contacts")
    print("  1 - username")
    print("  2 - first name")
    print("  3 - last name")
    print("  4 - phone prefix")
    print("  5 - show all")
    choice = input("  choice : ").strip()

    conn = get_connection()
    cursor = conn.cursor()
    q = "SELECT id, username, first_name, last_name, phone FROM contacts"

    if choice == "1":
        val = input("  username : ").strip()
        cursor.execute(q + " WHERE username = %s;", (val,))
    elif choice == "2":
        val = input("  first name : ").strip()
        cursor.execute(q + " WHERE first_name ILIKE %s;", (f"%{val}%",))
    elif choice == "3":
        val = input("  last name : ").strip()
        cursor.execute(q + " WHERE last_name ILIKE %s;", (f"%{val}%",))
    elif choice == "4":
        val = input("  phone prefix : ").strip()
        cursor.execute(q + " WHERE phone LIKE %s;", (f"{val}%",))
    elif choice == "5":
        cursor.execute(q + " ORDER BY username;")
    else:
        print("Invalid choice.")
        cursor.close()
        conn.close()
        return

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print("No contacts found.")
        return

    print(f"\n  {'ID':<5} {'Username':<15} {'First':<12} {'Last':<12} {'Phone'}")
    print("  " + "-" * 58)
    for r in rows:
        print(f"  {r[0]:<5} {r[1]:<15} {str(r[2] or ''):<12} {str(r[3] or ''):<12} {r[4]}")
    print(f"\n  {len(rows)} result(s)")


def delete_contact():
    print("\nDelete contact")
    print("  1 - by username")
    print("  2 - by phone")
    choice = input("  choice : ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if choice == "1":
        val = input("  username : ").strip()
        cursor.execute("DELETE FROM contacts WHERE username = %s;", (val,))
    elif choice == "2":
        val = input("  phone : ").strip()
        cursor.execute("DELETE FROM contacts WHERE phone = %s;", (val,))
    else:
        print("Invalid choice.")
        cursor.close()
        conn.close()
        return

    if cursor.rowcount == 0:
        print("No contact found.")
    else:
        conn.commit()
        print(f"Deleted {cursor.rowcount} contact(s).")

    cursor.close()
    conn.close()


def main_menu():
    create_table()

    while True:
        print("\nPhoneBook")
        print("  1. import from CSV")
        print("  2. add contact")
        print("  3. update contact")
        print("  4. search contacts")
        print("  5. delete contact")
        print("  0. exit")

        choice = input("\n> ").strip()

        if choice == "1":
            path = input("CSV path [contacts.csv]: ").strip() or "contacts.csv"
            insert_from_csv(path)
        elif choice == "2":
            insert_from_console()
        elif choice == "3":
            update_contact()
        elif choice == "4":
            search_contacts()
        elif choice == "5":
            delete_contact()
        elif choice == "0":
            print("Bye!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main_menu()
