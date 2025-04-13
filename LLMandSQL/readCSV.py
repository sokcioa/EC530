import pandas as pd
import sqlite3
import os
import datetime

def log_error(message):
    """Log error message to an error log file."""
    log_file = 'error_log.txt'    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def infer_sqlite_type(value):
    """Infer SQLite data type from a sample value."""
    try:
        int(value)
        return "INTEGER"
    except ValueError:
        try:
            float(value)
            return "REAL"
        except ValueError:
            return "TEXT"

def table_exists(conn, table_name):
    """Check if a table exists in the SQLite database."""
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    cursor = conn.execute(query)
    return cursor.fetchone() is not None

def get_table_schema(conn, table_name):
    """Retrieve the schema of an existing SQLite table."""
    query = f"PRAGMA table_info({table_name});"
    cursor = conn.execute(query)
    schema = {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: data_type}
    return schema
def list_tables(db_path):
    """Lists all tables in the SQLite database."""
    if not os.path.exists(db_path):
        print("No database found. Load a CSV first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    if tables:
        print("\nTables in the database:")
        for table in tables:
            print(f"- {table}")
    else:
        print("No tables found in the database.")

def schema_matches(conn, table_name, df):
    """Check if the DataFrame columns match the existing table schema."""
    existing_schema = get_table_schema(conn, table_name)
    new_columns = df.columns.tolist()

    # Check if every column from the table schema exists in the DataFrame
    for column in existing_schema.keys():
        if column not in new_columns:
            print(f"Column '{column}' missing from CSV.")
            return False

    # Check if every DataFrame column exists in the table schema
    for column in new_columns:
        if column not in existing_schema:
            print(f"Unexpected column '{column}' in CSV.")
            return False

    return True

def append_unique_data(conn, table_name, new_data):
    """Append only new data to an existing SQLite table, ensuring schema match."""
    # Check for schema match
    if not schema_matches(conn, table_name, new_data):
        error_message = f"Schema mismatch between CSV and existing table '{table_name}'."
        print(error_message)
        # Log the error to a file
        log_error(error_message)
        
        while True:
            choice = input("Choose an action - (O)verwrite, (R)ename, (S)kip: ").strip().lower()
            if choice == 'o':
                # Drop the existing table and recreate it
                conn.execute(f"DROP TABLE IF EXISTS {table_name};")
                new_data.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"Table '{table_name}' has been overwritten with new data.")
                return
            elif choice == 'r':
                new_table_name = input("Enter a new table name: ").strip()
                new_data.to_sql(new_table_name, conn, if_exists='replace', index=False)
                print(f"Data saved to new table '{new_table_name}'.")
                return
            elif choice == 's':
                print("Operation skipped. No data appended.")
                return
            else:
                print("Invalid choice. Please enter 'O', 'R', or 'S'.")

    # Load existing data from the database
    existing_data = pd.read_sql(f"SELECT * FROM {table_name};", conn)

    # Find new rows that are not in the existing data
    combined = pd.concat([existing_data, new_data]).drop_duplicates(keep=False)
    unique_new_data = combined[~combined.isin(existing_data)].dropna(how="all")

    if not unique_new_data.empty:
        # Build and execute INSERT statements using string formatting
        columns = ", ".join(unique_new_data.columns)
        for _, row in unique_new_data.iterrows():
            values = ", ".join(f"'{str(val)}'" if isinstance(val, str) else str(val) for val in row)
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
            conn.execute(insert_query)
        conn.commit()
        print(f"Appended {len(unique_new_data)} new rows to '{table_name}'.")
    else:
        print("No new data to append.")

def create_or_append_table_from_csv(csv_path, db_path, table_name = None):
    """Create a new table from CSV or append unique data to an existing table."""
    # Generate table name from CSV file name (without extension)
    if table_name is None:
        table_name = os.path.splitext(os.path.basename(csv_path))[0]

    # Load the CSV into a DataFrame
    df = pd.read_csv(csv_path)

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)

    # Check if the table already exists
    if table_exists(conn, table_name):
        print(f"Table '{table_name}' exists. Checking schema and appending unique data...")
        append_unique_data(conn, table_name, df)
    else:
        print(f"Table '{table_name}' does not exist. Creating table...")
        
        # Infer data types and generate the CREATE TABLE statement using string formatting
        column_types = {}
        for col in df.columns:
            sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
            column_types[col] = infer_sqlite_type(sample_value)

        # Generate the CREATE TABLE statement
        columns = ", ".join([f"{col} {col_type}" for col, col_type in column_types.items()])
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        conn.execute(create_table_query)
        conn.commit()

        # Insert all data into the new table using string formatting
        for _, row in df.iterrows():
            values = ", ".join(f"'{str(val)}'" if isinstance(val, str) else str(val) for val in row)
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({values});"
            print("Generated SQL Insert Query:", insert_query)
            conn.execute(insert_query)
        conn.commit()
        print(f"Table '{table_name}' created with {len(df)} rows.")

    # Verify the data import (showing a few rows)
    sample_query = f"SELECT * FROM {table_name} LIMIT 5;"
    rows = conn.execute(sample_query).fetchall()
    print("Sample rows:")
    for row in rows:
        print(row)

    # Close the connection
    conn.close()

