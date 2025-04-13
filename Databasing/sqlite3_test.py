import sqlite3 as sql

con = sql.connect('Students.db') # Enfore foreign key constraint
con.execute("PRAGMA foreign_keys = ON;")
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS enrollment")
cur.execute("DROP TABLE IF EXISTS classes")
cur.execute("DROP TABLE IF EXISTS students")
cur.execute('''Create Table students(id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name text,last_name text,age integer,major text)''')

cur.executemany("INSERT INTO students (first_name, last_name, age, major) VALUES (?, ?, ?, ?)", [
                ('Alice', 'Johnson', 20, 'Comp Sci'), 
                ('Bob', 'Smith', 22, 'Math'),
                ('Charlie','Brown',19,'Physics'),
                ('Sam', 'G', 27, 'EE')]
                ) 

cur.execute('''Create Table classes(id INTEGER PRIMARY KEY AUTOINCREMENT, name text, number int, year integer,
            spring boolean)''')

cur.executemany("INSERT INTO classes(name, number, year, spring) VALUES (?, ?, ?, ?)", [
                ('ML', 530, 2022, False), 
                ('IC', 565, 2021, True)
                ]) 

cur.execute('''CREATE TABLE enrollment (
    class_id INTEGER,
    student_id INTEGER,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
)''')
cur.executemany("INSERT INTO enrollment(class_id, student_id) VALUES (?, ?)", [
                (2, 1), 
                (1, 2),
                (2, 3), 
                (1, 4)
                ]) 
con.commit()
cur.execute('''
    SELECT students.first_name, classes.name
    FROM students
    JOIN enrollment ON students.id = enrollment.student_id
    JOIN classes ON enrollment.class_id = classes.id
            ''')

"""
class_name = "ML"
cur.execute('''
    SELECT students.first_name, students.last_name
    FROM students
    JOIN enrollment ON students.id = enrollment.student_id
    JOIN classes ON enrollment.class_id = classes.id
    WHERE classes.name = ?
''', (class_name,))
"""
print(cur.fetchall())



"""
cur.execute("PRAGMA table_info(students);")
print(cur.fetchall())
cur.execute("PRAGMA table_info(classes);")
print(cur.fetchall())

cur.execute("PRAGMA table_info(students);")
cur.execute( '''Update students 
            Set major = 'MSEE' 
            Where first_name = 'Sam' ''')

cur.execute("select *  from students where first_name = 'Sam'")
print(cur.fetchone())

cur.execute(''' Select sum(age) From students 
            ''')
print(cur.fetchone())
#cur.execute('''Delete from Students where first_name = 'Charlie' ''')

cur.execute( ''' Alter Table students 
            Add Column graduated Integer default 0''')

cur.execute('''Update students 
            Set graduated = 1
            Where first_name = 'Charlie' ''' )

cur.execute(''' Select sum(age) From students 
                where graduated is not 1
            ''')
print(cur.fetchone())"""

