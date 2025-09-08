import os
import psycopg
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)

def get_db_connection():
  """A function to connect to the database"""
  conn = psycopg.connect(os.environ['DATABASE_URL'])
  return conn

@app.route('/create/', methods=('GET', 'POST'))
def create():
  """A function to create a new course and add to database"""
  if request.method == 'POST':
    id = request.form['id']
    name = request.form['name']
    instructor = request.form['instructor']
    room_number = request.form['room_number']
    print(id, name, instructor, room_number)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO courses(id, name, instructor, room_number)
      VALUES (%s, %s, %s, %s)""",
      (id, name, instructor, room_number)
      )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))
  return render_template('create.html')

@app.route('/')
def index():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("""
    SELECT * FROM courses;""")
  courses = cur.fetchall()

  cur.execute("""
    SELECT COUNT(*) FROM courses;""")
  count = cur.fetchall()
  print(count)
  cur.close()
  conn.close()
  return render_template('index.html', courses=courses)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)