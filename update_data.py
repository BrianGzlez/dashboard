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
     SELECT 
            auth.dotfile_cases.id as Case_ID,
            q.individual_id as individual_id,
            auth.dotfile_cases.status as cases_status,
            q.type as check_type,  
            q.id as check_id,
            q.status as check_status,    
            auth.dotfile_cases.tags as entity_type,
            auth.dotfile_cases.assignee_fullname as assignee_name,  
            auth.dotfile_cases.assignee_email as assignee_email,
            auth.dotfile_cases.created_at as created_at,
            auth.dotfile_cases.last_activity_at as last_activity_cases,
            auth.dotfile_cases.risk_level as risk_level,
            auth.dotfile_individuals.is_pep as is_pep,
            auth.dotfile_individuals.employment_status as employment_status,
            auth.dotfile_addresses.country as country
        FROM auth.dotfile_cases
        INNER JOIN auth.dotfile_individuals 
            ON auth.dotfile_cases.id = auth.dotfile_individuals.case_id
        INNER JOIN auth.dotfile_checks q
            ON auth.dotfile_individuals.id = q.individual_id
        INNER JOIN auth.dotfile_addresses 
            ON auth.dotfile_individuals.id = auth.dotfile_addresses.individual_id;
    """
    df = pd.read_sql(query, engine)
    
    # Guardar en Data.csv
    df.to_csv("Data.csv", index=False)
    print("✅ Data actualizada y guardada en Data.csv")

# Ejecutar la función
if __name__ == "__main__":
    fetch_and_save_data()
