import json
import os
import re
import hashlib
import argparse
import re
import unicodedata
import requests
import cv2
import os
import torch
import numpy as np
from urllib.parse import urlencode
from PIL import Image, ImageDraw
from colorthief import ColorThief
from reportlab.lib.pagesizes import A4, A3
from reportlab.pdfgen import canvas
from realesrgan.utils import RealESRGANer
from PIL import Image
from basicsr.archs.rrdbnet_arch import RRDBNet


# Constants
OUTPUT_DIR = "magic_cards"
CACHE_DIR = f"{OUTPUT_DIR}\\cache"
DEFAULT_PAGE_SIZE = "A4"
CACHE_FILE = f"{CACHE_DIR}\\cards_fetched.cache"

CARD_LIST_OUTPUT = "printed_card_list_with_tokens.txt"
CARD_SPACING = 10  # Margin between cards
COLLAGE_COLOR = "white"  # Background color for the collage
MARGIN_CM = 0
MARGIN_DPI = int(( MARGIN_CM / 2.54 ) * 300)  # 1cm margin in mm to dpi

PAGE_SIZES = {
    "A4": {"width": 2481 - MARGIN_DPI * 2, "height": 3507 - MARGIN_DPI * 2, "dpi": 300},
    "A3": {"width": 4960 - MARGIN_DPI * 2 , "height": 3508 - MARGIN_DPI * 2, "dpi": 300},
}


# MTG CARD 2,5 inc (6,3 cm) X 3,5 inc (8,8 cm)
CARD_WIDTH = 750  # Card width at 300 DPI
CARD_HEIGHT = 1050  # Card height at 300 DPI

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def sanitize_filename(name):
    """Sanitize a file name to avoid invalid characters and normalize accents."""
    
    # Normalize the string to remove accents and special characters
    name_normalized = unicodedata.normalize('NFKD', name)
    name_without_accents = ''.join([c for c in name_normalized if not unicodedata.combining(c)])
    
    # Replace invalid filename characters with underscores
    sanitized_name = re.sub(r'[<>:"/\\|?* ]', '_', name_without_accents)
    
    return sanitized_name

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)

def get_with_cache(url, params=None):
    cache = load_cache()
    if params:
        url = f"{url}?{urlencode(params)}"    

    key_data = f"{url}".encode('utf-8')
    cache_key = hashlib.md5(key_data).hexdigest()
    
    if cache_key in cache:
        print("Returning cached response")
        return cache[cache_key]


    response = requests.get(url)
    cache[cache_key] = {
        "url": url,
        "params": params,
        "status_code": response.status_code,
        "content": response.json(),
    }
    save_cache(cache)
    return cache[cache_key]

def fetch_card_lang(name, code, number):
    """Fetch card in PT language."""
    base_url_search = "https://api.scryfall.com/cards"
    response_cards = []

    # Step 2: Search for the card in Portuguese    
    response_cards = get_with_cache(f"{base_url_search}/{number}/{code}/pt")
    print(f"-INFO: {response_cards['url']}")

    if response_cards['status_code'] != 200:
        print(f"!WARNING: Fallback to EN: {name}")
        response_cards = get_with_cache(f"{base_url_search}/{number}/{code}")
        print(f"-INFO: {response_cards['url']}")
    
    #elif response_cards.json().get('image_status') == "placeholder":  
    elif response_cards['content'].get('image_status') in ("placeholder", "missing"):
        print(f"!WARNING: No valid Image found. Fallback to EN: {name}")
        response_cards = get_with_cache(f"{base_url_search}/{number}/{code}")
        print(f"-INFO: {response_cards['url']}")

    if response_cards['status_code'] != 200:
        print(f"$ERROR: Failed to fetch card lang: {name}")
        return

    card_data = response_cards['content']
    card = []
    if 'image_uris' in card_data: 
        name = card_data.get("printed_name", card_data["name"])
        card = {
            "name": name,
            "lang":card_data["lang"],
            "image_url": card_data["image_uris"].get("png") or card_data["image_uris"].get("large") or card_data["image_uris"].get("normal"),
            "type": card_data["type_line"].split(" ")[0]
        }
                

    elif 'card_faces' in card_data: 
        for card_face in card_data['card_faces']:
            name = card_face.get("printed_name", card_face["name"])
            card = {
                "name": name,
                "lang":card_face.get("lang", "en"),
                "image_url": card_face["image_uris"].get("png") or card_face["image_uris"].get("large") or card_face["image_uris"].get("normal"),
                "type": card_face["type_line"].split(" ")[0]
            }

    print(f"-INFO: Fetched card details: {card['name']}:{card['lang']}:{card['type']}")    
    return card

    



