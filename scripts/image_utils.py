import os
from typing import List
import torch
import numpy as np
from PIL import Image, ImageDraw
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from scripts.constants import BLEED, CACHE_DIR, SCALE
from scripts.card_class import Card
   
def __get_card_image_with_fixes__(image_path) -> Image:
    print("-INFO: Fixing card RGB and borders")    
    image = get_rgb_image(image_path)
    image = fix_card_borders(image)
    return image


def bleed_card_borders(image: Image, bleed: int = BLEED)-> Image:
    ##### thrief border color
    # Define the coordinates of the region to extract (x1, y1, x2, y2)
    # Example: top-left (x1, y1) and bottom-right (x2, y2)
    region = (50, 0, 60, 5)  # Modify as per your desired region

    # Crop the image to the region
    cropped_image = image.crop(region)

    # Convert the cropped image to RGB (in case it's in another format)
    cropped_image = cropped_image.convert("RGB")

    # Get the pixel data from the cropped image
    pixels = list(cropped_image.getdata())

    # Calculate the average color of the region
    avg_color = tuple(sum(col) // len(col) for col in zip(*pixels))    
    
    # Create a drawing context
    image_with_bleed = Image.new("RGB", (image.width + 2 * bleed, image.height + 2 * bleed), avg_color)
    image_with_bleed.paste(image, (bleed, bleed))
    return image_with_bleed


def fix_card_borders(image: Image, border_width: int = 20)-> Image:
    ##### thrief border color
    # Define the coordinates of the region to extract (x1, y1, x2, y2)
    # Example: top-left (x1, y1) and bottom-right (x2, y2)
    region = (50, 0, 60, 5)  # Modify as per your desired region

    # Crop the image to the region
    cropped_image = image.crop(region)

    # Convert the cropped image to RGB (in case it's in another format)
    cropped_image = cropped_image.convert("RGB")

    # Get the pixel data from the cropped image
    pixels = list(cropped_image.getdata())

    # Calculate the average color of the region
    avg_color = tuple(sum(col) // len(col) for col in zip(*pixels))    
    
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    # Get image dimensions
    width, height = image.size

    draw.rectangle([(0, 0), (width, height)], outline=avg_color, width=border_width)
    return image




def get_rgb_image(image_path: str) -> Image:
    # try:
    #     img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)  # Load with alpha
    #     if img.shape[-1] == 4:  # Check if alpha channel exists
    #         img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Remove alpha   
    #     return img
    # except:
    # Open with PIL, discard alpha, and fix potential color shifts
    pil_img = Image.open(image_path)
    pil_img.load()
    if pil_img.mode != "RGB":
        # Remove alpha by blending with a white background (to avoid dark edges)
        background = Image.new("RGBA", pil_img.size, (255, 255, 255))
        pil_img_rgb = Image.alpha_composite(background, pil_img).convert('RGB')

        # Convert to NumPy array and switch RGB to BGR for OpenCV compatibility
        #img_np = np.array(pil_img_rgb)[:, :, ::-1]            
        return pil_img_rgb
    return pil_img

def upscale_image(cards: List[Card]):
    # Load the Real-ESRGAN model
    #model_path = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" 
    #model_path = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth" 
    #model_path = "weights\\RealESRGAN_x4plus.pth" 
    #model_path = "weights\\ESRGAN_SRx4_DF2KOST_official-ff704c30.pth" 
    model_path = "weights\\RealESRGAN_x2plus.pth" 
    scale_factor = SCALE

    # Initialize the RealESRGAN model
    device = torch.device('cuda')# if torch.cuda.is_available() else 'cpu')
    #model = RRDBNet(num_in_ch=3, num_out_ch=3)#, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale_factor)
    model.eval()
    model = model.to(device)
    realESRGANer = RealESRGANer(scale=scale_factor, model_path=model_path, model=model, tile=0, tile_pad=10, pre_pad=0, half=False, device=device)
        

    output_folder = os.path.join(CACHE_DIR, "UP")
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for card in cards:
        # Load the RGB image    
        img_path = card.image_path

        # Generate the output file path
        base_filename = os.path.basename(img_path)
        filename, ext = os.path.splitext(base_filename)
        filename = f"{filename}[upscaled]{ext}"
        output_path = os.path.join(output_folder, filename)
        card.image_path = output_path

        if os.path.exists(output_path):
            print(f"-INFO: Image already upscaled: {filename}")
            continue

        img = __get_card_image_with_fixes__(img_path)
         
        if img is None:
            print(f"$Error: Unable to load image at {img_path}")
            continue
        
        # Convert the PIL image to a NumPy array (OpenCV/Real-ESRGAN compatible)
        img_np = np.array(img)

        # Upscale the image using the enhance method
        upscaled_img, _ = realESRGANer.enhance(img_np, outscale=scale_factor)
        
        # Convert back to PIL Image for further processing
        img = Image.fromarray(upscaled_img)

        #resized_img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.BICUBIC)
        
        # Save the upscaled image
        #resized_img.save(output_path)
        img.save(output_path)

        print(f"Upscaled image saved to: {output_path}")

