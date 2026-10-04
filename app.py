from datetime import date
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    add_transaction,
    create_table,
    delete_transaction,
    get_transactions,
    transaction_exists,
)
from ai_assistant import ask_gemma


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="FinTrack AI",
    page_icon="💰",
    layout="wide",
)

create_table()

OWNERS = ["Father", "Uncle"]

TRANSACTION_TYPES = [
    "Bank Deposit",
    "Bank Withdrawal",
    "SIP Contribution",
    "Mutual Fund Purchase",
    "Investment Redemption",
    "Transfer In",
    "Transfer Out",
    "Other Inflow",
    "Other Outflow",
]

CATEGORIES = [
    "Banking",
    "SIP",
    "Mutual Fund",
    "Income",
    "Expense",
    "Transfer",
    "Other",
]


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def money(value):
    """Format an amount in Indian Rupees."""
    return f"₹{float(value):,.2f}"


def safe_number(value):
    """Convert an imported amount to a positive number."""
    if pd.isna(value):
        raise ValueError("Amount is missing.")

    if isinstance(value, str):
        value = (
            value.replace("₹", "")
            .replace(",", "")
            .strip()
        )

    number = float(value)

    if number <= 0:
        raise ValueError("Amount must be greater than zero.")

    return number


def safe_date(value):
    """Convert a spreadsheet date into YYYY-MM-DD."""
    parsed = pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True
    )

    if pd.isna(parsed):
        raise ValueError("Invalid date.")

    return parsed.strftime("%Y-%m-%d")


def normalize_transaction_type(value):
    """Match imported transaction types to known types."""
    if pd.isna(value) or not str(value).strip():
        return "Other Inflow"

    text = str(value).strip().lower()

    aliases = {
        "deposit": "Bank Deposit",
        "bank deposit": "Bank Deposit",
        "withdrawal": "Bank Withdrawal",
        "bank withdrawal": "Bank Withdrawal",
        "sip": "SIP Contribution",
        "sip contribution": "SIP Contribution",
        "mutual fund": "Mutual Fund Purchase",
        "mutual fund purchase": "Mutual Fund Purchase",
        "redemption": "Investment Redemption",
        "investment redemption": "Investment Redemption",
        "transfer in": "Transfer In",
        "transfer out": "Transfer Out",
        "income": "Other Inflow",
        "expense": "Other Outflow",
    }

    return aliases.get(
        text,
        value if value in TRANSACTION_TYPES else "Other Inflow"
    )


def calculate_summary(df):
    """Calculate totals using Python, not the AI model."""
    if df.empty:
        return {
            "deposits": 0.0,
            "withdrawals": 0.0,
            "sip": 0.0,
            "mutual_funds": 0.0,
            "redemptions": 0.0,
            "transfers_in": 0.0,
            "transfers_out": 0.0,
            "other_inflows": 0.0,
            "other_outflows": 0.0,
        }

    totals = (
        df.groupby("transaction_type")["amount"]
        .sum()
        .to_dict()
    )

    return {
        "deposits": totals.get("Bank Deposit", 0.0),
        "withdrawals": totals.get("Bank Withdrawal", 0.0),
        "sip": totals.get("SIP Contribution", 0.0),
        "mutual_funds": totals.get("Mutual Fund Purchase", 0.0),
        "redemptions": totals.get("Investment Redemption", 0.0),
        "transfers_in": totals.get("Transfer In", 0.0),
        "transfers_out": totals.get("Transfer Out", 0.0),
        "other_inflows": totals.get("Other Inflow", 0.0),
        "other_outflows": totals.get("Other Outflow", 0.0),
    }


