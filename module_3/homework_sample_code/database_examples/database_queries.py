import os
import psycopg
import psycopg_pool

pool = psycopg_pool.ConnectionPool(os.environ['DATABASE_URL'])

#Get a connection from the pool.
conn = pool.getconn()

with conn.cursor() as cur:

  #Select and print all
  cur.execute("""
    SELECT * FROM students;""")

  print("Students in Database Include: ", cur.fetchall())

  cur.execute("""
    SELECT * FROM courses;""")

  print("Courses in Database Include: ", cur.fetchall())

  cur.execute("""
    SELECT * FROM studentCourses;""")

  print("Student Courses pairs in Database Include: ", cur.fetchall())

  # Select all the students taking Java and tell me their names

  cur.execute("""
    SELECT s.name FROM students s
    INNER JOIN studentCourses sc ON s.id = sc.studentID
    INNER JOIN courses c ON sc.courseID = c.id
    WHERE c.name = 'Java';""")
  
  print("Students taking Java: ", cur.fetchall())

  # Calculate the average GPA needed for each course
  cur.execute("""
    SELECT AVG(c.gpa) 
    FROM courses c;""")

  print("Average GPA for each course: ", cur.fetchall())

