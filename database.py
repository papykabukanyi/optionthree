# import sqlite3
# import json
# import random

# def init_db():
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
    
#     # Create submissions table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS submissions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             app_id TEXT,
#             data TEXT,
#             submission_time TEXT
#         )
#     ''')

#     # Create users table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE,
#             email TEXT UNIQUE,
#             password TEXT
#         )
#     ''')

#     conn.commit()
#     conn.close()

# def generate_app_id():
#     return f"HE-{random.randint(111111, 999999)}"

# def insert_submission(app_id, data, submission_time):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     data_json = json.dumps(data)
#     cursor.execute('''
#         INSERT INTO submissions (app_id, data, submission_time)
#         VALUES (?, ?, ?)
#     ''', (app_id, data_json, submission_time))
#     conn.commit()
#     conn.close()

# def get_submissions():
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM submissions')
#     submissions = cursor.fetchall()
#     conn.close()
#     return submissions

# def get_submission_by_id(submission_id):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
#     submission = cursor.fetchone()
#     conn.close()
#     return submission

# def delete_submission(submission_id):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
#     conn.commit()
#     conn.close()

# def update_submission(submission_id, data):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     data_json = json.dumps(data)
#     cursor.execute('''
#         UPDATE submissions
#         SET data = ?
#         WHERE id = ?
#     ''', (data_json, submission_id))
#     conn.commit()
#     conn.close()

# def insert_user(username, email, password):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO users (username, email, password)
#         VALUES (?, ?, ?)
#     ''', (username, email, password))
#     conn.commit()
#     conn.close()

# def get_user_by_email(email):
#     conn = sqlite3.connect('app.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
#     user = cursor.fetchone()
#     conn.close()
#     return user

# import psycopg2
# import json
# import random
# from psycopg2 import sql
# from dotenv import load_dotenv
# import os

# load_dotenv()

# # PostgreSQL connection parameters
# def get_db_connection():
#     conn = psycopg2.connect(
#         host=os.getenv('DB_HOST'),
#         database=os.getenv('DB_NAME'),
#         user=os.getenv('DB_USER'),
#         password=os.getenv('DB_PASSWORD')
#     )
#     return conn

# def init_db():
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Create submissions table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS submissions (
#             id SERIAL PRIMARY KEY,
#             app_id TEXT,
#             data JSONB,
#             submission_time TIMESTAMP
#         )
#     ''')

#     # Create users table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id SERIAL PRIMARY KEY,
#             username TEXT UNIQUE,
#             email TEXT UNIQUE,
#             password TEXT
#         )
#     ''')

#     conn.commit()
#     cursor.close()
#     conn.close()

# def generate_app_id():
#     return f"HE-{random.randint(111111, 999999)}"

# def insert_submission(app_id, data, submission_time):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO submissions (app_id, data, submission_time)
#         VALUES (%s, %s, %s)
#     ''', (app_id, json.dumps(data), submission_time))
#     conn.commit()
#     cursor.close()
#     conn.close()

# def get_submissions():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM submissions')
#     submissions = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     return submissions

# def get_submission_by_id(submission_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM submissions WHERE id = %s', (submission_id,))
#     submission = cursor.fetchone()
#     cursor.close()
#     conn.close()
#     return submission

# def delete_submission(submission_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('DELETE FROM submissions WHERE id = %s', (submission_id,))
#     conn.commit()
#     cursor.close()
#     conn.close()

# def update_submission(submission_id, data):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         UPDATE submissions
#         SET data = %s
#         WHERE id = %s
#     ''', (json.dumps(data), submission_id))
#     conn.commit()
#     cursor.close()
#     conn.close()

# def insert_user(username, email, password):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO users (username, email, password)
#         VALUES (%s, %s, %s)
#     ''', (username, email, password))
#     conn.commit()
#     cursor.close()
#     conn.close()

# def get_user_by_email(email):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
#     user = cursor.fetchone()
#     cursor.close()
#     conn.close()
#     return user
import psycopg2
import os
import json

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id SERIAL PRIMARY KEY,
            app_id TEXT,
            data JSONB,
            submission_time TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def generate_app_id():
    import random
    return f"HE-{random.randint(111111, 999999)}"

def insert_submission(app_id, data, submission_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (app_id, data, submission_time)
        VALUES (%s, %s, %s)
    ''', (app_id, json.dumps(data), submission_time))
    conn.commit()
    conn.close()

def get_submissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions')
    submissions = cursor.fetchall()
    conn.close()
    return submissions

def get_submission_by_id(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = %s', (submission_id,))
    submission = cursor.fetchone()
    conn.close()
    return submission

def delete_submission(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submissions WHERE id = %s', (submission_id,))
    conn.commit()
    conn.close()
