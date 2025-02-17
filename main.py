import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

# Obtener la fecha y hora de la última actualización del archivo
def get_last_update_time(file_path):
    if os.path.exists(file_path):
        last_modified_time = os.path.getmtime(file_path)
        utc_dt = datetime.fromtimestamp(last_modified_time, pytz.utc)  # Convertir a UTC
        rd_tz = pytz.timezone('America/Santo_Domingo')  # Zona horaria UTC-4
        local_dt = utc_dt.astimezone(rd_tz)  # Convertir a UTC-4
        return local_dt.strftime('%Y-%m-%d %H:%M:%S UTC-4')
    else:
        return "File not found"

# Calcular la última actualización
last_update = get_last_update_time('Data.csv')

# Configure Streamlit page
st.set_page_config(page_title="Case Dashboard", layout="wide")

# Load data using cache
@st.cache_data
def load_data():
    df = pd.read_csv('Data.csv', skip_blank_lines=True)
    print(df.info())  # Verifica si realmente tiene datos
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    return df

# Navigation button
page = st.sidebar.radio("Go to", ["Dashboard", "KYC Process Dashboard", "Instructions"])

# Load dataset
df = load_data()

# Verify essential columns
if 'created_at' in df.columns:
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
else:
    st.error(":warning: The column 'created_at' is missing in the dataset.")
    
if 'last_activity_cases' in df.columns:
    df['last_activity_cases'] = pd.to_datetime(df['last_activity_cases'], errors='coerce').dt.tz_localize(None)
else:
    st.error(":warning: The column 'last_activity_cases' is missing in the dataset.")

if 'assignee_name' in df.columns:
    df['assignee_name'] = df['assignee_name'].fillna('Un-assignee')
else:
    st.error(":warning: The column 'assignee_name' is missing in the dataset.")
    
if 'check_status' in df.columns:
    df['check_status_original'] = df['check_status']
    df['check_status_kpi'] = df['check_status'].replace(['in_progress', 'processing', 'need_review'], 'pending')
else:
    st.error(":warning: The column 'check_status' is missing in the dataset.")

