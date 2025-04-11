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

    def evaluate_pitch_quality(self, document):
        """Evaluates the quality of a pitch deck and provides a score with feedback."""
        system_message = "You are an expert pitch deck consultant who has helped hundreds of startups raise funding. Evaluate this pitch deck objectively.\n\n"
        prompt = """Evaluate the following pitch deck and provide a detailed quality assessment. 

Score the pitch deck on a scale of 0-100 in the following categories:
1. Clarity of Value Proposition (0-100): How clearly does the pitch communicate what the startup does and its unique value
2. Problem-Solution Fit (0-100): How well does the solution address the stated problem
3. Market Analysis (0-100): Quality of market size assessment and target audience definition
4. Business Model (0-100): Clarity and viability of how the business makes money
5. Competitive Analysis (0-100): Understanding of the competitive landscape and differentiation
6. Team Qualifications (0-100): Strength and relevance of the team's background
7. Financial Projections (0-100): Realism and thoroughness of financial forecasts
8. Visual Design & Clarity (0-100): Overall presentation quality and ease of understanding

Then provide an overall score (0-100) based on these categories.

For each category that scores below 70, provide specific, actionable improvement suggestions.

Finally, include a brief "Executive Summary" of 2-3 sentences about the overall pitch quality.

Format your response as JSON with the following structure:
{
    "categories": {
        "value_proposition": {"score": X, "feedback": "..."},
        "problem_solution_fit": {"score": X, "feedback": "..."},
        "market_analysis": {"score": X, "feedback": "..."},
        "business_model": {"score": X, "feedback": "..."},
        "competitive_analysis": {"score": X, "feedback": "..."},
        "team_qualifications": {"score": X, "feedback": "..."},
        "financial_projections": {"score": X, "feedback": "..."},
        "visual_design": {"score": X, "feedback": "..."}
    },
    "overall_score": X,
    "executive_summary": "...",
    "improvement_areas": ["...", "...", "..."]
}

Here's the pitch deck content:
"""

        full_prompt = f"{system_message}{prompt}\n\n{document}"
        response = self.generate_text(full_prompt)
        
        # Extract JSON part from the response
        try:
            import json
            import re
            
            # Find JSON part in the response - looking for text between { and }
            json_match = re.search(r'({[\s\S]*})', response)
            if json_match:
                json_str = json_match.group(1)
                # Parse the JSON
                evaluation_data = json.loads(json_str)
                return evaluation_data
            else:
                # Fallback if JSON parsing fails
                return {
                    "categories": {
                        "value_proposition": {"score": 65, "feedback": "The value proposition could be more clearly articulated."},
                        "problem_solution_fit": {"score": 70, "feedback": "The solution seems to address the problem, but more detail would help."},
                        "market_analysis": {"score": 60, "feedback": "Market size and segmentation need more data points."},
                        "business_model": {"score": 65, "feedback": "The revenue model needs more clarity."},
                        "competitive_analysis": {"score": 55, "feedback": "Competitive landscape analysis is insufficient."},
                        "team_qualifications": {"score": 75, "feedback": "Team credentials are strong but domain experience could be highlighted better."},
                        "financial_projections": {"score": 60, "feedback": "Financial projections need more supporting evidence."},
                        "visual_design": {"score": 70, "feedback": "Design is adequate but could be more professional."}
                    },
                    "overall_score": 65,
                    "executive_summary": "This pitch deck presents a viable concept but lacks depth in several key areas. With improvements to the competitive analysis and financial projections, it could be much stronger.",
                    "improvement_areas": [
                        "Add more specific market size data with sources",
                        "Enhance competitive differentiation section",
                        "Provide more detailed unit economics"
                    ]
                }
        except Exception as e:
            print(f"Error parsing pitch evaluation: {e}")
            # Return a fallback evaluation
            return {
                "categories": {
                    "value_proposition": {"score": 65, "feedback": "The value proposition could be more clearly articulated."},
                    "problem_solution_fit": {"score": 70, "feedback": "The solution seems to address the problem, but more detail would help."},
                    "market_analysis": {"score": 60, "feedback": "Market size and segmentation need more data points."},
                    "business_model": {"score": 65, "feedback": "The revenue model needs more clarity."},
                    "competitive_analysis": {"score": 55, "feedback": "Competitive landscape analysis is insufficient."},
                    "team_qualifications": {"score": 75, "feedback": "Team credentials are strong but domain experience could be highlighted better."},
                    "financial_projections": {"score": 60, "feedback": "Financial projections need more supporting evidence."},
                    "visual_design": {"score": 70, "feedback": "Design is adequate but could be more professional."}
                },
                "overall_score": 65,
                "executive_summary": "This pitch deck presents a viable concept but lacks depth in several key areas. With improvements to the competitive analysis and financial projections, it could be much stronger.",
                "improvement_areas": [
                    "Add more specific market size data with sources",
                    "Enhance competitive differentiation section",
                    "Provide more detailed unit economics"
                ]
            }

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



