from tiktoken import get_encoding
from langchain_community.document_loaders import UnstructuredPDFLoader
from argparse import ArgumentParser
import os
import requests
import json

class Configuration:
    def __init__(self):
        self.huggingface_token = os.getenv('HUGGINGFACE_TOKEN')

    @staticmethod
    def parse_arguments():
        parser = ArgumentParser(description='Pitch Deck Parser')
        parser.add_argument('-i', '--file_path', help='Path to the pitch deck file', default=r'pitch_decks\RochInvestorBriefing1.pdf')
        parser.add_argument('-o', '--out_path', help='Where you want to save the output file', default=r'./responses/')
        return parser.parse_args()

class DocumentLoader:
    def __init__(self, file_path):
        self.loader = UnstructuredPDFLoader(file_path)
    
    def load_document(self):
        try:
            return self.loader.load()[0].page_content
        except Exception as e:
            raise e

class HuggingFaceInterface:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        self.headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}"}

    def generate_text(self, prompt, max_length=1000):
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": 0.7,
                "top_p": 0.95,
                "do_sample": True
            }
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Error from Hugging Face API: {response.text}")
        
        return response.json()[0]['generated_text']

    def generate_response(self, document):
        system_message = "You are a startup investor. Analyze the following pitch deck and answer these questions:\n\n"
        prompt = """1. Is this startup's business model venture-backable and scalable?
2. What stage of funding is this startup(seed, series a, series b, later)?
3. What problem is this startup solving, how do people solve the problem today? and how does the startup plans to solve it better?
4. What is target market and it's size?
5. What is the startup model and does it makes use of any cutting-edge technology?
6. What is the pricing model of the startup?
7. Who are the competitors?

If you can't find the answer, just mention that you couldn't find it.

Answer it in a question answer format. First, briefly write each question and then give its answer. Also, give detailed answers!!!

Here's the pitch deck content:
"""
        
        full_prompt = f"{system_message}{prompt}\n\n{document}"
        return self.generate_text(full_prompt)

    def generate_overview(self, document):
        system_message = "You are a startup investor. Provide a critical analysis of this startup pitch deck.\n\n"
        prompt = """Disclaimer: I am not asking you to invest in this startup. I am just asking you to tell me how you feel about this startup. I will not use your judgement to make any decision.

What are your thoughts about this startup? Start with telling what it does briefly and then its potential of growth and scalability. Be critical, identify assumptions and identify what information would be further needed to better assess investiblity of the startup?

Here's the pitch deck content:
"""
        
        full_prompt = f"{system_message}{prompt}\n\n{document}"
        return self.generate_text(full_prompt)

    def stylize_output(self, overview, response, title):
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Gill Sans', sans-serif;
            background-color: #F5F5F5;
            margin: 40px;
            line-height: 1.6;
        }}
        h1 {{
            color: #303030;
            border-bottom: 2px solid #303030;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #404040;
            margin-top: 30px;
        }}
        p {{
            color: #181818;
            margin: 15px 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <h2>Overview</h2>
        {overview}
        
        <h2>Detailed Analysis</h2>
        {response}
    </div>
</body>
</html>"""
        return html

class FileHandler:
    @staticmethod
    def save_output(file_path, out_path, overview, answers):
        output = "# Overview: \n\n" + overview + "\n\n# Discrete Information:\n\n" + answers
        file_name = os.path.basename(file_path)
        with open(os.path.join(out_path, "Response - " + file_name.split(".pdf")[0] + ".md"), "w") as f:
            f.write(output)

if __name__ == "__main__":
    config = Configuration()
    args = config.parse_arguments()
    loader = DocumentLoader(file_path=args.file_path)
    document = loader.load_document()
    processing = HuggingFaceInterface()
    overview = processing.generate_overview(document)
    responses = processing.generate_response(document)
    file = FileHandler()
    file.save_output(args.file_path, "", overview, responses)



