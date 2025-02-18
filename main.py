import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import altair as alt
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
page = st.sidebar.radio("Go to", ["Dashboard", "KYC Process Dashboard", "Advanced Stats"])

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
elif page == "Advanced Stats":
    st.title(":bar_chart: Advanced Stats - Agent Tracking")
    st.markdown("### Select an agent to view advanced statistics and compare with Horatio team averages")
    
    # Agent selection
    agent_list = sorted(df['assignee_name'].dropna().unique())
    selected_agent = st.selectbox("Select an agent", agent_list)
    df_agent = df[df['assignee_name'] == selected_agent].copy()
    
    # Ensure 'created_at' is in datetime format
    if 'created_at' in df_agent.columns:
        df_agent['created_at'] = pd.to_datetime(df_agent['created_at'], errors='coerce')
        df_agent['Month'] = df_agent['created_at'].dt.to_period('M').astype(str)
    else:
        st.error("Missing 'created_at' column for agent data.")
        st.stop()
    
    # General Metrics for the selected agent
    total_cases = df_agent['case_id'].nunique()
    approved_cases = df_agent[df_agent['cases_status'] == 'approved']['case_id'].nunique()
    rejected_cases = df_agent[df_agent['cases_status'] == 'rejected']['case_id'].nunique()
    open_cases = df_agent[df_agent['cases_status'] == 'open']['case_id'].nunique()
    
    st.subheader("General Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", total_cases)
    col2.metric("Approved Cases", approved_cases)
    col3.metric("Rejected Cases", rejected_cases)
    col4.metric("Open Cases", open_cases)
    
    if (approved_cases + rejected_cases) > 0:
        agent_win_ratio = round(approved_cases / (approved_cases + rejected_cases) * 100, 2)
        st.write(f"**Approval Rate (Agent):** {agent_win_ratio}%")
    else:
        st.write("Not enough data to calculate the agent's approval rate.")
    
    # Horatio team data
    df_horatio = df[df['assignee_email'].str.endswith("@hirehoratio.co", na=False)].copy()
    horatio_approved = df_horatio[df_horatio['cases_status'] == 'approved']['case_id'].nunique()
    horatio_rejected = df_horatio[df_horatio['cases_status'] == 'rejected']['case_id'].nunique()
    
    if (horatio_approved + horatio_rejected) > 0:
        horatio_win_ratio = round(horatio_approved / (horatio_approved + horatio_rejected) * 100, 2)
        st.write(f"**Approval Rate (Horatio Team):** {horatio_win_ratio}%")
    else:
        st.write("Not enough data to calculate the Horatio team's approval rate.")
    
    st.markdown("---")
    
    # Helper functions for approval rate trends
    def compute_approved_rate_trend_cases(data):
        """Compute monthly approval rate trend for cases."""
        if 'updated_at_cases' in data.columns:
            data['Month_Cases'] = pd.to_datetime(data['updated_at_cases'], errors='coerce').dt.to_period('M').astype(str)
        else:
            data['Month_Cases'] = data['created_at'].dt.to_period('M').astype(str)
        trend = data.groupby('Month_Cases').agg(
            approved_cases=('cases_status', lambda x: (x == 'approved').sum()),
            total_cases=('case_id', 'nunique')
        ).reset_index()
        trend['approved_rate'] = trend['approved_cases'] / trend['total_cases']
        return trend
    
    def compute_approved_rate_trend_checks(data):
        """Compute monthly approval rate trend for checks."""
        if 'updated_at_checks' in data.columns:
            data['Month_Checks'] = pd.to_datetime(data['updated_at_checks'], errors='coerce').dt.to_period('M').astype(str)
        else:
            data['Month_Checks'] = data['created_at'].dt.to_period('M').astype(str)
        trend = data.groupby('Month_Checks').agg(
            approved_checks=('check_status', lambda x: (x == 'approved').sum()),
            total_checks=('check_id', 'nunique')
        ).reset_index()
        trend['approved_rate'] = trend['approved_checks'] / trend['total_checks']
        return trend
    
    # Approval rate trend for cases
    agent_cases_trend = compute_approved_rate_trend_cases(df_agent)
    horatio_cases_trend = compute_approved_rate_trend_cases(df_horatio)
    agent_cases_trend['Group'] = 'Selected Agent'
    horatio_cases_trend['Group'] = 'Horatio Team'
    combined_cases_trend = pd.concat([agent_cases_trend, horatio_cases_trend], ignore_index=True)
    
    st.subheader("Monthly Approval Rate Trend (Cases)")
    if not combined_cases_trend.empty:
        chart_cases = alt.Chart(combined_cases_trend).mark_line(point=True).encode(
            x=alt.X('Month_Cases:N', title='Month'),
            y=alt.Y('approved_rate:Q', title='Approval Rate', axis=alt.Axis(format='%')),
            color=alt.Color('Group:N', scale=alt.Scale(domain=['Selected Agent', 'Horatio Team'],
                                                        range=['#1f77b4', '#ff7f0e'])),
            tooltip=['Month_Cases', alt.Tooltip('approved_rate:Q', format='.2%')]
        ).properties(width=700, height=300, title="Monthly Approval Rate Trend (Cases)")
        st.altair_chart(chart_cases, use_container_width=True)
    else:
        st.info("No data available for case approval trend.")
    
    st.markdown("---")
    
    # Approval rate trend for checks
    agent_checks_trend = compute_approved_rate_trend_checks(df_agent)
    horatio_checks_trend = compute_approved_rate_trend_checks(df_horatio)
    agent_checks_trend['Group'] = 'Selected Agent'
    horatio_checks_trend['Group'] = 'Horatio Team'
    combined_checks_trend = pd.concat([agent_checks_trend, horatio_checks_trend], ignore_index=True)
    
    st.subheader("Monthly Approval Rate Trend (Checks)")
    if not combined_checks_trend.empty:
        chart_checks = alt.Chart(combined_checks_trend).mark_line(point=True).encode(
            x=alt.X('Month_Checks:N', title='Month'),
            y=alt.Y('approved_rate:Q', title='Approval Rate', axis=alt.Axis(format='%')),
            color=alt.Color('Group:N', scale=alt.Scale(domain=['Selected Agent', 'Horatio Team'],
                                                        range=['#1f77b4', '#ff7f0e'])),
            tooltip=['Month_Checks', alt.Tooltip('approved_rate:Q', format='.2%')]
        ).properties(width=700, height=300, title="Monthly Approval Rate Trend (Checks)")
        st.altair_chart(chart_checks, use_container_width=True)
    else:
        st.info("No data available for check approval trend.")
    
    st.markdown("---")
    
    # Resolution Time Analysis
    st.subheader("Resolution Time Analysis")
    if 'last_activity_cases' in df_agent.columns:
        df_agent['last_activity_cases'] = pd.to_datetime(df_agent['last_activity_cases'], errors='coerce')
        df_agent['resolution_time'] = (df_agent['last_activity_cases'] - df_agent['created_at']).dt.days
    else:
        st.error("Missing 'last_activity_cases' column for resolution time analysis.")
    
    df_agent_closed = df_agent[df_agent['cases_status'].isin(['approved', 'rejected'])].copy()
    if not df_agent_closed.empty:
        agent_resolution_trend = df_agent_closed.groupby('Month').agg(avg_resolution=('resolution_time', 'mean')).reset_index()
    else:
        agent_resolution_trend = pd.DataFrame()
    
    if 'last_activity_cases' in df_horatio.columns:
        df_horatio['last_activity_cases'] = pd.to_datetime(df_horatio['last_activity_cases'], errors='coerce')
        df_horatio['resolution_time'] = (df_horatio['last_activity_cases'] - pd.to_datetime(df_horatio['created_at'], errors='coerce')).dt.days
    else:
        st.error("Missing 'last_activity_cases' column for Horatio team resolution time analysis.")
    
    df_horatio_closed = df_horatio[df_horatio['cases_status'].isin(['approved', 'rejected'])].copy()
    if not df_horatio_closed.empty:
        horatio_resolution_trend = df_horatio_closed.groupby(
            df_horatio_closed['created_at'].dt.to_period('M').astype(str)
        ).agg(avg_resolution=('resolution_time', 'mean')).reset_index().rename(columns={'created_at': 'Month'})
    else:
        horatio_resolution_trend = pd.DataFrame()
    
    if not agent_resolution_trend.empty and not horatio_resolution_trend.empty:
        agent_resolution_trend['Group'] = 'Selected Agent'
        horatio_resolution_trend['Group'] = 'Horatio Team'
        combined_resolution_trend = pd.concat([agent_resolution_trend, horatio_resolution_trend], ignore_index=True)
        chart_resolution = alt.Chart(combined_resolution_trend).mark_line(point=True).encode(
            x=alt.X('Month:N', title='Month'),
            y=alt.Y('avg_resolution:Q', title='Average Resolution Time (days)'),
            color=alt.Color('Group:N', scale=alt.Scale(domain=['Selected Agent', 'Horatio Team'],
                                                        range=['#1f77b4', '#ff7f0e'])),
            tooltip=['Month', alt.Tooltip('avg_resolution:Q', format=".2f")]
        ).properties(width=700, height=300, title="Monthly Average Resolution Time")
        st.altair_chart(chart_resolution, use_container_width=True)
    else:
        st.info("Not enough data to analyze resolution time trends.")
    
    st.markdown("---")
    
    # Resolution Time Distribution (Box Plot)
    st.subheader("Resolution Time Distribution")
    if not df_agent_closed.empty and not df_horatio_closed.empty:
        agent_box = df_agent_closed[['resolution_time']].copy()
        agent_box['Group'] = 'Selected Agent'
        horatio_box = df_horatio_closed[['resolution_time']].copy()
        horatio_box['Group'] = 'Horatio Team'
        combined_box = pd.concat([agent_box, horatio_box], ignore_index=True)
        boxplot = alt.Chart(combined_box).mark_boxplot().encode(
            x=alt.X('Group:N', title='Group'),
            y=alt.Y('resolution_time:Q', title='Resolution Time (days)'),
            tooltip=[alt.Tooltip('resolution_time:Q', title='Days')]
        ).properties(width=700, height=300, title="Distribution of Resolution Time")
        st.altair_chart(boxplot, use_container_width=True)
    else:
        st.info("Not enough data to analyze resolution time distribution.")
    
    st.markdown("---")
    
    # Open Cases Aging Analysis
    st.subheader("Open Cases Aging Analysis")
    today = pd.to_datetime(date.today())
    # Remove duplicate cases based on 'case_id' before analysis
    df_open = df_agent[df_agent['cases_status'] == 'open'].drop_duplicates(subset=['case_id']).copy()
    if not df_open.empty:
        df_open['days_open'] = (today - df_open['created_at']).dt.days
        st.markdown("**Summary of Open Cases Aging (in days):**")
        st.write(df_open['days_open'].describe().reset_index())
        aging_chart = alt.Chart(df_open).mark_bar().encode(
            x=alt.X('days_open:Q', bin=alt.Bin(step=10), title='Days Open'),
            y=alt.Y('count()', title='Number of Cases'),
            tooltip=[alt.Tooltip('count()', title='Count'),
                     alt.Tooltip('days_open:Q', title='Days Open')]
        ).properties(width=700, height=300, title="Distribution of Open Cases Aging")
        st.altair_chart(aging_chart, use_container_width=True)
        oldest_cases = df_open.sort_values(by='days_open', ascending=False).head(10)
        st.markdown("**Top 10 Oldest Open Cases:**")
        st.dataframe(oldest_cases[['case_id', 'created_at', 'days_open']])
    else:
        st.info("No open cases available for aging analysis.")
    
    st.markdown("---")
    r
    # Additional Advanced Analytics Suggestions
    st.subheader("Additional Advanced Analytics")
    st.markdown("""
    **Question:** Given that duplicate cases (with the same `case_id`) are excluded from the aging analysis of open cases, what other advanced analytics would you be interested in seeing?
    
    Some suggestions include:
    - **Predictive Analytics:** Forecasting case resolution times using historical trends.
    - **Cohort Analysis:** Grouping cases by creation month or other attributes to analyze performance over time.
    - **Funnel Analysis:** Tracking the conversion process from open to approved or rejected.
    - **Agent Efficiency Metrics:** Comparing agents based on resolution times, workload, and success rates.
    - **Outlier Detection:** Identifying cases with unusually high resolution times or abnormal patterns.
    - **Geographical Analysis:** If location data is available, analyzing cases by region or country.
    """)
    
    st.markdown("---")
    st.subheader("Selected Agent Data")
    st.dataframe(df_agent)

