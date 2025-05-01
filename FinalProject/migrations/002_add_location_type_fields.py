import sqlite3
import os

def run_migration():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'errands.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add new columns to errands table
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN is_remote BOOLEAN DEFAULT FALSE
        ''')
        
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN use_exact_location BOOLEAN DEFAULT TRUE
        ''')
        
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN alternative_locations TEXT
        ''')
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Columns already exist, skipping migration")
        else:
            print(f"Error during migration: {str(e)}")
            conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration() 