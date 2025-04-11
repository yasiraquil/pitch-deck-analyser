import os
import sys
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the API token
api_token = os.getenv('HUGGINGFACE_TOKEN')

if not api_token:
    print("Error: Hugging Face API token not found in environment variables")
    print("Please set the HUGGINGFACE_TOKEN environment variable.")
    sys.exit(1)

print("=========================================")
print("    Pitch Deck Analyzer Web Interface    ")
print("=========================================")
print("\nLaunching the web interface...")
print("\nInstead of analyzing a single pitch deck, you can now use our")
print("new web interface to analyze and view reports for multiple pitch decks.")
print("\nFeatures:")
print("- Beautiful, modern UI for viewing analysis reports")
print("- Upload and analyze any pitch deck PDF")
print("- Save and view multiple reports")
print("- Print or share your analysis reports")

# Try to start the web server and open the browser
try:
    # Instructions to run the web app
    print("\nTo use the web application:")
    print("1. Run 'python app.py' in your terminal")
    print("2. Open your browser to http://127.0.0.1:5000")
    print("\nWould you like to launch the web app now? (y/n)")
    
    response = input().strip().lower()
    if response == 'y' or response == 'yes':
        # Attempt to open the browser to the local web server
        print("\nAttempting to open the web interface...")
        try:
            # Open default browser to the web app URL
            webbrowser.open('http://127.0.0.1:5000')
            print("\nBrowser opened! If the web app is not running yet, please start it with 'python app.py'")
        except Exception as e:
            print(f"\nCouldn't open browser automatically: {str(e)}")
            print("Please open http://127.0.0.1:5000 in your browser manually after starting the app.")
    else:
        print("\nYou can start the web app later by running 'python app.py'")

except KeyboardInterrupt:
    print("\nExiting...")
    sys.exit(0) 