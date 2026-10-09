
import streamlit as st
import pandas as pd
from mysql.connector import Error
from db import get_connection

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)


def run_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


def show_table(query):
    rows = run_query(query, fetch=True)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


st.title("📚 Library Management System")
st.caption("Streamlit • Python • MySQL")

try:
    # Dashboard
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Books", "Members", "Loans", "SQL Demo"]
    )

    if page == "Dashboard":
        col1, col2, col3, col4 = st.columns(4)

        counts = {}
        for table in ["books", "members", "loans", "categories"]:
            result = run_query(
                f"SELECT COUNT(*) AS total FROM {table}",
                fetch=True
            )
            counts[table] = result[0]["total"]

        col1.metric("Book titles", counts["books"])
        col2.metric("Members", counts["members"])
        col3.metric("Loan records", counts["loans"])
        col4.metric("Categories", counts["categories"])

        st.subheader("Book Catalogue")
        show_table("SELECT * FROM book_details ORDER BY book_id")

        st.subheader("Recent Loans")
        show_table(
            "SELECT * FROM loan_details ORDER BY loan_id DESC LIMIT 10"
        )

    elif page == "Books":
        st.subheader("Book Catalogue")

        tab1, tab2, tab3 = st.tabs(
            ["View Books", "Add Book", "Update / Delete"]
        )

        with tab1:
            show_table("SELECT * FROM book_details ORDER BY book_id")

        with tab2:
            with st.form("add_book"):
                title = st.text_input("Book title")
                author = st.text_input("Author")
                publisher_id = st.number_input(
                    "Publisher ID", min_value=1, step=1
                )
                category_id = st.number_input(
                    "Category ID", min_value=1, step=1
                )
                copies = st.number_input(
                    "Total copies", min_value=1, value=1, step=1
                )
                price = st.number_input(
                    "Price", min_value=0.0, value=100.0, step=10.0
                )
                submitted = st.form_submit_button("Add Book")

                if submitted:
                    if not title.strip() or not author.strip():
                        st.error("Enter both title and author.")
                    else:
                        run_query(
                            """INSERT INTO books
                            (title, author, publisher_id, category_id,
                             total_copies, available_copies, price)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (
                                title.strip(), author.strip(),
                                publisher_id, category_id,
                                copies, copies, price
                            )
                        )
                        st.success("Book added successfully.")
                        st.rerun()

        with tab3:
            show_table(
                "SELECT book_id, title, total_copies, available_copies, price "
                "FROM books ORDER BY book_id"
            )

            book_id = st.number_input(
                "Book ID to edit", min_value=1, step=1, key="edit_book_id"
            )
            new_price = st.number_input(
                "New price", min_value=0.0, step=10.0, key="new_price"
            )

            if st.button("Update Price"):
                run_query(
                    "UPDATE books SET price=%s WHERE book_id=%s",
                    (new_price, book_id)
                )
                st.success("Price updated.")
                st.rerun()

            delete_id = st.number_input(
                "Book ID to delete",
                min_value=1,
                step=1,
                key="delete_book_id"
            )
            if st.button("Delete Book"):
                run_query(
                    "DELETE FROM books WHERE book_id=%s",
                    (delete_id,)
                )
                st.success(
                    "Delete command completed. A book referenced by a loan "
                    "cannot be deleted until its loan records are removed."
                )
                st.rerun()

    elif page == "Members":
        st.subheader("Library Members")

        tab1, tab2 = st.tabs(["View Members", "Add Member"])

        with tab1:
            show_table("SELECT * FROM members ORDER BY member_id")

            member_id = st.number_input(
                "Member ID to update",
                min_value=1,
                step=1,
                key="member_update_id"
            )
            phone = st.text_input("New phone number")

            if st.button("Update Phone"):
                run_query(
                    "UPDATE members SET phone=%s WHERE member_id=%s",
                    (phone.strip() or None, member_id)
                )
                st.success("Member updated.")
                st.rerun()

            delete_member_id = st.number_input(
                "Member ID to delete",
                min_value=1,
                step=1,
                key="member_delete_id"
            )

            if st.button("Delete Member"):
                run_query(
                    "DELETE FROM members WHERE member_id=%s",
                    (delete_member_id,)
                )
                st.success(
                    "Delete command completed. A member with loan records "
                    "cannot be deleted until those records are removed."
                )
                st.rerun()

        with tab2:
            with st.form("add_member"):
                name = st.text_input("Full name")
                email = st.text_input("Email")
                phone_new = st.text_input("Phone")
                joined = st.date_input("Joining date")

                submitted = st.form_submit_button("Add Member")

                if submitted:
                    if not name.strip() or not email.strip():
                        st.error("Name and email are required.")
                    else:
                        run_query(
                            """INSERT INTO members
                            (name, email, phone, joined_on)
                            VALUES (%s, %s, %s, %s)""",
                            (
                                name.strip(), email.strip(),
                                phone_new.strip() or None, joined
                            )
                        )
                        st.success("Member added.")
                        st.rerun()

    elif page == "Loans":
        st.subheader("Issue and Return Books")

        tab1, tab2, tab3 = st.tabs(
            ["View Loans", "Issue Book", "Return Book"]
        )

        with tab1:
            show_table(
                "SELECT * FROM loan_details ORDER BY loan_id DESC"
            )

        with tab2:
            members = run_query(
                "SELECT member_id, name FROM members ORDER BY name",
                fetch=True
            )
            books = run_query(
                """SELECT book_id, title FROM books
                   WHERE available_copies > 0 ORDER BY title""",
                fetch=True
            )

            if not members:
                st.warning("Add a member first.")
            elif not books:
                st.warning("No books are currently available.")
            else:
                member_options = {
                    f'{m["name"]} (ID {m["member_id"]})': m["member_id"]
                    for m in members
                }
                book_options = {
                    f'{b["title"]} (ID {b["book_id"]})': b["book_id"]
                    for b in books
                }

                with st.form("issue_book"):
                    selected_member = st.selectbox(
                        "Member", list(member_options.keys())
                    )
                    selected_book = st.selectbox(
                        "Book", list(book_options.keys())
                    )
                    issue_date = st.date_input("Issue date")
                    due_date = st.date_input("Due date")
                    submitted = st.form_submit_button("Issue Book")

                    if submitted:
                        if due_date < issue_date:
                            st.error("Due date cannot precede issue date.")
                        else:
                            run_query(
                                """INSERT INTO loans
                                (member_id, book_id, issue_date, due_date,
                                 status)
                                VALUES (%s, %s, %s, %s, 'Issued')""",
                                (
                                    member_options[selected_member],
                                    book_options[selected_book],
                                    issue_date, due_date
                                )
                            )
                            st.success("Book issued successfully.")
                            st.rerun()

        with tab3:
            active_loans = run_query(
                """SELECT loan_id, member_id, book_id, issue_date, due_date
                   FROM loans WHERE status='Issued' ORDER BY loan_id""",
                fetch=True
            )

            if not active_loans:
                st.info("There are no books awaiting return.")
            else:
                st.dataframe(
                    pd.DataFrame(active_loans),
                    use_container_width=True
                )
                loan_ids = [row["loan_id"] for row in active_loans]
                selected_loan = st.selectbox(
                    "Select loan ID to return", loan_ids
                )
                return_date = st.date_input("Return date")

                if st.button("Confirm Return"):
                    run_query(
                        """UPDATE loans
                           SET status='Returned', return_date=%s
                           WHERE loan_id=%s AND status='Issued'""",
                        (return_date, selected_loan)
                    )
                    st.success("Book returned successfully.")
                    st.rerun()

    elif page == "SQL Demo":
        st.subheader("SQL Command Demonstrations")
        st.write(
            "These read-only examples demonstrate SELECT, JOIN, "
            "GROUP BY, and subqueries. Use the other pages for "
            "INSERT, UPDATE, and DELETE."
        )

        example = st.selectbox(
            "Choose a query",
            [
                "All books",
                "Books with publisher and category",
                "Members with issued books",
                "Count books by category",
                "Books priced above average"
            ]
        )

        queries = {
            "All books":
                "SELECT * FROM books",
            "Books with publisher and category":
                "SELECT * FROM book_details",
            "Members with issued books":
                """SELECT m.name, b.title, l.due_date
                   FROM loans l
                   JOIN members m ON l.member_id=m.member_id
                   JOIN books b ON l.book_id=b.book_id
                   WHERE l.status='Issued'""",
            "Count books by category":
                """SELECT c.category_name, COUNT(b.book_id) AS book_count
                   FROM categories c
                   LEFT JOIN books b ON c.category_id=b.category_id
                   GROUP BY c.category_id, c.category_name""",
            "Books priced above average":
                """SELECT title, price FROM books
                   WHERE price > (SELECT AVG(price) FROM books)"""
        }

        if st.button("Run Query"):
            show_table(queries[example])

except Error as error:
    st.error(f"MySQL error: {error}")
    st.info(
        "Check that MySQL Server is running, your .env credentials "
        "are correct, and schema.sql has been executed."
    )
except Exception as error:
    st.error(f"Error: {error}")