# :bar_chart: **Dashboard**
if page == "Dashboard":
    st.title(":bar_chart: Case Dashboard")
    st.markdown("### :pushpin: Overview of Cases and Checks")
    
    # :pushpin: **Sidebar - Filters**
    with st.sidebar.expander(":dart: Case Filters", expanded=False):
        case_status_filter = st.multiselect("Filter by Case Status", df['cases_status'].unique(), default=df['cases_status'].unique())
        assignee_filter = st.multiselect("Filter by Assignee", df['assignee_name'].unique(), default=df['assignee_name'].unique())
    
    with st.sidebar.expander(":hammer_and_wrench: Check Filters", expanded=False):
        check_status_filter = st.multiselect("Filter by Check Status", df['check_status_original'].unique(), default=df['check_status_original'].unique())
        check_type_filter = st.multiselect("Filter by Check Type", df['check_type'].unique(), default=df['check_type'].unique())
    
    with st.sidebar.expander(":earth_africa: Additional Filters", expanded=False):
        # Filter for Date Selection
        date_filter_choice = st.radio(
            "Choose the date filter",
            ("Created At", "Last Activity Cases"),
            help="Select the date field you wish to filter by."
        )
        
        # Filter dates based on choice
        if date_filter_choice == "Created At":
            start_date = st.date_input(":date: Start Date", df['created_at'].min())
            end_date = st.date_input(":date: End Date", df['created_at'].max())
        else:
            start_date = st.date_input(":date: Start Date", df['last_activity_cases'].min())
            end_date = st.date_input(":date: End Date", df['last_activity_cases'].max())
        
        start_date = pd.to_datetime(start_date).normalize()
        end_date = pd.to_datetime(end_date).normalize()

        # Additional filters for Country, PEP, Risk Level, etc.
        if 'country' in df.columns:
            country_list = df['country'].dropna().unique()
            selected_country = st.text_input(":mag: Search Country", "").strip()
            country_filter = [c for c in country_list if selected_country.lower() in c.lower()] if selected_country else country_list
        else:
            st.warning(":warning: The column 'country' is missing in the dataset.")
            country_filter = []
        
        pep_filter = st.selectbox(":shield: Filter by PEP", ["All", "Yes", "No"])
        if 'risk_level' in df.columns:
            risk_level_filter = st.multiselect(":warning: Filter by Risk Level", df['risk_level'].dropna().unique(), default=df['risk_level'].dropna().unique())
        else:
            st.warning(":warning: The column 'risk_level' is missing in the dataset.")
            risk_level_filter = []

    # Apply filters based on the selected date choice
    if date_filter_choice == "Created At":
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
    else:
        df_filtered = df[
            df['cases_status'].isin(case_status_filter) &
            df['check_status_original'].isin(check_status_filter) &
            df['assignee_name'].isin(assignee_filter) &
            df['check_type'].isin(check_type_filter) &
            df['country'].isin(country_filter) &
            df['risk_level'].isin(risk_level_filter) &
            (df['last_activity_cases'] >= start_date) &
            (df['last_activity_cases'] <= end_date)
        ]

    if pep_filter == "Yes":
        df_filtered = df_filtered[df_filtered['is_pep'] == True]
    elif pep_filter == "No":
        df_filtered = df_filtered[df_filtered['is_pep'] == False]
    
    # :bar_chart: **Case KPIs**
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label=":large_yellow_circle: Open Cases", value=df_filtered[df_filtered['cases_status'] == 'open']['case_id'].nunique())
    with col2:
        st.metric(label=":large_green_circle: Approved Cases", value=df_filtered[df_filtered['cases_status'] == 'approved']['case_id'].nunique())
    with col3:
        st.metric(label=":red_circle: Rejected Cases", value=df_filtered[df_filtered['cases_status'] == 'rejected']['case_id'].nunique())
    with col4:
        st.metric(label=":black_circle: Total Cases", value=df_filtered['case_id'].nunique())
    
    # :bar_chart: **Check KPIs**
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label=":large_yellow_circle: Pending Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'pending']['check_id'].nunique())
    with col6:
        st.metric(label=":large_green_circle: Approved Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'approved']['check_id'].nunique())
    with col7:
        st.metric(label=":red_circle: Rejected Checks", value=df_filtered[df_filtered['check_status_kpi'] == 'rejected']['check_id'].nunique())
    with col8:
        st.metric(label=":black_circle: Total Checks", value=df_filtered['check_id'].nunique())
    
    # :bar_chart: **Charts**
    df_filtered['Month'] = df_filtered[date_filter_choice.lower().replace(" ", "_")].dt.to_period('M').astype(str)
    df_monthly_cases = df_filtered.groupby(['Month', 'assignee_name'])['case_id'].nunique().reset_index(name='Case Count')
    df_monthly_checks = df_filtered.groupby(['Month', 'assignee_name'])['check_id'].nunique().reset_index(name='Check Count')
    
    if not df_monthly_cases.empty:
        st.markdown("### :date: Monthly Case Distribution")
        st.bar_chart(df_monthly_cases.pivot(index="Month", columns="assignee_name", values="Case Count").fillna(0))
    
    if not df_monthly_checks.empty:
        st.markdown("### :date: Monthly Check Distribution")
        st.bar_chart(df_monthly_checks.pivot(index="Month", columns="assignee_name", values="Check Count").fillna(0))

    # :clipboard: **Tables**
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### :label: Cases by Assignee and Status")
        st.dataframe(df_filtered.groupby(['assignee_name', 'cases_status'])['case_id'].nunique().unstack(fill_value=0))
    with col_right:
        st.markdown("### :white_check_mark: Checks by Assignee and Status")
        st.dataframe(df_filtered.groupby(['assignee_name', 'check_status_original'])['check_id'].nunique().unstack(fill_value=0))
    
    # :open_file_folder: **Filtered Dataset Table**
    st.markdown("### :open_file_folder: Filtered Dataset")
    st.dataframe(df_filtered)

    # :inbox_tray: **Download Data**
    st.download_button(":inbox_tray: Download Filtered Data", df_filtered.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")
    st.markdown("---")
    st.info(f":date: **Last Updated:** {last_update}")

# :scroll: **Instructions**
elif page == "Instructions":
    st.title(":book: Instructions")
    st.markdown("""
    ## How to Use the Case Dashboard
    ...
    """)

elif page == "KYC Process Dashboard":
    st.title("📊 KYC Process Dashboard")
    
    # 📌 **Sidebar - Filtros**
    st.sidebar.header("🔍 Filters")

    # Filtro de rango de fechas predefinido
    date_filter = st.sidebar.selectbox("📅 Select Date Range", 
                                       ["Historical Data", "Last Day", "Last Week", "Last 15 Days", "Last Month"])

    # Obtener la fecha actual
    today = datetime.today()

    # Filtrar datos según la opción seleccionada
    filtered_data = df.copy()
    if date_filter == "Last Day":
        filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=1)]
    elif date_filter == "Last Week":
        filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(weeks=1)]
    elif date_filter == "Last 15 Days":
        filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=15)]
    elif date_filter == "Last Month":
        filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=30)]

    # Dropdowns para filtros adicionales
    case_status_filter = st.sidebar.selectbox("📂 Case Status", ["All"] + list(filtered_data["cases_status"].dropna().unique()))
    check_type_filter = st.sidebar.selectbox("✅ Check Type", ["All"] + list(filtered_data["check_type"].dropna().unique()))
    risk_level_filter = st.sidebar.selectbox("⚠️ Risk Level", ["All"] + list(filtered_data["risk_level"].dropna().unique()))
    country_filter = st.sidebar.selectbox("🌍 Country", ["All"] + list(filtered_data["country"].dropna().unique()))

    # Aplicar filtros solo si no es "All"
    if case_status_filter != "All":
        filtered_data = filtered_data[filtered_data["cases_status"] == case_status_filter]
    if check_type_filter != "All":
        filtered_data = filtered_data[filtered_data["check_type"] == check_type_filter]
    if risk_level_filter != "All":
        filtered_data = filtered_data[filtered_data["risk_level"] == risk_level_filter]
    if country_filter != "All":
        filtered_data = filtered_data[filtered_data["country"] == country_filter]

    # 📊 **KPIs**
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.metric("🆔 Users Starting KYC", filtered_data['case_id'].nunique())
    col2.metric("📄 Completed KYC (In Review)", filtered_data[filtered_data['cases_status'] == 'open']['case_id'].nunique())
    col3.metric("🚨 AML Alerts", filtered_data[(filtered_data['check_type'] == 'aml') & (filtered_data['check_status'] == 'need_review')]['check_id'].nunique())
    col4.metric("🛂 IDV Alerts", filtered_data[(filtered_data['check_type'] == 'id_verification') & (filtered_data['check_status'] == 'need_review')]['check_id'].nunique())
    col5.metric("📑 Document Alerts (Individuals)", filtered_data[(filtered_data['check_type'].isin(['id_document', 'document'])) & (filtered_data['check_status'] == 'need_review')]['check_id'].nunique())
    col6.metric("🏢 Document Alerts (Companies)", filtered_data[(filtered_data['check_type'] == 'document') & (filtered_data['check_status'] == 'need_review')]['check_id'].nunique())

    # 📋 **Datos Filtrados**
    st.markdown("### 📋 Filtered Data")
    st.dataframe(filtered_data)

    # 📥 **Descargar datos filtrados**
    st.download_button("📥 Download Filtered Data", filtered_data.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")


