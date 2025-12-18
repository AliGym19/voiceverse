"""File parsing routes - PDF and DOCX parsing"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from docx import Document
from PyPDF2 import PdfReader
import io

file_parsing_bp = Blueprint('file_parsing', __name__)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@file_parsing_bp.route('/api/parse-docx', methods=['POST'])
@login_required
def parse_docx():
    """Parse DOCX file and extract text"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.docx'):
            return jsonify({'error': 'File must be a .docx file'}), 400

        # Read the DOCX file
        doc = Document(io.BytesIO(file.read()))

        # Extract all text
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])

        return jsonify({
            'success': True,
            'text': text,
            'length': len(text)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to parse DOCX: {str(e)}'}), 500

@file_parsing_bp.route('/api/parse-pdf', methods=['POST'])
@login_required
def parse_pdf():
    """Parse PDF file and extract text"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a .pdf file'}), 400

        # Read the PDF file
        pdf_reader = PdfReader(io.BytesIO(file.read()))

        # Extract text from all pages
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text() + '\n'

        return jsonify({
            'success': True,
            'text': text.strip(),
            'length': len(text),
            'pages': len(pdf_reader.pages)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to parse PDF: {str(e)}'}), 500