elif page == "KYC Process Dashboard":
    st.title("📊 KYC Process Dashboard")
    
    # 📌 **Sidebar - Filtros**
    st.sidebar.header("🔍 Filters")

    # Filtro de rango de fechas predefinido
    date_filter = st.sidebar.selectbox("📅 Select Date Range", 
                                       ["Historical Data", "Last 15 Days", "Last Month"])

    # Obtener la fecha actual
    today = datetime.today()

    # Filtrar datos según la opción seleccionada
    filtered_data = df.copy()
    if date_filter == "Last 15 Days":
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

    total_kyc_cases = filtered_data['case_id'].nunique()
    completed_kyc_cases = filtered_data[filtered_data['cases_status'] == 'open']['case_id'].nunique()
    aml_alerts = filtered_data[(filtered_data['check_type'] == 'aml') & (filtered_data['check_status'] == 'need_review') & 
                               (filtered_data['cases_status'].isin(['open', 'approved']))]['check_id'].nunique()
    idv_alerts = filtered_data[(filtered_data['check_type'] == 'id_verification') & (filtered_data['check_status'] == 'need_review') & 
                               (filtered_data['cases_status'] == 'open')]['check_id'].nunique()
    
    individual_types = {"POA Lookback (1.14.2025)", "Individual", "True Match - PEP", "Employee", "VIP_Customer"}
    document_alerts = filtered_data[(filtered_data['check_type'].isin(['id_document', 'document'])) & 
                                    (filtered_data['check_status'] == 'need_review') & 
                                    (filtered_data['cases_status'] == 'open') & 
                                    (filtered_data['entity_type'].apply(lambda x: any(ind in x for ind in individual_types)))]['check_id'].nunique()
    document_alerts_companies = filtered_data[(filtered_data['check_type'] == 'document') & 
                                              (filtered_data['check_status'] == 'need_review') & 
                                              (filtered_data['cases_status'] == 'open') & 
                                              (filtered_data['entity_type'] == 'business')]['check_id'].nunique()


    
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    col1.metric("🆔 Total Number of Users Starting KYC", total_kyc_cases)
    col2.metric("📄 Total Number of Completed KYC and in Review", completed_kyc_cases)
    col3.metric("🚨 Total Number of AML Alerts in Review", aml_alerts)
    col4.metric("🛂 Total Number of IDV Alerts in Review", idv_alerts)
    col5.metric("📑 Total Number of Document Alerts (Individuals) in Review", document_alerts)
    col6.metric("🏢 Total Number of Document Alerts (Companies) in Review", document_alerts_companies)

    # 📋 **Datos Filtrados**
    st.markdown("### 📋 Filtered Data")
    st.dataframe(filtered_data)

    # 📥 **Descargar datos filtrados**
    st.download_button("📥 Download Filtered Data", filtered_data.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")


