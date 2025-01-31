import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Obtener la fecha y hora de la última actualización del archivo
def get_last_update_time(file_path):
    if os.path.exists(file_path):
        # Obtener el tiempo de modificación del archivo
        last_modified_time = os.path.getmtime(file_path)
        # Convertir a formato de fecha y hora legible
        return datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return "File not found"

# Llama a la función para obtener la última actualización
last_update = get_last_update_time('Data.csv')


# Configure Streamlit page
st.set_page_config(page_title="Case Dashboard", layout="wide")

# Load data using cache
@st.cache_data
def load_data():
    df = pd.read_csv('Data.csv')

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    return df

# Navigation button
page = st.sidebar.radio("Go to", ["Dashboard", "Instructions"])

# Load dataset
df = load_data()

# Verify essential columns
if 'created_at' in df.columns:
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
else:
    st.error("⚠️ The column 'created_at' is missing in the dataset.")

if 'assignee_name' in df.columns:
    df['assignee_name'] = df['assignee_name'].fillna('Un-assignee')
else:
    st.error("⚠️ The column 'assignee_name' is missing in the dataset.")

if 'check_status' in df.columns:
    df['check_status_original'] = df['check_status']
    df['check_status_kpi'] = df['check_status'].replace(['in_progress', 'processing', 'need_review'], 'pending')
else:
    st.error("⚠️ The column 'check_status' is missing in the dataset.")

# 📊 **Dashboard**
if page == "Dashboard":
    st.title("📊 Case Dashboard")
    st.markdown("### 📌 Overview of Cases and Checks")

    # 📌 **Sidebar - Filters**
    with st.sidebar.expander("🎯 Case Filters", expanded=False):
        case_status_filter = st.multiselect("Filter by Case Status", df['cases_status'].unique(), default=df['cases_status'].unique())
        assignee_filter = st.multiselect("Filter by Assignee", df['assignee_name'].unique(), default=df['assignee_name'].unique())

    with st.sidebar.expander("🛠️ Check Filters", expanded=False):
        check_status_filter = st.multiselect("Filter by Check Status", df['check_status_original'].unique(), default=df['check_status_original'].unique())
        check_type_filter = st.multiselect("Filter by Check Type", df['check_type'].unique(), default=df['check_type'].unique())

    with st.sidebar.expander("🌍 Additional Filters", expanded=False):
        if 'country' in df.columns:
            country_list = df['country'].dropna().unique()
            selected_country = st.text_input("🔍 Search Country", "").strip()
            country_filter = [c for c in country_list if selected_country.lower() in c.lower()] if selected_country else country_list
        else:
            st.warning("⚠️ The column 'country' is missing in the dataset.")
            country_filter = []

        pep_filter = st.selectbox("🛡️ Filter by PEP", ["All", "Yes", "No"])

        if 'risk_level' in df.columns:
            risk_level_filter = st.multiselect("⚠️ Filter by Risk Level", df['risk_level'].dropna().unique(), default=df['risk_level'].dropna().unique())
        else:
            st.warning("⚠️ The column 'risk_level' is missing in the dataset.")
            risk_level_filter = []
        
        start_date = st.date_input("📅 Start Date", df['created_at'].min())
        end_date = st.date_input("📅 End Date", df['created_at'].max())
      
