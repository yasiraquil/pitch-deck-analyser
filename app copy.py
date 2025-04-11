from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import utils
import openai
import os
from werkzeug.utils import secure_filename
from io import BytesIO
import base64
import eventlet
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Log initialization
app.logger.info("App initialized")

model = "gpt-3.5-turbo-16k"
openai.api_key = os.environ.get('OPENAI_API_KEY')
UPLOAD_FOLDER = os.getcwd() + '/temp_uploads'

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('process_file')
def handle_file(data):
    try:
        app.logger.info("File processing started")
        file_data = base64.b64decode(data['file'])
        file_name = data['filename']

        if not file_data or not allowed_file(file_name):
            emit('file_response', {'error': 'Invalid file.'})
            return

        file = BytesIO(file_data)

        # save to temporary folder
        filename = secure_filename(file_name)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(file.read())
        
        # Processing code restored
        loader = utils.DocumentLoader(filepath)
        document = loader.load_document()
        processing = utils.OpenAIInterface(model)
        overview = processing.generate_overview(document)
        responses = processing.generate_response(document)
        stylized_output = processing.stylize_output(overview, responses, filename)
        
        # Delete the file after processing
        os.remove(filepath)

        # Save the stylized_output in the session
        session['stylized_output'] = stylized_output
        session['filename_for_download'] = filename + ".html"

        emit('file_response', {'content': stylized_output, 'filename': filename + ".html"})
        app.logger.info("File processing complete")
    except Exception as e:
        emit('file_response', {'error': f"Server error: {str(e)}"})
        app.logger.error(f"Error during file processing: {str(e)}")

@socketio.on('download_file')
def handle_download(data):
    try:
        app.logger.info("File download initiated")
        buffer = BytesIO()
        stylized_output = session.get('stylized_output', "")
        filename_for_download = session.get('filename_for_download', "output.html")
        buffer.write(stylized_output.encode('utf-8'))
        buffer.seek(0)

        # Convert buffer to base64 and send to client
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        emit('download_response', {'file_data': base64_data, 'filename': filename_for_download})
        app.logger.info("File download complete")
    except Exception as e:
        emit('download_response', {'error': f"Server error: {str(e)}"})
        app.logger.error(f"Error during file download: {str(e)}")

if __name__ == "__main__":
    socketio.run(app, debug=True)