def fetch_cards(card_names, find_tokens=False, url=""):
    """Fetch card details from Scryfall API."""
    base_url_named = "https://api.scryfall.com/cards/named"   
    mtg_back_url = "https://i.imgur.com/LdOBU1I.jpeg"

    cards = []
    for name in card_names:
        # try get from cache instead of doing a get from scryfall
        if name.lower() == "mtg back":
            cards.append({"name": "MTG Back", "image_url": mtg_back_url})
        else:
            # Step 1: Fetch English card details from named endpoint
            print(f"-INFO: Fetching card {name} info")
            if url:
                response_named = get_with_cache(url)
            else:
                response_named = get_with_cache(base_url_named, params={"fuzzy": name})
            
            print(f"-INFO: {response_named['url']}")
            if response_named['status_code'] != 200:
                print(f"$ERROR: Failed to fetch card details: {name}")
                continue

            card_data = response_named['content']
            code = card_data["collector_number"]
            number = card_data["set"]

            fetched_card = fetch_card_lang(name, code, number)
            cards.append(fetched_card)
            
            # If the card has tokens, attempt to fetch them
            if find_tokens:
                if 'all_parts' in card_data:
                    print(f"-INFO: Fetching card parts")
                    for part in card_data['all_parts']:
                        if part['component'] == 'token' or (part['component'] == 'combo_piece' and part['type_line'] == 'Emblem'):
                            token_name = part.get('name')                            
                            tokens = fetch_cards([token_name], False, part['uri'])
                            if tokens:
                                cards.extend(tokens)
            
            print()
    return cards


def download_images(cards):
    """Download high-definition images for each card."""
    for card in cards:
        image_path = os.path.join(CACHE_DIR, sanitize_filename(f"{card['name']}[{card['lang']}].png"))
        if not os.path.exists(image_path):
            response = requests.get(card['image_url'], stream=True)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            card['image_path'] = image_path
            print(f"-INFO: Downloaded: {card['name']} | {card['lang']}")
            fix_card_image(card)

        else:
            print(f"-INFO: Image already exists: {card['name']}")
            card['image_path'] = image_path
   
def fix_card_image(card):
    print("-INFO: Fixing card RGB and borders")
    image_path = card["image_path"]
    image = get_rgb_image(image_path)
    image = fix_card_borders(image)
    image.save(image_path)


def fix_card_borders(image: Image, border_width = 15)-> Image:
    ##### thrief border color
    # Define the coordinates of the region to extract (x1, y1, x2, y2)
    # Example: top-left (x1, y1) and bottom-right (x2, y2)
    region = (10, 10, 15, 15)  # Modify as per your desired region

    # Crop the image to the region
    cropped_image = image.crop(region)

    # Convert the cropped image to RGB (in case it's in another format)
    cropped_image = cropped_image.convert("RGB")

    # Get the pixel data from the cropped image
    pixels = list(cropped_image.getdata())

    # Calculate the average color of the region
    avg_color = tuple(sum(col) // len(col) for col in zip(*pixels))
    #print(f"Average color in the region: {avg_color}")
    #card['border_color'] = avg_color
    
    # Crop the image to adjust for the border
     # Crop the image to make space for the border
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    # Get image dimensions
    width, height = image.size

    draw.rectangle([(0, 0), (width, height)], outline=avg_color, width=border_width)
    return image




def get_rgb_image(image_path):
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

def upscale_image(cards):
    # Load the Real-ESRGAN model
    #model_path = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" 
    #model_path = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth" 
    #model_path = "weights\\RealESRGAN_x4plus.pth" 
    #model_path = "weights\\ESRGAN_SRx4_DF2KOST_official-ff704c30.pth" 
    model_path = "weights\\RealESRGAN_x2plus.pth" 
    scale_factor = 2

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
        img_path = card['image_path']

        # Generate the output file path
        base_filename = os.path.basename(img_path)
        filename, ext = os.path.splitext(base_filename)
        filename = f"{filename}[upscaled]{ext}"
        output_path = os.path.join(output_folder, filename)
        card['image_path'] = output_path

        if os.path.exists(output_path):
            print(f"-INFO: Image already upscaled: {filename}")
            continue

        img = Image.open(img_path)
        img.load()        
        if img is None:
            print(f"$Error: Unable to load image at {img_path}")
            continue
        
        # Convert the PIL image to a NumPy array (OpenCV/Real-ESRGAN compatible)
        img_np = np.array(img)

        # Upscale the image using the enhance method
        upscaled_img, _ = realESRGANer.enhance(img_np, outscale=scale_factor)
        
        # Convert back to PIL Image for further processing
        img = Image.fromarray(upscaled_img)

        resized_img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.BICUBIC)

        # Save the upscaled image
        resized_img.save(output_path)

        print(f"Upscaled image saved to: {output_path}")




