
import streamlit as st
import matplotlib.pyplot as plt
from database import get_connection, initialize_database

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide"
)

# Initialize database
initialize_database()

# Custom styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    div[data-testid="stMetric"] {
        background: #1c2333;
        padding: 18px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def get_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='Income'"
    )
    income = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='Expense'"
    )
    expenses = cursor.fetchone()[0] or 0

    cursor.execute("SELECT goal_amount FROM savings_goal WHERE id=1")
    goal_row = cursor.fetchone()

    conn.close()

    goal = goal_row[0] if goal_row else 0
    return income, expenses, income - expenses, goal


def add_transaction(transaction_type, category, amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO transactions (type, category, amount) VALUES (?, ?, ?)",
        (transaction_type, category, amount)
    )

    conn.commit()
    conn.close()


# Sidebar
st.sidebar.title("💰 Finance Tracker")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Transaction", "Savings Goals",
     "Transaction History", "Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Personal Finance Tracker | Python + SQLite + Streamlit")

# Dashboard
if page == "Dashboard":

    st.title("💰 Personal Finance Dashboard")
    st.write("Manage your money smarter.")

    income, expenses, balance, goal = get_summary()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Income", f"₹{income:,.2f}")
    col2.metric("Total Expenses", f"₹{expenses:,.2f}")
    col3.metric("Available Balance", f"₹{balance:,.2f}")

    st.markdown("---")

    st.subheader("Savings Progress")

    if goal > 0:
        progress = max(0, min(balance / goal, 1))
        st.progress(progress)
        st.write(f"Saved: ₹{balance:,.2f} / Goal: ₹{goal:,.2f}")
        st.write(f"{progress * 100:.1f}% completed")
    else:
        st.info("Set a savings goal to track your progress.")

    st.markdown("---")
    st.subheader("Recent Transactions")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, category, amount, date
        FROM transactions
        ORDER BY date DESC, id DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.dataframe(
            [
                {
                    "ID": r[0],
                    "Type": r[1],
                    "Category": r[2],
                    "Amount (₹)": r[3],
                    "Date": r[4]
                }
                for r in rows
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transactions yet. Add your first transaction!")

# Add Transaction
elif page == "Add Transaction":

    st.title("➕ Add Transaction")

    transaction_type = st.radio(
        "Transaction Type",
        ["Income", "Expense"],
        horizontal=True
    )

    with st.form("transaction_form"):

        category = st.text_input(
            "Category",
            placeholder="e.g. Salary, Food, Rent"
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=100.0
        )

        submitted = st.form_submit_button("Save Transaction")

        if submitted:
            if not category.strip():
                st.error("Please enter a category.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                add_transaction(
                    transaction_type,
                    category.strip(),
                    amount
                )
                st.success(f"{transaction_type} added successfully!")
                st.rerun()

# Savings Goals
elif page == "Savings Goals":

    st.title("🎯 Savings Goals")

    income, expenses, balance, goal = get_summary()

    st.metric("Current Balance", f"₹{balance:,.2f}")

    with st.form("goal_form"):

        new_goal = st.number_input(
            "Your Savings Target (₹)",
            min_value=1.0,
            value=float(goal) if goal > 0 else 10000.0,
            step=500.0
        )

        submitted = st.form_submit_button("Save Goal")

        if submitted:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT OR REPLACE INTO savings_goal (id, goal_amount) VALUES (1, ?)",
                (new_goal,)
            )

            conn.commit()
            conn.close()

            st.success("Savings goal updated!")
            st.rerun()

    if goal > 0:
        progress = max(0, min(balance / goal, 1))
        st.progress(progress)
        st.write(f"Goal completion: {progress * 100:.1f}%")
        st.write(f"Remaining: ₹{max(0, goal - balance):,.2f}")

# Transaction History
elif page == "Transaction History":

    st.title("📋 Transaction History")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, category, amount, date
        FROM transactions
        ORDER BY date DESC, id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.dataframe(
            [
                {
                    "ID": r[0],
                    "Type": r[1],
                    "Category": r[2],
                    "Amount (₹)": r[3],
                    "Date": r[4]
                }
                for r in rows
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transactions available.")

# Analytics
elif page == "Analytics":

    st.title("📊 Financial Analytics")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE type='Expense'
        GROUP BY category
    """)

    expense_rows = cursor.fetchall()

    cursor.execute("""
        SELECT date(date), SUM(amount)
        FROM transactions
        GROUP BY date(date)
        ORDER BY date(date)
    """)

    daily_rows = cursor.fetchall()

    conn.close()

    if expense_rows:

        categories = [r[0] for r in expense_rows]
        amounts = [r[1] for r in expense_rows]

        fig, ax = plt.subplots()
        ax.bar(categories, amounts)
        ax.set_title("Expenses by Category")
        ax.set_ylabel("Amount (₹)")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        fig, ax = plt.subplots()
        ax.pie(
            amounts,
            labels=categories,
            autopct="%1.1f%%",
            startangle=90
        )
        ax.set_title("Spending Distribution")

        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("Add some expenses to see your analytics.")

    if daily_rows:
        dates = [r[0] for r in daily_rows]
        values = [r[1] for r in daily_rows]

        fig, ax = plt.subplots()
        ax.plot(dates, values, marker="o")
        ax.set_title("Daily Transaction Trend")
        ax.set_ylabel("Amount (₹)")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)
