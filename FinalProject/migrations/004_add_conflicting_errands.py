import sqlite3
import os

def run_migration():
    """Add new columns for conflicting errands"""
    try:
        # Connect to the database
        conn = sqlite3.connect('errands.db')
        cursor = conn.cursor()
        
        # Add new columns
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN conflicting_errands TEXT
        ''')
        
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN conflict_type TEXT
        ''')
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Columns already exist, skipping migration")
        else:
            print(f"Error during migration: {str(e)}")
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration() 