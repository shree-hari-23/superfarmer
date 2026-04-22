import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import execute_fluxbase_sql

def init_db():
    # users
    print("Creating users table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # farmer_profile
    print("Creating farmer_profile table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS farmer_profile (
        farmer_id SERIAL PRIMARY KEY,
        user_id INT,
        name VARCHAR(100),
        land_size FLOAT,
        location VARCHAR(100),
        water_availability VARCHAR(50),
        farming_goals TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    ''')

    # soil_records
    print("Creating soil_records table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS soil_records (
        record_id SERIAL PRIMARY KEY,
        farmer_id INT,
        soil_type VARCHAR(50),
        nitrogen FLOAT,
        phosphorus FLOAT,
        potassium FLOAT,
        soil_moisture FLOAT,
        temperature FLOAT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id)
    );
    ''')

    # crop_recommendations
    print("Creating crop_recommendations table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS crop_recommendations (
        recommendation_id SERIAL PRIMARY KEY,
        farmer_id INT,
        recommended_crops VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id)
    );
    ''')

    # crop_plans
    print("Creating crop_plans table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS crop_plans (
        plan_id SERIAL PRIMARY KEY,
        farmer_id INT,
        crop_name VARCHAR(100),
        sowing_schedule TEXT,
        irrigation_plan TEXT,
        fertilizer_schedule TEXT,
        pest_alerts TEXT,
        harvest_timeline TEXT,
        status VARCHAR(50) DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id)
    );
    ''')

    # nutrient_risk_log
    print("Creating nutrient_risk_log table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS nutrient_risk_log (
        log_id SERIAL PRIMARY KEY,
        farmer_id INT,
        plan_id INT,
        risk_probability FLOAT,
        risk_level VARCHAR(20),
        suggested_action TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id),
        FOREIGN KEY (plan_id) REFERENCES crop_plans(plan_id)
    );
    ''')
    
    # Reports
    print("Creating reports table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS reports (
        report_id SERIAL PRIMARY KEY,
        farmer_id INT,
        report_text TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id)
    );
    ''')

    # Session Logs
    print("Creating session_logs table...")
    execute_fluxbase_sql('''
    CREATE TABLE IF NOT EXISTS session_logs (
        session_id SERIAL PRIMARY KEY,
        farmer_id INT,
        interaction_log TEXT,
        session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmer_profile(farmer_id)
    );
    ''')

    print("Fluxbase database initialized successfully.")

if __name__ == '__main__':
    init_db()