def convert_images_to_pdf(images, output_pdf, page_size):
    """Convert the images into a single PDF file with maximum quality, using PNG directly."""
    # Determine page size (A4 or A3 landscape)
   # Define the page sizes for A4 and A3 (landscape)
    A4_PORTRAIT = A4  # A4 portrait
    A3_LANDSCAPE = (A3[1], A3[0])  # A3 landscape (rotate to landscape)

    if page_size == "A4":
        page_width, page_height = A4_PORTRAIT
    elif page_size == "A3":
        page_width, page_height = A3_LANDSCAPE
    else:
        raise ValueError("Unsupported page size")

    # Create a PDF canvas
    c = canvas.Canvas(output_pdf, pagesize=(page_width, page_height))

    for image_path in images:
        try:
            # Open the PNG image
            img = Image.open(image_path)
            img_width, img_height = img.size

            # Scale the image to fit the page while maintaining aspect ratio
            # Calculate scaling factors
            scale_width = page_width / img_width 
            scale_height = page_height / img_height 
            scale = min(scale_width, scale_height)

            # New dimensions for the image
            new_width = img_width * scale
            new_height = img_height * scale

            # Center the image on the page
            x_offset = (page_width - new_width) / 2
            y_offset = (page_height - new_height) / 2

            # Draw the image on the canvas
            c.drawImage(image_path, x_offset, y_offset, width=new_width, height=new_height)

            c.showPage()  # Add a new page

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    # Add card list if it exists        
    card_list_path = os.path.join(OUTPUT_DIR, CARD_LIST_OUTPUT)  # Use os.path.join for clarity
    if card_list_path and os.path.exists(card_list_path):
        try:
            with open(card_list_path, "r") as f:
                card_list_text = f.read()
            
            c.setFont("Helvetica", 10)
            text_margin = 40  # Margin for text placement
            text_y = page_height - text_margin
            
            for line in card_list_text.splitlines():
                c.drawString(text_margin, text_y, line)
                text_y -= 12  # Move to the next line
            
            c.showPage()  # Add a page for the card list
        except Exception as e:
            print(f"Error adding card list to PDF: {e}")
    # Save the PDF
    c.save()
    print(f"PDF created: {output_pdf}")



