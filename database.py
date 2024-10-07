import psycopg2
import json
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DB_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id SERIAL PRIMARY KEY,
            app_id TEXT NOT NULL,
            data JSONB,
            submission_time TIMESTAMP
        )
    ''')

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()


def generate_app_id():
    return f"HE-{random.randint(111111, 999999)}"


def insert_submission(app_id, data, submission_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (app_id, data, submission_time)
        VALUES (%s, %s, %s)
    ''', (app_id, json.dumps(data), submission_time))
    conn.commit()
    cursor.close()
    conn.close()


def get_submissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions')
    submissions = cursor.fetchall()
    cursor.close()
    conn.close()
    return submissions


def get_submission_by_id(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = %s', (submission_id,))
    submission = cursor.fetchone()
    cursor.close()
    conn.close()
    return submission


def delete_submission(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submissions WHERE id = %s', (submission_id,))
    conn.commit()
    cursor.close()
    conn.close()


def update_submission(submission_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE submissions
        SET data = %s
        WHERE id = %s
    ''', (json.dumps(data), submission_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (%s, %s, %s)
    ''', (username, email, password))
    conn.commit()
    cursor.close()
    conn.close()


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
