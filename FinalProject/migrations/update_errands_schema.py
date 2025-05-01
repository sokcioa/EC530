from sqlalchemy import create_engine, text, inspect
import os
from datetime import datetime

def column_exists(conn, table_name, column_name):
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def run_migration():
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'errands.db')
    
    # Create engine
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Get a connection
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            # List of columns to add with their definitions (without non-constant defaults)
            columns_to_add = [
                ('location_type', 'TEXT'),
                ('location_address', 'TEXT'),
                ('is_remote', 'BOOLEAN'),
                ('use_exact_location', 'BOOLEAN'),
                ('alternative_locations', 'TEXT'),
                ('access_type', 'TEXT'),
                ('repetition_period', 'TEXT'),
                ('valid_days_week1', 'TEXT'),
                ('valid_days_week2', 'TEXT'),
                ('starting_monday', 'DATE'),
                ('flexible_start_window', 'BOOLEAN'),
                ('flexible_end_window', 'BOOLEAN'),
                ('flexible_duration', 'BOOLEAN'),
                ('min_duration', 'INTEGER'),
                ('max_duration', 'INTEGER'),
                ('complementary_errands', 'TEXT'),
                ('same_day_required', 'BOOLEAN'),
                ('order_required', 'BOOLEAN'),
                ('same_location_required', 'BOOLEAN'),
                ('conflicting_errands', 'TEXT'),
                ('conflict_type', 'TEXT'),
                ('created_at', 'DATETIME'),
                ('updated_at', 'DATETIME')
            ]
            
            # Add new columns if they don't exist
            for column_name, column_type in columns_to_add:
                if not column_exists(conn, 'errands', column_name):
                    conn.execute(text(f'ALTER TABLE errands ADD COLUMN {column_name} {column_type}'))
                    print(f"Added column: {column_name}")
            
            # Handle column renames
            rename_mappings = [
                ('days_of_week', 'valid_days'),
                ('frequency_per_week', 'frequency'),
                ('location_latitude', 'latitude'),
                ('location_longitude', 'longitude')
            ]
            
            for old_name, new_name in rename_mappings:
                if column_exists(conn, 'errands', old_name) and not column_exists(conn, 'errands', new_name):
                    conn.execute(text(f'ALTER TABLE errands RENAME COLUMN {old_name} TO {new_name}'))
                    print(f"Renamed column: {old_name} -> {new_name}")
            
            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update existing data with default values
            conn.execute(text(f"""
                UPDATE errands 
                SET location_type = 'name',
                    use_exact_location = 1,
                    access_type = 'drive',
                    repetition = 'none',
                    created_at = '{current_time}',
                    updated_at = '{current_time}'
                WHERE location_type IS NULL;
            """))
            
            # Ensure user table has all required columns
            user_columns_to_add = [
                ('home_address', 'TEXT'),
                ('home_latitude', 'FLOAT'),
                ('home_longitude', 'FLOAT')
            ]
            
            for column_name, column_type in user_columns_to_add:
                if not column_exists(conn, 'users', column_name):
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}'))
                    print(f"Added column to users table: {column_name}")
            
            print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration() 