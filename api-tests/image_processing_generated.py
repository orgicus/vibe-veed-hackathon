import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv
import fal_client
import time
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

class ProcessingResult:
    def __init__(self, image_name):
        self.image_name = image_name
        self.timestamp = datetime.now().isoformat()
        self.cloudinary_url = None
        self.background_removed_url = None
        self.effects_video_url = None
        self.audio_url = None
        self.final_video_url = None
        self.status = "pending"
        self.error = None

    def to_dict(self):
        return {
            "image_name": self.image_name,
            "timestamp": self.timestamp,
            "cloudinary_url": self.cloudinary_url,
            "background_removed_url": self.background_removed_url,
            "effects_video_url": self.effects_video_url,
            "audio_url": self.audio_url,
            "final_video_url": self.final_video_url,
            "status": self.status,
            "error": self.error
        }

def save_processing_result(result, output_dir="processing_results"):
    """Save processing result to a JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{result.image_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    return filepath

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
        print(f"Calling fal.ai API with image URL: {image_url}")
        result = fal_client.subscribe(
            "fal-ai/bria/background/remove",
            arguments={
                "image_url": image_url
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        print(f"Fal.ai API response: {result}")
        if result and isinstance(result, dict) and 'image' in result and 'url' in result['image']:
            return {'url': result['image']['url']}
        else:
            print(f"Unexpected response format from fal.ai: {result}")
            return None
    except Exception as e:
        print(f"Error removing background: {str(e)}")
        return None

def apply_effects(image_url, effects_prompt):
    """Apply effects to the background-removed image"""
    try:
        # TODO: Implement effects application using appropriate API
        # This is a placeholder for the effects application step
        return None
    except Exception as e:
        print(f"Error applying effects: {str(e)}")
        return None

def generate_audio(prompt):
    """Generate audio using ElevenLabs API"""
    try:
        # TODO: Implement ElevenLabs API integration
        # This is a placeholder for the audio generation step
        return None
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return None

def create_final_video(video_url, audio_url):
    """Combine video and audio using fal.ai lipsync"""
    try:
        # TODO: Implement video combination using fal.ai lipsync
        # This is a placeholder for the final video creation step
        return None
    except Exception as e:
        print(f"Error creating final video: {str(e)}")
        return None

def process_image(image_path, effects_prompt=None, audio_prompt=None):
    """
    Main workflow: Process image through the complete pipeline
    """
    result = ProcessingResult(Path(image_path).stem)
    
    try:
        # Step 1: Upload to Cloudinary
        print("\nStep 1: Uploading to Cloudinary...")
        cloudinary_url = upload_to_cloudinary(image_path)
        if not cloudinary_url:
            raise Exception("Failed to upload to Cloudinary")
        result.cloudinary_url = cloudinary_url

        # Step 2: Remove background
        print("\nStep 2: Removing background...")
        bg_removed = remove_background(cloudinary_url)
        if not bg_removed:
            raise Exception("Failed to remove background")
        result.background_removed_url = bg_removed.get('url')

        # Step 3: Apply effects (if prompt provided)
        if effects_prompt:
            print("\nStep 3: Applying effects...")
            effects_result = apply_effects(result.background_removed_url, effects_prompt)
            if effects_result:
                result.effects_video_url = effects_result

        # Step 4: Generate audio (if prompt provided)
        if audio_prompt:
            print("\nStep 4: Generating audio...")
            audio_result = generate_audio(audio_prompt)
            if audio_result:
                result.audio_url = audio_result

        # Step 5: Create final video (if both video and audio are available)
        if result.effects_video_url and result.audio_url:
            print("\nStep 5: Creating final video...")
            final_video = create_final_video(result.effects_video_url, result.audio_url)
            if final_video:
                result.final_video_url = final_video

        result.status = "completed"
        
    except Exception as e:
        result.status = "failed"
        result.error = str(e)
        print(f"Error in processing pipeline: {str(e)}")
    
    # Save processing result
    result_file = save_processing_result(result)
    print(f"\nProcessing result saved to: {result_file}")
    
    return result

if __name__ == "__main__":
    # Process all images in the assets folder
    script_dir = Path(__file__).parent
    assets_dir = script_dir / "assets"
    if not assets_dir.exists():
        print(f"Assets directory not found at {assets_dir}")
        exit(1)

    # Example prompts (these should be configurable)
    effects_prompt = "Add a subtle zoom effect and smooth transitions"
    audio_prompt = "Generate a cheerful background music"

    for image_file in assets_dir.glob("*.jpg"):
        print(f"\nProcessing {image_file.name}...")
        result = process_image(
            str(image_file),
            effects_prompt=effects_prompt,
            audio_prompt=audio_prompt
        )
        # Add a small delay between processing multiple images
        time.sleep(1) 