def generate_collages(cards, page_size, is_mtg_back=False):
    """Generate multiple PNG collages with card images for the selected page size."""
    page_dims = PAGE_SIZES[page_size]    
    page_width, page_height = page_dims["width"], page_dims["height"]

    # Calculate layout dimensions
    cards_per_row = (page_width + CARD_SPACING) // (CARD_WIDTH + CARD_SPACING)
    rows_per_page = (page_height + CARD_SPACING) // (CARD_HEIGHT + CARD_SPACING)
    cards_per_page = cards_per_row * rows_per_page
    png_files = []  # This will store all the generated PNG files

    for page_idx in range(0, len(cards), cards_per_page):
        page_cards = cards[page_idx:page_idx + cards_per_page]

        # If MTG back is selected, set the collage background to black and remove cut lines
        collage_color =  COLLAGE_COLOR
        collage = Image.new("RGB", (page_width, page_height), collage_color)
        draw = ImageDraw.Draw(collage)

        # Calculate offset to center cards
        total_cards_width = cards_per_row * CARD_WIDTH + (cards_per_row - 1) * CARD_SPACING
        total_cards_height = rows_per_page * CARD_HEIGHT + (rows_per_page - 1) * CARD_SPACING
        offset_x = (page_width - total_cards_width) // 2
        offset_y = (page_height - total_cards_height) // 2


        # If MTG back is not selected, draw cut lines
        if not is_mtg_back:                
            cutline_color = "gray"
            cutline_width = 2
            cutline_offset = 25
            # Draw cut lines ony for normal cards        
            for row in range(rows_per_page + 1):
                y_line = offset_y + row * (CARD_HEIGHT + CARD_SPACING) - (CARD_SPACING // 2) 
                draw.line([(offset_x - cutline_offset, y_line - 1), (offset_x + total_cards_width + cutline_offset , y_line - 1)], fill=cutline_color, width=cutline_width)

            for col in range(cards_per_row + 1):
                x_line = offset_x + col * (CARD_WIDTH + CARD_SPACING) - (CARD_SPACING // 2) 
                draw.line([(x_line - 1, offset_y - cutline_offset), (x_line - 1, offset_y + total_cards_height + cutline_offset)], fill=cutline_color, width=cutline_width)
        else:
            margin_offset = 50
            draw.rectangle(
                [(offset_x - margin_offset , offset_y - margin_offset), 
                (offset_x + total_cards_width + margin_offset , offset_y + total_cards_height  + margin_offset)], 
                outline=page_cards[0]['border_color'], width=150
            )


        for i, card in enumerate(page_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            x_pos = offset_x + col * (CARD_WIDTH + CARD_SPACING) 
            y_pos = offset_y + row * (CARD_HEIGHT + CARD_SPACING) 
            # # If MTG back is selected, don't draw the black background behind cards
            # if not is_mtg_back:
            #     # Draw black background square behind the card
            #     draw.rectangle([x_pos, y_pos, x_pos + CARD_WIDTH, y_pos + CARD_HEIGHT], fill="black")
            try:
                with Image.open(card['image_path']) as img:
                    collage.paste(img, (x_pos, y_pos))
            except Exception as e:
                print(f"Error processing image {card['name']}: {e}")                

        output_png = os.path.join(OUTPUT_DIR, f"magic_cards_collage_page_{page_idx // cards_per_page + 1}.png")
        collage.save(output_png)
        print(f"Collage saved as {output_png}")

        # Add the PNG file to the list
        png_files.append(output_png)

    # Now, convert all PNG files to a single PDF
    pdf_output_file = os.path.join(OUTPUT_DIR, f"magic_cards_collages_{page_size}.pdf")
    convert_images_to_pdf(png_files, pdf_output_file, page_size)

def save_card_list(cards, output_file="card_list.txt"):
    """Save card names and quantities grouped by card types to a file."""
    card_groups = {}
    
    for card in cards:
        card_type = card.get("type", "Unknown")
        card_name = card.get("name", "Unnamed Card")
        card_groups.setdefault(card_type, {})
        card_groups[card_type][card_name] = card_groups[card_type].get(card_name, 0) + 1

    with open(output_file, "w", encoding="utf-8") as f:
        for card_type, card_names in sorted(card_groups.items()):
            f.write(f"=== {card_type} ===\n")
            for name, count in sorted(card_names.items()):
                f.write(f"{count} {name}\n")
            f.write("\n")

    print(f"Card list saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate printable MTG card collages.")
    parser.add_argument("--page-size", choices=PAGE_SIZES.keys(), default=DEFAULT_PAGE_SIZE, help="Page size for the collages (default: A4).")
    parser.add_argument("--mtg-back", action="store_true", help="Generate a page with only MTG back cards.")
    parser.add_argument("--download-tokens", action="store_true", help="Download tokens created by each card.")
    parser.add_argument("--list-all-deck-and-tokens", action="store_true", help="Generate a list with all deck card names and tokens.")

    args = parser.parse_args()

    if args.mtg_back:
        # Generate a full page with only MTG back cards
        print("Generating MTG back cards collage...")
        card_names = ["MTG Back"] * (PAGE_SIZES[args.page_size]["width"] // (CARD_WIDTH ) *
                                    (PAGE_SIZES[args.page_size]["height"] // (CARD_HEIGHT ))) 
        cards = fetch_cards(card_names, False)
    else:
        # Load the card names from the file
        input_file = "card_names.txt"
        if not os.path.exists(input_file):
            print(f"Input file '{input_file}' not found. Please create it and list card names, one per line.")
            return

        with open(input_file, "r") as f:
            card_names = []
            for line in f:
                line = line.strip()
                if line.startswith("#-"):
                   break
                
                if not line or line.startswith("#") or line.startswith("=") :
                    continue
                   
                parts = line.split(maxsplit=1)
                if len(parts) == 2 and parts[0].isdigit():
                    count = int(parts[0])
                    name = parts[1]
                    card_names.extend([name] * count)
                else:
                    card_names.append(line)

        print("Fetching card data...")
        cards = fetch_cards(card_names, args.download_tokens or args.list_all_deck_and_tokens)
    
    
    # save file with all card names and its quantities 
    output_file = os.path.join(OUTPUT_DIR, CARD_LIST_OUTPUT)
    save_card_list(cards, output_file)

    if not args.list_all_deck_and_tokens:
        print("Downloading images...")
        download_images(cards)

        # After downloading images, scale them
        print("Scaling UP images...")
        upscale_image(cards)  # Scale all images in the cache folder

        print("Generating collages...")
        generate_collages(cards, args.page_size, is_mtg_back=args.mtg_back)

if __name__ == "__main__":
    main()