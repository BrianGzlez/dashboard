import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz

# Configuración de la página
st.set_page_config(page_title="Dashboard", layout="wide")

# 📌 **Función para obtener la última actualización del archivo**
def get_last_update_time(file_path):
    if os.path.exists(file_path):
        last_modified_time = os.path.getmtime(file_path)
        utc_dt = datetime.fromtimestamp(last_modified_time, pytz.utc)  # Convertir a UTC
        rd_tz = pytz.timezone('America/Santo_Domingo')  # Zona horaria UTC-4
        local_dt = utc_dt.astimezone(rd_tz)  # Convertir a UTC-4
        return local_dt.strftime('%Y-%m-%d %H:%M:%S UTC-4')
    else:
        return "File not found"

# Obtener última actualización
last_update = get_last_update_time('data.csv')

# 📌 **Función para cargar datos con cache**
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    df.columns = df.columns.str.strip().str.lower()  # Normalizar nombres de columnas
    
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
    else:
        st.error("⚠️ The dataset is missing the 'created_at' column for filtering by date.")
    
    return df

# Cargar datos
data = load_data()

# 📌 **Menú de navegación**
page = st.sidebar.radio("📍 Select Dashboard", ["KYC Process Dashboard", "Case Dashboard"])

# ==========================
# 📊 **KYC Process Dashboard**
# ==========================
if page == "KYC Process Dashboard":
    st.title("📊 KYC Process Dashboard")
    
    # 📌 **Sidebar - Filtros**
    st.sidebar.header("🔍 Filters")

    # Filtro de rango de fechas predefinido
    date_filter = st.sidebar.selectbox("📅 Select Date Range", 
                                       ["Historical Data", "Last Day", "Last Week", "Last 15 Days", "Last Month"])

    # Obtener la fecha actual
    today = datetime.today()

    # Filtrar datos según la opción seleccionada
    filtered_data = data.copy()
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


# ==========================
# 📊 **Case Dashboard**
# ==========================
elif page == "Case Dashboard":
    st.title("📊 Case Dashboard")
    
    # 📌 **Última actualización**
    st.info(f"🕒 **Last Updated:** {last_update}")

    # Filtros básicos
    case_status_filter = st.sidebar.multiselect("📂 Filter by Case Status", data["cases_status"].unique(), default=data["cases_status"].unique())
    assignee_filter = st.sidebar.multiselect("👨‍💼 Filter by Assignee", data["assignee_name"].unique(), default=data["assignee_name"].unique())
    
    # Aplicar filtros
    df_filtered = data[
        data['cases_status'].isin(case_status_filter) & 
        data['assignee_name'].isin(assignee_filter)
    ]

    # 📊 **KPIs**
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟡 Open Cases", df_filtered[df_filtered['cases_status'] == 'open']['case_id'].nunique())
    col2.metric("🟢 Approved Cases", df_filtered[df_filtered['cases_status'] == 'approved']['case_id'].nunique())
    col3.metric("🔴 Rejected Cases", df_filtered[df_filtered['cases_status'] == 'rejected']['case_id'].nunique())
    col4.metric("⚫ Total Cases", df_filtered['case_id'].nunique())

    # 📋 **Datos Filtrados**
    st.markdown("### 📋 Filtered Cases Data")
    st.dataframe(df_filtered)

    # 📥 **Descargar datos filtrados**
    st.download_button("📥 Download Filtered Data", df_filtered.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")
