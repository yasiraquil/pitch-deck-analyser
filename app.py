from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import utils
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

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

# Sample influencer database (in a real app, this would be a proper database)
INFLUENCER_DB = {
    'tech': [
        {
            'name': 'John TechInvestor',
            'linkedin': 'https://www.linkedin.com/in/johntech',
            'specialization': 'Enterprise Software, Cloud Computing',
            'keywords': ['saas', 'cloud', 'enterprise', 'software', 'tech', 'startup', 'innovation']
        },
        {
            'name': 'Sarah StartupGuru',
            'linkedin': 'https://www.linkedin.com/in/sarahstartup',
            'specialization': 'Early-stage Tech Startups',
            'keywords': ['startup', 'tech', 'early-stage', 'innovation', 'founder', 'venture']
        }
    ],
    'health': [
        {
            'name': 'Dr. HealthInnovator',
            'linkedin': 'https://www.linkedin.com/in/healthinnovator',
            'specialization': 'Healthcare Technology',
            'keywords': ['healthcare', 'medical', 'biotech', 'health', 'medicine', 'patient']
        }
    ],
    'fintech': [
        {
            'name': 'Mike FinTechPro',
            'linkedin': 'https://www.linkedin.com/in/mikefintech',
            'specialization': 'Financial Technology',
            'keywords': ['fintech', 'blockchain', 'payments', 'finance', 'banking', 'financial']
        }
    ],
    'ai': [
        {
            'name': 'AI Expert',
            'linkedin': 'https://www.linkedin.com/in/aiexpert',
            'specialization': 'Artificial Intelligence',
            'keywords': ['ai', 'machine learning', 'deep learning', 'artificial intelligence', 'ml', 'data']
        }
    ],
    'sustainability': [
        {
            'name': 'Eco Investor',
            'linkedin': 'https://www.linkedin.com/in/ecoinvestor',
            'specialization': 'Sustainable Technology',
            'keywords': ['sustainability', 'green tech', 'environment', 'clean energy', 'eco', 'renewable']
        }
    ]
}

# Utility function for templates
@app.template_filter('now')
def current_time():
    return datetime.now()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_pitch_match(pitch, influencer_type):
    matches = []
    processing = utils.HuggingFaceInterface()
    
    for influencer in INFLUENCER_DB.get(influencer_type, []):
        # Calculate match score based on keyword presence
        keyword_matches = sum(1 for keyword in influencer['keywords'] 
                            if keyword.lower() in pitch.lower())
        score = min(100, (keyword_matches / len(influencer['keywords'])) * 100)
        
        # Generate personalized suggestions
        prompt = f"""As an expert pitch advisor, analyze this pitch for {influencer['name']}, 
        who specializes in {influencer['specialization']}. 
        The pitch is: {pitch}
        
        Provide 3 specific suggestions to improve the pitch for this investor. Make the suggestions actionable and specific."""
        
        try:
            suggestions_text = processing.generate_text(prompt, max_length=500)
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            suggestions = suggestions[:3]  # Take top 3 suggestions
        except Exception as e:
            suggestions = [
                "Focus on the investor's area of expertise",
                "Highlight relevant market opportunities",
                "Emphasize scalable aspects of your business"
            ]
        
        matches.append({
            'name': influencer['name'],
            'linkedin': influencer['linkedin'],
            'specialization': influencer['specialization'],
            'score': round(score, 1),
            'suggestions': suggestions
        })
    
    # Sort matches by score
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

@app.route('/pitch-matcher')
def pitch_matcher():
    return render_template('pitch_matcher.html')

@app.route('/match-pitch', methods=['POST'])
def match_pitch():
    try:
        pitch = request.form.get('pitch', '')
        influencer_type = request.form.get('influencerType', '')
        
        if not pitch or not influencer_type:
            return jsonify({'error': 'Missing required fields'}), 400
        
        matches = analyze_pitch_match(pitch, influencer_type)
        return jsonify({'matches': matches})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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