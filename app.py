from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import utils
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'pitch_decks'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['REPORTS_FOLDER'] = 'reports'

# Ensure upload and reports directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

# Utility function for templates
@app.template_filter('now')
def current_time():
    return datetime.now()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get list of available reports
    reports = []
    if os.path.exists(app.config['REPORTS_FOLDER']):
        for filename in os.listdir(app.config['REPORTS_FOLDER']):
            if filename.endswith('.json'):
                report_name = filename.split('.json')[0]
                reports.append(report_name)
    
    return render_template('index.html', reports=reports)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file
        try:
            # Extract text from PDF
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            # Initialize Hugging Face interface
            processing = utils.HuggingFaceInterface()
            
            # Generate analysis
            overview = processing.generate_overview(text)
            responses = processing.generate_response(text)
            
            # Prepare report name
            report_name = os.path.splitext(filename)[0]
            
            # Save as JSON for future use
            report_data = {
                'title': report_name,
                'overview': overview,
                'responses': responses
            }
            
            with open(os.path.join(app.config['REPORTS_FOLDER'], f"{report_name}.json"), 'w') as f:
                json.dump(report_data, f)
            
            # Redirect to report page
            return redirect(url_for('view_report', report_name=report_name))
        
        except Exception as e:
            flash(f"Error processing file: {str(e)}")
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a PDF file.')
    return redirect(url_for('index'))

@app.route('/report/<report_name>')
def view_report(report_name):
    report_path = os.path.join(app.config['REPORTS_FOLDER'], f"{report_name}.json")
    
    if not os.path.exists(report_path):
        flash('Report not found')
        return redirect(url_for('index'))
    
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    return render_template('report.html', 
                          title=report_data['title'],
                          overview=report_data['overview'],
                          responses=report_data['responses'])

if __name__ == '__main__':
    app.run(debug=True, port=5050)