import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv
import fal_client
import time

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

def process_image(image_path):
    """
    Main workflow: Upload to Cloudinary then remove background
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
        print("Result:", result)
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