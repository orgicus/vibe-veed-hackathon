import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv
import fal_client
import time
import requests

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

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

def save_processed_image(image_url, original_filename):
    """
    Save the processed image to the processed_images folder
    """
    try:
        # Create processed_images directory if it doesn't exist
        processed_dir = Path("processed_images")
        processed_dir.mkdir(exist_ok=True)
        
        # Generate new filename
        filename = f"processed_{original_filename}"
        output_path = processed_dir / filename
        
        # Download and save the image
        response = requests.get(image_url)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        print(f"Processed image saved to: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"Error saving processed image: {str(e)}")
        return None

def process_image(image_path):
    """
    Main workflow: Upload to Cloudinary then remove background
    
        1. service to upload a single user image  
            1. use cloudinary script, store the resuting URL
            2. upload the result URL to fal background removal
            3. store output video somewhere
        2. service to take in effects prompt:
            - input = backround removal result
            - prompt (can contain effects)
        3. service to take in promot to generate audio
            - use elevenlabs api script
            - store result
        4. service to put it together
            - video effects .mp4 file
            - eleven labs .mp3 file
            - send to fal for lipsync
            - store result
        5. when done notify/email URL

    """
    # Step 1: Upload to Cloudinary
    cloudinary_url = upload_to_cloudinary(image_path)
    if not cloudinary_url:
        print("Failed to upload to Cloudinary")
        return

    # Step 2: Remove background using the Cloudinary URL
    print("\nRemoving background...")
    result = remove_background(cloudinary_url)
    if result:
        print("\nBackground removal completed!")
        
        # Step 3: Save the processed image
        if 'image' in result:
            saved_path = save_processed_image(
                result['image'],
                Path(image_path).name
            )
            if saved_path:
                print(f"Final processed image saved at: {saved_path}")
        else:
            print("No processed image found in result")
    else:
        print("Failed to remove background")

if __name__ == "__main__":
    # Process all images in the assets folder
    assets_dir = Path("assets")
    if not assets_dir.exists():
        print(f"Assets directory not found at {assets_dir}")
        exit(1)

    for image_file in assets_dir.glob("*.jpg"):
        print(f"\nProcessing {image_file.name}...")
        process_image(str(image_file))
        # Add a small delay between processing multiple images
        time.sleep(1) 