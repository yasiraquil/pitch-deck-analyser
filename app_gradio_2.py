import gradio as gr
import utils
import os

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'doc', 'ppt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process(file, model):
    # Convert the model name to the model id
    model_dict = utils.get_model_dict()
    model = model_dict[model]

    # check if the file is allowed
    if file is None or not allowed_file(file.name):
        return "Invalid file format. Please upload a PDF."
    
    filepath = file.name
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

file_input = gr.File(file_count="single", file_types=[".pdf", ".docx", ".doc", ".pptx", ".ppt"])
model_dict = utils.get_model_dict()
model_input = gr.Radio(list(model_dict.keys()), label="Model", value="GPT 4")

gr.Interface(fn=process, inputs=[file_input, model_input] , outputs="file", css="footer {visibility: hidden}", allow_flagging="never", title="Pitch Deck Parser").launch(debug=True, show_api=False)