# Pitch Deck Analyzer

A modern web application for analyzing startup pitch decks with AI. This tool uses Hugging Face's Mistral-7B model to provide an investor's perspective on pitch decks, helping founders, investors, and entrepreneurs evaluate pitch decks effectively.

## Features

- **Modern Web Interface**: Elegant and user-friendly UI for viewing analysis reports
- **Pitch Deck Analysis**: Upload and analyze any pitch deck in PDF format
- **Multiple Reports**: Save and access multiple analysis reports
- **Detailed Insights**: Get comprehensive analysis including:
  - Business model evaluation
  - Market analysis
  - Competitive landscape
  - Investment readiness
  - Growth potential

## Installation

1. Clone this repository:
   ```
   git clone <your-repository-url>
   cd pitch-deck-analyzer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Hugging Face API token:
   - Create a `.env` file in the root directory
   - Add your token: `HUGGINGFACE_TOKEN=your_token_here`

## Usage

1. Start the web application:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. Upload a pitch deck PDF file and get your analysis

## Quick Start

Run the helper script to get started:
```
python analyze_sample.py
```

This will guide you through launching the web interface and analyzing your first pitch deck.

## Directory Structure

- `app.py` - Flask web application
- `utils.py` - Utility functions and HuggingFace integration
- `templates/` - HTML templates for the web interface
- `pitch_decks/` - Directory for uploaded pitch decks
- `reports/` - Directory for saved analysis reports

## Requirements

- Python 3.7+
- Flask
- PyPDF2
- Langchain
- python-dotenv
- Hugging Face API access

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.