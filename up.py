import cv2
import imquality.brisque as brisque
from PIL import Image

def get_image_quality(image_path):
    """Reads an image and returns a quality score (higher is better)."""
    image = Image.open(image_path).convert("L")  # Convert to grayscale for consistency
    score = brisque.score(image)
    
    # Normalize: Lower BRISQUE means better quality, so we invert it
    quality_score = max(0, 100 - score)  # Ensure the score is non-negative

    return quality_score

# Example usage
image_path = "your_image.jpg"  # Change this to your image path
quality = get_image_quality(image_path)
print(f"Image Quality Score: {quality:.2f}")
