import os
import mysql.connector
import pandas as pd
import streamlit as st

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="RetailPulse | MSME Analytics Hub",
    page_icon="📈",
    layout="wide"
)
st.title("📈 RetailPulse")
st.subheader("MSME Business Analytics & Decision Hub")
st.caption(
    "Understand retail performance. Identify bottlenecks. Make data-driven optimization decisions."
)

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "retailpulse_db")
    )

def load_business_logs():
    connection = get_connection()
    try:
        query = """
            SELECT log_id, store_branch, product_line,
                   issue_category, severity_score, operational_details, log_date
            FROM business_logs
            ORDER BY log_date DESC
        """
        return pd.read_sql(query, connection)
    finally:
        connection.close()

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio(
    "Workspace Navigation",
    ["Executive Dashboard", "Log Operations Data", "Strategic Recommendations"]
)

# Check database connectivity before loading data.
try:
    df = load_business_logs()
except mysql.connector.Error as error:
    st.error(
        "Could not connect to MySQL Server. Ensure that your database server is active, "
        "the database schema is initialized, and credentials are correct."
    )
    st.code(str(error))
    st.stop()

# ---------------- LOG OPERATIONS DATA ----------------
if page == "Log Operations Data":
    st.header("Capture Operational Friction")
    with st.form("operations_form", clear_on_submit=True):
        branch = st.text_input("Store Branch Location")
        product = st.text_input("Product Line / SKU Group")
        category = st.selectbox(
            "Operational Friction Category",
            ["Supply Chain Delay", "Inventory Stockout", "Payment Gateway Failure", 
             "Staff Shortage", "Customer Return/Defect", "Pricing Discrepancy"]
        )
        severity = st.slider("Issue Severity Level (5 = Critical Disruption)", 1, 5, 2)
        details = st.text_area("Operational Details / Field Notes")
        submitted = st.form_submit_button("Record Entry to Database")
        
    if submitted:
        if not branch.strip() or not product.strip():
            st.warning("Validation Error: Please provide both the Branch Location and Product Line.")
        else:
            connection = None
            try:
                connection = get_connection()
                cursor = connection.cursor()
                sql = """
                    INSERT INTO business_logs
                    (store_branch, product_line, issue_category, severity_score, operational_details)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    sql,
                    (branch.strip(), product.strip(), category, severity, details.strip())
                )
                connection.commit()
                st.success("Operational log recorded successfully!")
                st.rerun()
            except mysql.connector.Error as error:
                st.error(f"Database Write Error: {error}")
            finally:
                if connection is not None and connection.is_connected():
                    connection.close()

# ---------------- EXECUTIVE DASHBOARD ----------------
elif page == "Executive Dashboard":
    st.header("Retail Performance Analytics Dashboard")
    if df.empty:
        st.info("No field logs found. Navigate to 'Log Operations Data' to add data records.")
    else:
        avg_severity = df["severity_score"].mean()
        critical_disruptions = df["severity_score"].ge(4).mean() * 100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Operational Logs", len(df))
        col2.metric("Average Severity Index", f"{avg_severity:.2f} / 5")
        col3.metric("Critical Risks (Sev 4+)", f"{critical_disruptions:.1f}%")
        col4.metric("Stable Intervals (Sev 1)", int(df["severity_score"].eq(1).sum()))
        st.divider()
        
        left, right = st.columns(2)
        with left:
            st.subheader("Severity Index by Risk Category")
            category_metrics = df.groupby("issue_category")["severity_score"].mean().sort_values()
            st.bar_chart(category_metrics)
        with right:
            st.subheader("Friction Frequency by Product Line")
            product_metrics = df["product_line"].value_counts()
            st.bar_chart(product_metrics)
            
        st.subheader("Historical Corporate Logs")
        search = st.text_input("Filter Data Workspace by Branch or Product")
        filtered = df.copy()
        if search.strip():
            mask = (
                filtered["store_branch"].str.contains(search, case=False, na=False) |
                filtered["product_line"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        st.dataframe(filtered, width="stretch")

# ---------------- STRATEGIC RECOMMENDATIONS ----------------
else:
    st.header("Data-Driven Strategic Recommendations")
    if df.empty:
        st.info("Informed recommendations will be derived once operations logs are loaded.")
    else:
        category_risk = df.groupby("issue_category")["severity_score"].mean()
        high_risk_sectors = category_risk[category_risk > 3.5]
        actionable_escalations = df[df["severity_score"] >= 4]
        
        st.subheader("Automated Data Interventions")
        if not high_risk_sectors.empty:
            for sector, score in high_risk_sectors.items():
                st.error(
                    f"Urgent Risk: Category '{sector}' has breached safe limits with a severity "
                    f"index of {score:.2f}/5. Deploy core resources to stabilize this metric."
                )
        else:
            st.success("Operational Stability: No specific business functional unit exceeds safety risk levels.")
            
        if not actionable_escalations.empty:
            st.write(f"**Escalation Log:** Immediate action required for {len(actionable_escalations)} incidents.")
            st.dataframe(
                actionable_escalations[["store_branch", "product_line", "issue_category", "severity_score", "operational_details"]],
                use_container_width=True
            )
        st.caption("Friction analytics and thresholds are governed by internal data distributions, not external models.")
