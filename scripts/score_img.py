import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

def calculate_image_quality_score(image_path):
    """Calculates a quality score, focusing on fog and noise.

    Args:
        image_path: Path to the input image.

    Returns:
        A quality score (float) between 0 (worst) and 100 (best), or None if an error occurs.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Noise Estimation (using standard deviation in different image patches)
        patch_size = 32  # Adjust patch size as needed
        noise_scores = []
        for y in range(0, gray.shape[0], patch_size):
            for x in range(0, gray.shape[1], patch_size):
                patch = gray[y:y+patch_size, x:x+patch_size]
                noise_std = np.std(patch)
                noise_scores.append(noise_std)

        avg_noise = np.mean(noise_scores)
        noise_score = max(0, 100 - avg_noise * 0.5) # Scale and invert


        # 2. Contrast (related to fog - lower contrast often indicates fog)
        contrast = gray.std() #Standard deviation is a good measure of contrast.
        contrast_score = min(100, contrast * 0.5)  # Scale

        # 3. Blur (less weight since we're focusing on fog/noise)
        laplacian_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(100, laplacian_variance * 0.2)  # Lower weight


        # Combine scores (adjust weights as needed)
        quality_score = (noise_score * 0.5 + contrast_score * 0.3 + blur_score * 0.2)

        return quality_score

    except Exception as e:
        print(f"An error occurred: {e}")
        return None



# # Example usage (same as before):
# # image_path1 = "magic_cards\\cache\\Amarras_Luminosas[pt].png"  # Replace with your image path
# # image_path2 = "magic_cards\\cache\\Adarkar Wastes[en].png"  # Replace with your image path
# # quality1 = calculate_image_quality_score(image_path1)
# # List all images in the directory
# image_dir = "magic_cards\\cache"
# image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
# # Create a list to store image quality scores
# image_scores = []

# # Calculate quality scores for each image and store them in the list
# for image_file in image_files:
#     image_path = os.path.join(image_dir, image_file)
#     quality_score = calculate_image_quality_score(image_path)
#     if quality_score is not None:
#         image_scores.append((image_file, quality_score))

# # Sort the list by quality score in descending order
# image_scores.sort(key=lambda x: x[1], reverse=False)

# # Print the sorted list of image quality scores
# for image_file, quality_score in image_scores:
#     print(f"Quality score: {quality_score:.2f} | {image_file}")