def make_ai_summary(df):
    """Prepare a compact summary for the local AI model."""
    totals = calculate_summary(df)

    lines = [
        f"Number of recorded transactions: {len(df)}",
        f"Bank deposits: {money(totals['deposits'])}",
        f"Bank withdrawals: {money(totals['withdrawals'])}",
        f"SIP contributions: {money(totals['sip'])}",
        f"Mutual fund purchases: {money(totals['mutual_funds'])}",
        f"Investment redemptions: {money(totals['redemptions'])}",
        f"Transfers in: {money(totals['transfers_in'])}",
        f"Transfers out: {money(totals['transfers_out'])}",
        f"Other inflows: {money(totals['other_inflows'])}",
        f"Other outflows: {money(totals['other_outflows'])}",
    ]

    if not df.empty:
        lines.append(
            f"First recorded date: {df['date'].min()}"
        )
        lines.append(
            f"Last recorded date: {df['date'].max()}"
        )

        category_totals = (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        lines.append("Totals by category:")

        for category, amount in category_totals.items():
            lines.append(f"- {category}: {money(amount)}")

    return "\n".join(lines)


def choose_column(label, columns, key, required=False):
    """Allow the user to map an Excel column."""
    options = [None] + list(columns)

    selected = st.selectbox(
        label,
        options=options,
        format_func=lambda x: "— Skip —" if x is None else str(x),
        key=key,
    )

    if required and selected is None:
        st.warning(f"Please select a column for {label}.")

    return selected


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("💰 FinTrack AI")
st.sidebar.caption("Your family's financial record manager")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Transaction",
        "Transactions",
        "Import Excel",
        "AI Assistant",
    ],
)

owner_filter = st.sidebar.selectbox(
    "View records for",
    ["All"] + OWNERS,
)

st.sidebar.divider()

st.sidebar.caption(
    "Your financial records are stored in a local SQLite "
    "database on this computer. The AI feature uses a "
    "locally running Ollama model."
)

