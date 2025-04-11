import gradio as gr
import utils
import os

temp_folder = os.path.join(os.getcwd(),'tmp')
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model = 'gpt-3.5-turbo-16k'

def process(file):
    # check if the file is allowed
    if file is None or not allowed_file(file.name):
        return "Invalid file format. Please upload a PDF."
    
    filepath = file.name
    print(filepath)
    try:
        loader = utils.DocumentLoader(filepath)
        print("loader created")
        document = loader.load_document()
        print("document loaded")
        processing = utils.OpenAIInterface(model)
        print("processing created")
        overview = processing.generate_overview(document)
        print("overview generated")
        responses = processing.generate_response(document)
        print("response generated")
        stylized_output = processing.stylize_output(overview, responses, 'abc')
        print("stylized output generated")
    except Exception as e:
        return f"Error processing file: {str(e)}"

    # Saving the stylized_output to a file
    filepath = filepath.split(".pdf")[0] + ".html"
    print("filepath: ", filepath)
    with open(filepath, 'w') as f:
        f.write(stylized_output)
    print("file saved")
    return filepath

gr.Interface(fn=process, inputs="file", outputs="file", css="footer {visibility: hidden}", allow_flagging="never").launch(debug=True, show_api=False)