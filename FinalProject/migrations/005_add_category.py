import sqlite3
import os

def run_migration():
    """Add category field to errands table"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'errands.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add category column
        cursor.execute('ALTER TABLE errands ADD COLUMN category TEXT')
        conn.commit()
        print("Successfully added category column to errands table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Category column already exists")
        else:
            print(f"Error adding category column: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration() 