import pandas as pd
import sqlite3
import os
import datetime
from readCSV import *
import openai
import re

def log_error(message):
    """Log error message with timestamp to an error log file."""
    log_file = 'error_log.txt'
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def get_db_schema(db_path):
    """Retrieve the schema of all tables in the SQLite database."""
    if not os.path.exists(db_path):
        return "No database found."

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    schema_info = ""
    for table in tables:
        schema_info += f"\nTable: {table}\n"
        table_schema = conn.execute(f"PRAGMA table_info({table});").fetchall()
        for column in table_schema:
            schema_info += f"  - {column[1]} ({column[2]})\n"

    conn.close()
    return schema_info.strip()
def ask_ai_for_sql(schema, user_query):
    """Pass table schema and user query to AI, then return the generated SQL and explanation."""
    
    openai.api_key =os.getenv("OPENAI_API_KEY")

    if not openai.api_key:
        return None, "Error: OpenAI API key is not set or is invalid."

    prompt = f"""
    You are an AI assistant tasked with converting user queries into SQL statements.
    The database uses SQLite and contains the following tables:
    {schema}
    User Query: {user_query}

    Your task is to:
    1. Generate a SQL query that accurately answers the user's question.
    2. Ensure the SQL is compatible with SQLite syntax.
    3. Provide a short comment explaining what the query does.

    Output Format:
    - SQL Query
    - Explanation
    """

    try:
        client = openai.OpenAI()  # Create an OpenAI client
        response = client.chat.completions.create(
            model="gpt-4",  # Use "gpt-3.5-turbo" if needed
            messages=[
                {"role": "system", "content": "You are a helpful AI that generates SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        ai_output = response.choices[0].message.content.strip()

        # Log the AI response for debugging
        print("AI response:", ai_output)

        # Look for SQL Query and Explanation sections
        try:
            # Attempt to find and separate the query and explanation
            if "SQL Query:" in ai_output and "Explanation:" in ai_output:
                # Split based on these labels
                sql_start = ai_output.find("SQL Query:") + len("SQL Query:")
                sql_stop =  ai_output.find("Explanation:") 
                explanation_start = ai_output.find("Explanation:") + len("Explanation:")

                sql_query = ai_output[sql_start:sql_stop].strip()
                sql_query = re.sub(r"```sql(.*?)```", r"\1", sql_query, flags=re.DOTALL).strip()

                explanation = ai_output[explanation_start:].strip()

                # Remove any Markdown code block formatting (```sql ... ```)
                return sql_query.strip(), explanation.strip()
            else:
                # If the format is not as expected, return an error message
                return None, f"Error: The response format was incorrect. AI returned: {ai_output}"
        except Exception as e:
            return None, f"Error extracting query and explanation: {e}"

    except Exception as e:
        return None, f"Error communicating with AI: {e}"
    
def run_sql_query(db_path, generated_sql):
    """Pass schema and user request to AI, execute generated SQL, and display results."""
    generated_sql = generated_sql.replace('\n', ' ')
    if not os.path.exists(db_path):
        print("No database found. Load a CSV first.")
        return

    schema = get_db_schema(db_path)
    print(schema)
    print(generated_sql + '\n')
    # Execute the SQL query and display results
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql(generated_sql, conn)
        print("\nQuery Result:")
        print(result)
    except Exception as e:
        log_error(f"Error running AI-generated query: {str(e)}")
        print(f"Error executing query: {e}")
    conn.close()

def chatbot_interaction():
    """Chatbot-like interaction to handle CSV loading, SQL execution, and AI-generated queries."""
    db_path = "my_database.db"

    print("Welcome to the SQLite Chatbot!")
    
    # Ensure a database exists
    if not os.path.exists(db_path):
        print("No database found. A new database will be created when you load a CSV file.")

    while True:
        print("\nOptions:")
        print("1. Load a CSV file and update the database")
        print("2. Run a manual SQL query")
        print("3. Generate and run an AI-powered SQL query")
        print("4. List all tables")
        print("5. Exit")

        user_input = input("What would you like to do? (1/2/3/4/5): ").strip()

        if user_input == '1':
            csv_path = input("Enter the path to the CSV file: ").strip()
            if os.path.exists(csv_path):
                create_or_append_table_from_csv(csv_path, db_path)
            else:
                print("File not found. Please enter a valid CSV file path.")

        elif user_input == '2':
            query = input("Enter the SQL query to run: ").strip()
            run_sql_query(db_path, query)

        elif user_input == '3':
            user_query = input("Describe the data you want to retrieve: ").strip()
            schema = get_db_schema(db_path)

            generated_sql, explanation = ask_ai_for_sql(schema, user_query)

            if generated_sql is None:
                print("AI failed to generate SQL:", explanation)
                continue

            print("\nGenerated SQL Query:")
            print(generated_sql)
            print("\nExplanation:")
            print(explanation)

            # Ask user for confirmation before executing the query
            confirm = input("Would you like to run this query? (yes/no): ").strip().lower()
            if confirm == "yes":
                run_sql_query(db_path, generated_sql)
            else:
                print("Query execution canceled.")

        elif user_input == '4':
            list_tables(db_path)

        elif user_input == '5':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
# Run the chatbot

chatbot_interaction()