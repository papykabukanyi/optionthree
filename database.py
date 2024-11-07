import psycopg2
import json
import random
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

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

    # Create notes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            submission_id INT REFERENCES submissions(id) ON DELETE CASCADE,
            note TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Create communications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communications (
            id SERIAL PRIMARY KEY,
            submission_id INT REFERENCES submissions(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT NOW(),
            email_sent BOOLEAN DEFAULT FALSE
        )
    ''')

    # Create replies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id SERIAL PRIMARY KEY,
            submission_id INT REFERENCES submissions(id) ON DELETE CASCADE,
            sender TEXT,
            body TEXT,
            attachments JSONB,
            timestamp TIMESTAMP
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
    try:
        cursor.execute('''
            INSERT INTO submissions (app_id, data, submission_time)
            VALUES (%s, %s, %s)
        ''', (app_id, json.dumps(data), submission_time))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_submissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM submissions')
        submissions = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [
        (s[0], s[1], s[2] if isinstance(s[2], dict) else json.loads(s[2]), s[3])
        for s in submissions
    ]

def get_submission_by_app_id(app_id):
    """Retrieve a submission by its application ID (app_id) instead of the primary ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM submissions WHERE app_id = %s', (app_id,))
        submission = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if submission:
        return {
            'id': submission[0],
            'app_id': submission[1],
            'data': json.loads(submission[2]) if isinstance(submission[2], str) else submission[2],
            'submission_time': submission[3]
        }
    return None

def delete_submission(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM submissions WHERE id = %s', (submission_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_submission(submission_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE submissions
            SET data = %s
            WHERE id = %s
        ''', (json.dumps(data), submission_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def insert_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        ''', (username, email, password))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user

def insert_note(submission_id, note):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO notes (submission_id, note) VALUES (%s, %s)', (submission_id, note))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_notes(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT note, timestamp FROM notes WHERE submission_id = %s ORDER BY timestamp DESC', (submission_id,))
        notes = [{'note': note, 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')} for note, timestamp in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()
    return notes

def insert_communication(submission_id, status, email_sent=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO communications (submission_id, status, email_sent) VALUES (%s, %s, %s)', (submission_id, status, email_sent))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_communications(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT status, timestamp, email_sent FROM communications WHERE submission_id = %s ORDER BY timestamp DESC', (submission_id,))
        communications = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return communications

def insert_reply(submission_id, sender, body, attachments, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO replies (submission_id, sender, body, attachments, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        ''', (submission_id, sender, body, json.dumps(attachments), timestamp))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_replies(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT sender, body, attachments, timestamp FROM replies WHERE submission_id = %s', (submission_id,))
        replies = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [{
        "sender": sender,
        "body": body,
        "attachments": json.loads(attachments),
        "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for sender, body, attachments, timestamp in replies]

def get_submission_by_id(submission_id):
    """Fetch a submission using either an integer ID or string app_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the input is an integer (for `id`) or a string (for `app_id`)
    try:
        if isinstance(submission_id, int) or submission_id.isdigit():
            cursor.execute('SELECT * FROM submissions WHERE id = %s', (int(submission_id),))
        else:
            cursor.execute('SELECT * FROM submissions WHERE app_id = %s', (submission_id,))
        
        submission = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if submission:
        return {
            'id': submission[0],
            'app_id': submission[1],
            'data': json.loads(submission[2]) if isinstance(submission[2], str) else submission[2],
            'submission_time': submission[3]
        }
    return None
