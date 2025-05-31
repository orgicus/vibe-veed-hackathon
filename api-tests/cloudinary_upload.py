import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


def upload_image_to_cloudinary(file_path, public_id=None, folder=None):
    """
    Upload an image to Cloudinary
    
    Args:
        file_path (str): Path to the image file
        public_id (str, optional): Custom public ID for the image
        folder (str, optional): Folder to organize images in Cloudinary
    
    Returns:
        dict: Upload result from Cloudinary
    """
    try:
        upload_options = {}

        if public_id:
            upload_options['public_id'] = public_id

        if folder:
            upload_options['folder'] = folder

        # Upload the image
        result = cloudinary.uploader.upload(file_path, **upload_options)

        print(f"Upload successful!")
        print(f"URL: {result['secure_url']}")
        print(f"Public ID: {result['public_id']}")

        return result

    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        return None


def upload_all_images_in_folder(folder_path="api-tests/assets"):
    """
    Upload all images in the specified folder to Cloudinary
    
    Args:
        folder_path (str): Path to the folder containing images
    """
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
    }

    folder = Path(folder_path)

    if not folder.exists():
        print(f"Folder {folder_path} does not exist")
        return

    uploaded_files = []

    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower(
        ) in image_extensions:
            print(f"Uploading {file_path.name}...")

            # Use filename without extension as public_id
            public_id = file_path.stem

            result = upload_image_to_cloudinary(str(file_path),
                                                public_id=public_id,
                                                folder="uploaded_images")

            if result:
                uploaded_files.append(result)

    print(f"\nTotal files uploaded: {len(uploaded_files)}")
    return uploaded_files


if __name__ == "__main__":
    # Upload all images in the assets folder
    upload_all_images_in_folder("assets")
