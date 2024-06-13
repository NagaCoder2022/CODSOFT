import os
from flask import Flask, request, render_template, send_file
import pandas as pd
import re
import uuid
from bs4 import BeautifulSoup

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_information_from_cv(cv_file):
    try:
        # Read the entire content of the file
        text = cv_file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = cv_file.read().decode('latin-1')  # Try another encoding
        except UnicodeDecodeError:
            return "Error: Unable to decode file"

    # Extract email using regex
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)

    # Extract phone number using regex
    phone = re.findall(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', text)

    # Parse HTML and extract plain text
    soup = BeautifulSoup(text, 'html.parser')
    plain_text = soup.get_text(separator='\n')  # Use newline separator

    return email, phone, plain_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist('file')
    data = {'Email': [], 'Contact': [], 'Text': []}

    for file in uploaded_files:
        email, phone, plain_text = extract_information_from_cv(file)
        data['Email'].extend(email)
        data['Contact'].extend(phone)
        data['Text'].append(plain_text)

        # Save the uploaded file to the uploads folder
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        cv_file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(cv_file_path)

    # Pad arrays with empty strings to ensure they have the same length
    max_length = max(len(data['Email']), len(data['Contact']), sum(len(text.split('\n')) for text in data['Text']))
    data['Email'] += [''] * (max_length - len(data['Email']))
    data['Contact'] += [''] * (max_length - len(data['Contact']))
    text_rows = []
    for text in data['Text']:
        lines = text.split('\n')
        text_rows.extend(lines)
    text_rows += [''] * (max_length - len(text_rows))

    # Create DataFrame
    df = pd.DataFrame({
        'Email': data['Email'],
        'Contact': data['Contact'],
        'Text': text_rows
    })

    output_filename = str(uuid.uuid4()) + '.xlsx'  # Generate a unique filename with xlsx extension
    df.to_excel(output_filename, index=False)

    return send_file(output_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)