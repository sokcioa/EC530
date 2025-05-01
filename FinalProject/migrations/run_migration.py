import sqlite3
import os

def run_migration():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'errands.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add new columns to errands table
        cursor.execute("""
            ALTER TABLE errands 
            ADD COLUMN flexible_start_window BOOLEAN DEFAULT FALSE
        """)
        cursor.execute("""
            ALTER TABLE errands 
            ADD COLUMN flexible_end_window BOOLEAN DEFAULT FALSE
        """)
        cursor.execute("""
            ALTER TABLE errands 
            ADD COLUMN flexible_duration BOOLEAN DEFAULT FALSE
        """)
        cursor.execute("""
            ALTER TABLE errands 
            ADD COLUMN min_duration INTEGER
        """)
        cursor.execute("""
            ALTER TABLE errands 
            ADD COLUMN max_duration INTEGER
        """)
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Columns already exist. Migration not needed.")
        else:
            print(f"Error during migration: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration() 