all_df = get_transactions()
df = get_transactions(owner_filter)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":
    st.title("Financial Dashboard")
    st.write(
        "View recorded bank activity and investment contributions."
    )

    if df.empty:
        st.info(
            "No transactions found. Add a transaction or "
            "import an existing Excel file to get started."
        )

    totals = calculate_summary(df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Bank Deposits",
        money(totals["deposits"]),
    )

    col2.metric(
        "Bank Withdrawals",
        money(totals["withdrawals"]),
    )

    col3.metric(
        "SIP Contributions",
        money(totals["sip"]),
    )

    col4.metric(
        "Mutual Fund Purchases",
        money(totals["mutual_funds"]),
    )

    st.caption(
        "These figures represent recorded transaction totals, "
        "not necessarily current bank balances or market values."
    )

    if not df.empty:
        st.subheader("Monthly Financial Activity")

        chart_df = df.copy()
        chart_df["date"] = pd.to_datetime(
            chart_df["date"],
            errors="coerce"
        )

        chart_df = chart_df.dropna(subset=["date"])

        chart_df["month"] = (
            chart_df["date"].dt.to_period("M").astype(str)
        )

        monthly = (
            chart_df.groupby(
                ["month", "transaction_type"]
            )["amount"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            monthly,
            x="month",
            y="amount",
            color="transaction_type",
            barmode="group",
            title="Recorded Amounts by Month",
            labels={
                "month": "Month",
                "amount": "Amount (₹)",
                "transaction_type": "Transaction Type",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.subheader("Category Breakdown")

        category_totals = (
            df.groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig2 = px.pie(
            category_totals,
            names="category",
            values="amount",
            title="Recorded Amounts by Category",
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
        )

        st.subheader("Recent Transactions")

        st.dataframe(
            df.head(10),
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

elif page == "Add Transaction":
    st.title("Add a Transaction")

    with st.form("add_transaction_form"):
        owner = st.selectbox(
            "Record belongs to",
            OWNERS,
        )

        transaction_date = st.date_input(
            "Transaction date",
            value=date.today(),
        )

        description = st.text_input(
            "Description",
            placeholder="e.g. Monthly SIP payment",
        )

        category = st.selectbox(
            "Category",
            CATEGORIES,
        )

        transaction_type = st.selectbox(
            "Transaction type",
            TRANSACTION_TYPES,
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=1000.0,
            step=100.0,
        )

        account = st.text_input(
            "Bank account / investment name",
            placeholder="e.g. Savings account or fund name",
        )

        submitted = st.form_submit_button(
            "Save Transaction",
            use_container_width=True,
        )

        if submitted:
            if not description.strip():
                st.error("Please enter a description.")
            else:
                try:
                    add_transaction(
                        owner=owner,
                        date=transaction_date.isoformat(),
                        description=description,
                        category=category,
                        transaction_type=transaction_type,
                        amount=amount,
                        account=account,
                    )

                    st.success("Transaction saved successfully!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not save transaction: {error}")


# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------

elif page == "Transactions":
    st.title("Transaction History")

    if df.empty:
        st.info("No transactions available.")
    else:
        search = st.text_input(
            "Search description, category, or account"
        )

        display_df = df.copy()

        if search.strip():
            mask = (
                display_df["description"].fillna("").str.contains(
                    search, case=False, na=False
                )
                | display_df["category"].fillna("").str.contains(
                    search, case=False, na=False
                )
                | display_df["account"].fillna("").str.contains(
                    search, case=False, na=False
                )
            )

            display_df = display_df[mask]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = display_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "Export displayed transactions as CSV",
            data=csv_data,
            file_name="fintrack_transactions.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Delete a Transaction")

        transaction_ids = display_df["id"].tolist()

        if transaction_ids:
            selected_id = st.selectbox(
                "Select transaction ID",
                transaction_ids,
            )

            confirm_delete = st.checkbox(
                "I understand this permanently deletes the selected record."
            )

            if st.button(
                "Delete Selected Transaction",
                disabled=not confirm_delete,
            ):
                delete_transaction(selected_id)
                st.success("Transaction deleted.")
                st.rerun()


# --------------------------------------------------
# IMPORT EXCEL OR CSV
# --------------------------------------------------

elif page == "Import Excel":
    st.title("Import Existing Financial Records")

    st.write(
        "Upload an Excel or CSV file. Choose which columns "
        "contain the dates, descriptions, and amounts."
    )

    st.warning(
        "Use a copy of your spreadsheet. Check the preview "
        "before importing. Do not upload sensitive financial "
        "files to public websites."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"],
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                imported_df = pd.read_csv(uploaded_file)
            else:
                imported_df = pd.read_excel(uploaded_file)

            if imported_df.empty:
                st.warning("The selected file contains no rows.")
            else:
                st.subheader("Spreadsheet Preview")

                st.dataframe(
                    imported_df.head(20),
                    use_container_width=True,
                    hide_index=True,
                )

                columns = list(imported_df.columns)

                st.subheader("Map Your Columns")

                col1, col2 = st.columns(2)

                with col1:
                    date_col = choose_column(
                        "Date column",
                        columns,
                        "import_date",
                        required=True,
                    )

                    description_col = choose_column(
                        "Description column",
                        columns,
                        "import_description",
                        required=True,
                    )

                    amount_col = choose_column(
                        "Amount column",
                        columns,
                        "import_amount",
                        required=True,
                    )

                with col2:
                    category_col = choose_column(
                        "Category column (optional)",
                        columns,
                        "import_category",
                    )

                    type_col = choose_column(
                        "Transaction type column (optional)",
                        columns,
                        "import_type",
                    )

                    account_col = choose_column(
                        "Account column (optional)",
                        columns,
                        "import_account",
                    )

                import_owner = st.selectbox(
                    "These records belong to",
                    OWNERS,
                    key="import_owner",
                )

                default_type = st.selectbox(
                    "Default transaction type",
                    TRANSACTION_TYPES,
                    key="import_default_type",
                )

                if st.button(
                    "Import Records",
                    type="primary",
                    use_container_width=True,
                ):
                    if (
                        date_col is None
                        or description_col is None
                        or amount_col is None
                    ):
                        st.error(
                            "Select the date, description, "
                            "and amount columns."
                        )
                    else:
                        imported_count = 0
                        skipped_count = 0
                        errors = []

                        for row_number, row in imported_df.iterrows():
                            try:
                                transaction_date = safe_date(
                                    row[date_col]
                                )

                                description = str(
                                    row[description_col]
                                ).strip()

                                if (
                                    not description
                                    or description.lower() == "nan"
                                ):
                                    raise ValueError(
                                        "Description is missing."
                                    )

                                amount = safe_number(
                                    row[amount_col]
                                )

                                if category_col is not None:
                                    raw_category = row[category_col]

                                    if (
                                        pd.isna(raw_category)
                                        or not str(raw_category).strip()
                                    ):
                                        category = "Other"
                                    else:
                                        category = str(
                                            raw_category
                                        ).strip()
                                else:
                                    category = "Other"

                                if type_col is not None:
                                    transaction_type = (
                                        normalize_transaction_type(
                                            row[type_col]
                                        )
                                    )
                                else:
                                    transaction_type = default_type

                                if account_col is not None:
                                    raw_account = row[account_col]

                                    account = (
                                        ""
                                        if pd.isna(raw_account)
                                        else str(raw_account).strip()
                                    )
                                else:
                                    account = ""

                                if transaction_exists(
                                    import_owner,
                                    transaction_date,
                                    description,
                                    amount,
                                    account,
                                ):
                                    skipped_count += 1
                                    continue

                                add_transaction(
                                    owner=import_owner,
                                    date=transaction_date,
                                    description=description,
                                    category=category,
                                    transaction_type=transaction_type,
                                    amount=amount,
                                    account=account,
                                )

                                imported_count += 1

                            except Exception as error:
                                skipped_count += 1

                                if len(errors) < 10:
                                    errors.append(
                                        f"Row {row_number + 2}: {error}"
                                    )

                        st.success(
                            f"Imported {imported_count} records. "
                            f"Skipped {skipped_count} records."
                        )

                        if errors:
                            st.warning(
                                "Some rows could not be imported:"
                            )

                            for message in errors:
                                st.write(f"- {message}")

                        st.info(
                            "Please check the Transactions page "
                            "to verify the imported records."
                        )

        except Exception as error:
            st.error(
                f"Could not read the file: {error}"
            )


# --------------------------------------------------
# AI ASSISTANT
# --------------------------------------------------

elif page == "AI Assistant":
    st.title("Ask FinTrack AI")
    st.write(
        "Ask questions about the financial records currently "
        "selected in the sidebar."
    )

    st.info(
        "The assistant uses locally running Gemma through Ollama. "
        "Python calculates the totals; the model explains them."
    )

    if df.empty:
        st.warning(
            "There are no records to analyze. Add or import "
            "some transactions first."
        )
    else:
        model_name = st.text_input(
            "Ollama model name",
            value="gemma3:1b",
            help=(
                "Use the exact model name shown by the "
                "ollama list command."
            ),
        )

        question = st.text_area(
            "Your question",
            placeholder=(
                "e.g. Summarize my recorded SIP contributions "
                "and bank activity."
            ),
        )

        with st.expander("View the summary sent to Gemma"):
            st.code(
                make_ai_summary(df),
                language="text",
            )

        if st.button(
            "Ask AI",
            type="primary",
            use_container_width=True,
        ):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner(
                    "Asking your local AI model..."
                ):
                    answer = ask_gemma(
                        question=question.strip(),
                        financial_summary=make_ai_summary(df),
                        model=model_name.strip(),
                    )

                st.subheader("FinTrack AI's Response")
                st.write(answer)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.sidebar.divider()

st.sidebar.caption(
    "FinTrack AI is a personal recordkeeping tool. "
    "It does not connect to banks, verify balances, "
    "or provide investment recommendations."
)