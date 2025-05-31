import os
import requests
import argparse
import time
import pathlib
from dotenv import load_dotenv

# Get the directory containing this script
script_dir = pathlib.Path(__file__).parent.absolute()

# Load environment variables from .env file in the same directory as the script
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Set up command line arguments
parser = argparse.ArgumentParser(description='Convert text to speech using Eleven Labs API')
parser.add_argument('--api-key', help='Eleven Labs API Key')
parser.add_argument('--text', default="Hello, this is a test of the Eleven Labs text to speech API.", 
                    help='Text to convert to speech')
parser.add_argument('--voice-id', default="JBFqnCBsd6RMkjVDRZzb", 
                    help='Voice ID (default: Rachel)')
parser.add_argument('--model-id', default="eleven_flash_v2_5", 
                    help='Model ID (default: eleven_flash_v2_5 - faster than multilingual)')
parser.add_argument('--output', default="elevenlabs_output.mp3", 
                    help='Output filename')
args = parser.parse_args()

# Get API key from command line argument or environment variable
api_key = args.api_key or os.environ.get('ELEVENLABS_API_KEY')

# Get current working directory for output path
current_dir = os.getcwd()

def text_to_speech():
    """Simple function to convert text to speech using Eleven Labs API"""
    if not api_key:
        print("Error: No API key provided.")
        print("Please provide your API key using one of these methods:")
        print("1. Command line: python3 eleven-labs-text-to-speech.py --api-key YOUR_API_KEY")
        print("2. Environment variable: export ELEVENLABS_API_KEY=YOUR_API_KEY")
        print("3. .env file: Create a .env file with ELEVENLABS_API_KEY=YOUR_API_KEY")
        return False
    
    # Get parameters from command line arguments
    text = args.text
    voice_id = args.voice_id
    model_id = args.model_id
    output_file = args.output
    
    # Full path to output file
    output_path = os.path.join(current_dir, output_file)
    
    # Debug API key information
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
        print(f"API Key first 4 chars: {api_key[:4]}")
        print(f"API Key last 4 chars: {api_key[-4:] if len(api_key) > 4 else api_key}")
        if api_key.startswith("your") or "placeholder" in api_key.lower() or "example" in api_key.lower():
            print("WARNING: Your API key appears to be a placeholder. Please replace it with your actual Eleven Labs API key.")
    else:
        print("API Key: Not provided")
    print(f"Text: '{text}'")
    print(f"Voice ID: {voice_id}")
    print(f"Model ID: {model_id}")
    print(f"Output will be saved to: {output_path}")
    
    # API endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    # Request headers
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Request body
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        print("\nSending request to Eleven Labs API...")
        start_time = time.time()
        
        # Make the API request
        response = requests.post(url, json=data, headers=headers)
        
        # Check if request was successful
        response.raise_for_status()
        
        end_time = time.time()
        print(f"Request completed in {end_time - start_time:.2f} seconds")
        
        # Save the audio to a file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"\nSuccess! Audio saved to {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\nError making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return False

if __name__ == "__main__":
    text_to_speech()