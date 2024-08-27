import sqlite3
import json
import random

def init_db():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Create submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT,
            data TEXT,
            submission_time TEXT
        )
    ''')

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

def generate_app_id():
    return f"HE-{random.randint(111111, 999999)}"

def insert_submission(app_id, data, submission_time):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    data_json = json.dumps(data)
    cursor.execute('''
        INSERT INTO submissions (app_id, data, submission_time)
        VALUES (?, ?, ?)
    ''', (app_id, data_json, submission_time))
    conn.commit()
    conn.close()

def get_submissions():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions')
    submissions = cursor.fetchall()
    conn.close()
    return submissions

def get_submission_by_id(submission_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    submission = cursor.fetchone()
    conn.close()
    return submission

def delete_submission(submission_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
    conn.commit()
    conn.close()

def update_submission(submission_id, data):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    data_json = json.dumps(data)
    cursor.execute('''
        UPDATE submissions
        SET data = ?
        WHERE id = ?
    ''', (data_json, submission_id))
    conn.commit()
    conn.close()

def insert_user(username, email, password):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
    ''', (username, email, password))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

