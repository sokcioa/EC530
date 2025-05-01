import sqlite3
import os

def run_migration():
    """Add new columns for complementary errand requirements"""
    try:
        # Connect to the database
        conn = sqlite3.connect('errands.db')
        cursor = conn.cursor()
        
        # Add new columns
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN same_day_required BOOLEAN DEFAULT FALSE
        ''')
        
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN order_required BOOLEAN DEFAULT FALSE
        ''')
        
        cursor.execute('''
            ALTER TABLE errands
            ADD COLUMN same_location_required BOOLEAN DEFAULT FALSE
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