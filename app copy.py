from flask_socketio import SocketIO
from flask import Flask, jsonify, request, render_template, redirect, url_for
from database import (
    insert_note, get_notes, insert_communication, get_submission_by_id
)
import logging

# Flask & WebSocket setup
app = Flask(__name__)
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

@app.route('/api/submissions/<int:submission_id>/note', methods=['POST'])
def add_note_with_notification(submission_id):
    data = request.get_json()
    note = data.get('note')
    if not note:
        return jsonify({'error': 'Note content required'}), 400

    # Clean and save note
    note_cleaned = note.replace('@email', '').strip()
    insert_note(submission_id, note_cleaned)
    logging.info(f"Note added for submission ID {submission_id}: {note_cleaned}")

    # Emit the new note to clients via WebSocket
    socketio.emit('note_update', {'submissionId': submission_id, 'note': note_cleaned})

    # If @email flag is in the note, send email to the borrower
    if '@email' in note:
        submission = get_submission_by_id(submission_id)
        borrower_email = submission['data'].get("borrower_email")
        if borrower_email:
            send_email(borrower_email, f"Update on Your Application ID: {submission['app_id']}", note_cleaned)

    return jsonify({'message': 'Note added and email sent if applicable.'}), 201

@socketio.on('connect')
def handle_connect():
    logging.info("Client connected to WebSocket.")

@socketio.on('disconnect')
def handle_disconnect():
    logging.info("Client disconnected from WebSocket.")

if __name__ == "__main__":
    socketio.run(app, debug=True)
