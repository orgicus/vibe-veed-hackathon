from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv
import fal_client
import time
import tempfile
import requests
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Configure ElevenLabs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', 'default_voice_id')  # You'll need to set this

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file_path):
    """
    Upload an image to Cloudinary and return the secure URL
    """
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder="uploaded_images"
        )
        print(f"Upload successful! URL: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return None

def remove_background(image_url):
    """
    Remove background from image using fal.ai
    """
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        result = fal_client.subscribe(
            "fal-ai/bria/background/remove",
            arguments={
                "image_url": image_url
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        return result
    except Exception as e:
        print(f"Error removing background: {str(e)}")
        return None

def generate_video_effects(background_removed_url, effects_prompt):
    """
    Generate video with effects using fal-ai pixverse
    """
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        result = fal_client.subscribe(
            "fal-ai/pixverse/v4.5/image-to-video/fast",
            arguments={
                "image_url": background_removed_url,
                "prompt": effects_prompt,
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        return result
    except Exception as e:
        print(f"Error generating video effects: {str(e)}")
        return None

def generate_audio_elevenlabs(message):
    """
    Generate audio from text using ElevenLabs API
    """
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": message,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Save audio to temporary file and upload to Cloudinary for URL access
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(response.content)
                temp_file.flush()
                
                # Upload audio to Cloudinary
                audio_result = cloudinary.uploader.upload(
                    temp_file.name,
                    resource_type="video",  # Use video resource type for audio files
                    folder="generated_audio"
                )
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return audio_result['secure_url']
        else:
            print(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return None

def sync_lips(video_url, audio_url):
    """
    Sync lips using fal.ai lipsync service
    """
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        result = fal_client.subscribe(
            "veed/lipsync",
            arguments={
                "video_url": video_url,
                "audio_url": audio_url
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        return result
    except Exception as e:
        print(f"Error syncing lips: {str(e)}")
        return None

@app.route('/process-video', methods=['POST'])
def process_video():
    """
    Main endpoint to process video with the complete pipeline
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        if 'effects_prompt' not in request.form:
            return jsonify({'error': 'No effects_prompt provided'}), 400
            
        if 'message' not in request.form:
            return jsonify({'error': 'No message provided'}), 400

        file = request.files['image']
        effects_prompt = request.form['effects_prompt']
        message = request.form['message']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            # Step 1: Upload to Cloudinary
            print("Step 1: Uploading to Cloudinary...")
            cloudinary_url = upload_to_cloudinary(temp_file_path)
            if not cloudinary_url:
                return jsonify({'error': 'Failed to upload image to Cloudinary'}), 500

            # Step 2: Remove background
            print("Step 2: Removing background...")
            background_result = remove_background(cloudinary_url)
            if not background_result or 'image' not in background_result:
                return jsonify({'error': 'Failed to remove background'}), 500
            
            background_removed_url = background_result['image']['url']

            # Step 3: Generate video with effects
            print("Step 3: Generating video with effects...")
            video_result = generate_video_effects(background_removed_url, effects_prompt)
            if not video_result or 'video' not in video_result:
                return jsonify({'error': 'Failed to generate video effects'}), 500
            
            video_url = video_result['video']['url']

            # Step 4: Generate audio from message
            print("Step 4: Generating audio...")
            audio_url = generate_audio_elevenlabs(message)
            if not audio_url:
                return jsonify({'error': 'Failed to generate audio'}), 500

            # Step 5: Sync lips
            print("Step 5: Syncing lips...")
            lipsync_result = sync_lips(video_url, audio_url)
            if not lipsync_result or 'video' not in lipsync_result:
                return jsonify({'error': 'Failed to sync lips'}), 500

            final_video_url = lipsync_result['video']['url']

            return jsonify({
                'success': True,
                'final_video_url': final_video_url,
                'processing_steps': {
                    'cloudinary_url': cloudinary_url,
                    'background_removed_url': background_removed_url,
                    'effects_video_url': video_url,
                    'audio_url': audio_url
                }
            })

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        print(f"Unexpected error in process_video: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Video processing server is running'})

@app.route('/', methods=['GET'])
def home():
    """Basic info endpoint"""
    return jsonify({
        'message': 'Video Processing API',
        'endpoints': {
            'process_video': 'POST /process-video - Upload image, effects prompt, and message',
            'health': 'GET /health - Health check'
        },
        'required_params': {
            'image': 'File upload (png, jpg, jpeg, gif, webp)',
            'effects_prompt': 'String - Video effects description',
            'message': 'String - Text to convert to speech'
        }
    })

if __name__ == "__main__":
    # Check required environment variables
    required_env_vars = [
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY', 
        'CLOUDINARY_API_SECRET',
        'ELEVENLABS_API_KEY',
        'FAL_KEY'  # fal_client uses FAL_KEY
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        exit(1)
    
    print("Starting video processing server...")
    print("Required environment variables found")
    print("Server will be available at http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /process-video - Main processing endpoint")
    print("  GET /health - Health check")
    print("  GET / - API info")
    
    app.run(debug=True, host='0.0.0.0', port=9887)