st.markdown("---")
st.info(f"📅 **Last Updated:** {last_update}")

    
    start_date = pd.to_datetime(start_date).normalize()
    end_date = pd.to_datetime(end_date).normalize()


    # Apply filters
    df_filtered = df[
        df['cases_status'].isin(case_status_filter) & 
        df['check_status_original'].isin(check_status_filter) &  
        df['assignee_name'].isin(assignee_filter) & 
        df['check_type'].isin(check_type_filter) & 
        df['country'].isin(country_filter) &  
        df['risk_level'].isin(risk_level_filter) &
        (df['created_at'] >= start_date) & 
        (df['created_at'] <= end_date)
    ]

    if pep_filter == "Yes":
        df_filtered = df_filtered[df_filtered['is_pep'] == True]
    elif pep_filter == "No":
        df_filtered = df_filtered[df_filtered['is_pep'] == False]

  

    # 📊 **Case KPIs**
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="🟡 Open Cases", value=df_filtered[df_filtered['cases_status'] == 'open']['case_id'].nunique())
    with col2:
        st.metric(label="🟢 Approved Cases", value=df_filtered[df_filtered['cases_status'] == 'approved']['case_id'].nunique())
    with col3:
        st.metric(label="🔴 Rejected Cases", value=df_filtered[df_filtered['cases_status'] == 'rejected']['case_id'].nunique())
    with col4:
        st.metric(label="⚫ Total Cases", value=df_filtered['case_id'].nunique())

    # 📊 **Check KPIs**
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label="🟡 Pending Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'pending']['check_id'].nunique())
    with col6:
        st.metric(label="🟢 Approved Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'approved']['check_id'].nunique())
    with col7:
        st.metric(label="🔴 Rejected Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'rejected']['check_id'].nunique())
    with col8:
        st.metric(label="⚫ Total Checks", value=df_filtered['check_id'].nunique())

    # 📊 **Charts**
    df_filtered['Month'] = df_filtered['created_at'].dt.to_period('M').astype(str)
    df_monthly_cases = df_filtered.groupby(['Month', 'assignee_name'])['case_id'].nunique().reset_index(name='Case Count')
    df_monthly_checks = df_filtered.groupby(['Month', 'assignee_name'])['check_id'].nunique().reset_index(name='Check Count')

    if not df_monthly_cases.empty:
        st.markdown("### 📅 Monthly Case Distribution")
        st.bar_chart(df_monthly_cases.pivot(index="Month", columns="assignee_name", values="Case Count").fillna(0))

    if not df_monthly_checks.empty:
        st.markdown("### 📅 Monthly Check Distribution")
        st.bar_chart(df_monthly_checks.pivot(index="Month", columns="assignee_name", values="Check Count").fillna(0))

    # 📋 **Tables**
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 🏷️ Cases by Assignee and Status")
        st.dataframe(df_filtered.groupby(['assignee_name', 'cases_status'])['case_id'].nunique().unstack(fill_value=0))

    with col_right:
        st.markdown("### ✅ Checks by Assignee and Status")
        st.dataframe(df_filtered.groupby(['assignee_name', 'check_status_original'])['check_id'].nunique().unstack(fill_value=0))

    # 📂 **Filtered Dataset Table**
    st.markdown("### 📂 Filtered Dataset")
    st.dataframe(df_filtered)

    # 📥 **Download Data**
    st.download_button("📥 Download Filtered Data", df_filtered.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")


# 📜 **Instructions**
elif page == "Instructions":
    st.title("📖 Instructions")
    st.markdown("""
    ## How to Use the Case Dashboard
    
    This dashboard is designed to help you analyze and visualize data related to cases and checks. Below are step-by-step instructions for using its features effectively:

    ### 🎯 **1. Filters**
    Use the filters in the sidebar to refine the data displayed:
    - **Case Status**: Select one or multiple statuses (e.g., open, approved, rejected) to focus on specific cases.
    - **Assignee**: Filter data based on the individuals or teams assigned to the cases.
    - **Check Type**: Choose specific types of checks for detailed analysis.
    - **Check Status**: Filter checks based on their current status (e.g., pending, approved, rejected).
    - **Date Range**: Specify a start and end date to analyze cases and checks within a particular time period.
    - **Country**: Search and filter data by country to narrow down results geographically.
    - **Risk Level**: Focus on cases categorized as low, medium, or high risk.
    - **Politically Exposed Person (PEP)**: Filter cases involving PEPs by selecting:
      - `Yes`: Includes only cases involving PEPs.
      - `No`: Excludes cases involving PEPs.
      - `All`: Includes all cases.

    💡 **Tip**: Use the "Reset Filters" button to clear all selections and restore the default filter values.

    ### 📊 **2. Key Metrics**
    The dashboard displays important KPIs (Key Performance Indicators) to give you a quick summary of the data:
    - **Case Metrics**:
      - 🟡 `Open Cases`: Total number of cases that are currently open.
      - 🟢 `Approved Cases`: Number of cases that have been approved.
      - 🔴 `Rejected Cases`: Count of cases that were rejected.
      - ⚫ `Total Cases`: Total number of cases matching the current filters.
    - **Check Metrics**:
      - 🟡 `Pending Checks`: Number of checks in progress or awaiting review.
      - 🟢 `Approved Checks`: Total checks that have been approved.
      - 🔴 `Rejected Checks`: Total checks that were rejected.
      - ⚫ `Total Checks`: Total checks matching the applied filters.

    ### 📈 **3. Visualizations**
    The dashboard provides the following charts to help you analyze trends:
    - **Monthly Case Distribution**: A bar chart showing the number of cases per month, grouped by assignee.
    - **Monthly Check Distribution**: A similar bar chart displaying checks per month by assignee.

    Use these visualizations to:
    - Spot trends over time.
    - Identify periods of high or low activity.
    - Compare the performance of different assignees.

    ### 📋 **4. Detailed Tables**
    - **Cases by Assignee and Status**: A table showing the breakdown of cases by assignee and their current status.
    - **Checks by Assignee and Status**: A table displaying the breakdown of checks by assignee and their status.
    - **Filtered Dataset**: A complete table with all data matching the filters applied. This table allows you to:
      - View the raw data for detailed analysis.
      - Identify patterns and correlations.

    ### 📥 **5. Export Filtered Data**
    At the bottom of the dashboard, you’ll find an option to download the filtered dataset as a CSV file:
    - Click the "📥 Download Filtered Data" button to export the data.
    - Use this file for offline analysis or to share with your team.

    ### 🚀 **Best Practices**
    1. Start by applying broad filters to get an overview of the data.
    2. Gradually narrow down the filters to focus on specific cases, checks, or periods.
    3. Use KPIs and visualizations to identify trends and outliers.
    4. Download the filtered data for further analysis using tools like Excel or Python.

    ✨ **Explore your data, uncover insights, and make better decisions with this dashboard!** ✨
    """)

