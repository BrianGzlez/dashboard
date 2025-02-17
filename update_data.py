import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a la base de datos
def connect_to_db():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return engine

# Obtener los datos de PostgreSQL y guardarlos en Data.csv
def fetch_and_save_data():
    engine = connect_to_db()
    query = """ 
       WITH latest_ips AS (
    SELECT 
        ip_address,
        created_at,
        user_id,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
    FROM auth.user_login_ips
)
SELECT 
    auth.dotfile_cases.id AS Case_ID,
    q.individual_id AS individual_id,
    auth.dotfile_cases.status AS cases_status,
    q.type AS check_type,  
    q.id AS check_id,
    q.status AS check_status,    
    auth.dotfile_cases.tags AS entity_type,
    auth.dotfile_cases.assignee_fullname AS assignee_name,  
    auth.dotfile_cases.assignee_email AS assignee_email,
    auth.dotfile_cases.created_at AS created_at,
    auth.dotfile_cases.last_activity_at AS last_activity_cases,
    auth.dotfile_cases.risk_level AS risk_level,
    auth.dotfile_individuals.is_pep AS is_pep,
    auth.dotfile_individuals.employment_status AS employment_status,
    auth.dotfile_addresses.country AS country,
    latest_ips.ip_address,
    latest_ips.created_at AS created_at_ip_address
FROM auth.dotfile_cases
INNER JOIN auth.dotfile_individuals 
    ON auth.dotfile_cases.id = auth.dotfile_individuals.case_id
INNER JOIN auth.dotfile_checks q
    ON auth.dotfile_individuals.id = q.individual_id
INNER JOIN auth.dotfile_addresses 
    ON auth.dotfile_individuals.id = auth.dotfile_addresses.individual_id
INNER JOIN latest_ips
    ON auth.dotfile_cases.external_id = latest_ips.user_id
WHERE latest_ips.rn = 1;

    """
    df = pd.read_sql(query, engine)
    
    # Guardar en Data.csv
    df.to_csv("Data.csv", index=False)
    print("✅ Data actualizada y guardada en Data.csv")

# Ejecutar la función
if __name__ == "__main__":
    fetch_and_save_data()
