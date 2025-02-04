import json
import os
import re
import hashlib
import argparse
import re
from typing import List
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
import time
from scripts.score_img import calculate_image_quality_score
from scripts.string_utils import sanitize_filename
from scripts.cache_utils import get_with_cache
from scripts.constants import CACHE_DIR, OUTPUT_DIR, DEFAULT_PAGE_SIZE, PAGE_SIZES_DPI, CARD_WIDTH, CARD_HEIGHT, CARD_SPACING, SCALE, COLLAGE_COLOR, CARD_LIST_OUTPUT
from scripts.image_utils import upscale_image
from scripts.cards_api import fetch_cards, download_images, fillUpCardPageWithRandomCards
from scripts.pdf_utils import convert_images_to_pdf
from scripts.card_class import Card
from scripts.pagesizeenum_class import PageSizeEnum

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_collages(cards: List[Card], page_size: PageSizeEnum, is_mtg_back: bool=False):
    """Generate multiple PNG collages with card images for the selected page size."""
    page_dims = PAGE_SIZES_DPI[page_size]    
    page_width, page_height = page_dims["width"], page_dims["height"]

    # Calculate layout dimensions
    cards_per_row = (page_width) // (CARD_WIDTH + CARD_SPACING)
    rows_per_page = (page_height) // (CARD_HEIGHT + CARD_SPACING)
    cards_per_page = int(cards_per_row * rows_per_page)
    png_files = []  # This will store all the generated PNG files

    for page_idx in range(0, len(cards), cards_per_page):
        page_cards = cards[page_idx:page_idx + cards_per_page]

        # Calculate offset to center cards
        total_cards_width = cards_per_row * CARD_WIDTH + (cards_per_row - 1) * CARD_SPACING
        total_cards_height = rows_per_page * CARD_HEIGHT + (rows_per_page - 1) * CARD_SPACING
      
        offset_x = CARD_SPACING * 2 #(page_width - total_cards_width) // 2 
        offset_y = CARD_SPACING * 2 #(page_height - total_cards_height) // 2 // 2 # margem superior

        # If MTG back is selected, set the collage background to black and remove cut lines
        collage_color =  COLLAGE_COLOR
        collage = Image.new("RGB", (total_cards_width + offset_x, total_cards_height + offset_y), collage_color)
        draw = ImageDraw.Draw(collage)


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
                fill=(17, 14, 3),  width=150
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
                with Image.open(card.image_path) as img:
                    collage.paste(img, (x_pos, y_pos))
            except Exception as e:
                print(f"Error processing image {card.name}: {e}")                

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
        card_type = card.card_type
        card_name = card.name
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
    parser.add_argument("--page-size", choices=[e.name for e in PageSizeEnum], default=DEFAULT_PAGE_SIZE, help="Page size for the collages (default: A4).")
    parser.add_argument("--mtg-back", action="store_true", help="Generate a page with only MTG back cards.")
    parser.add_argument("--download-tokens", action="store_true", help="Download tokens created by each card.")
    parser.add_argument("--list-all-deck-and-tokens", action="store_true", help="Generate a list with all deck card names and tokens.")
    parser.add_argument("--include-basic-lands", action="store_true", help="Include basic lands in the collages.")

    args = parser.parse_args()
    args.page_size = PageSizeEnum[args.page_size]

    if args.mtg_back:
        # Generate a full page with only MTG back cards
        print("Generating MTG back cards collage...")
        card_names = ["MTG Back"] * (PAGE_SIZES_DPI[args.page_size]["width"] // (CARD_WIDTH ) *
                                    (PAGE_SIZES_DPI[args.page_size]["height"] // (CARD_HEIGHT ))) 
        cards = fetch_cards(card_names, False)
    else:
        # Load the card names from the file
        input_file = "card_names.txt"
        if not os.path.exists(input_file):
            print(f"Input file '{input_file}' not found. Please create it and list card names, one per line.")
            return

        with open(input_file, "r") as f:
            card_names: list[str] = []
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

        if not args.include_basic_lands:
            card_names = [name for name in card_names if name not in ["Plains", "Island", "Swamp", "Mountain", "Forest"]]

        print("Fetching card data...")
        cards = fetch_cards(card_names, args.download_tokens or args.list_all_deck_and_tokens)
        cards.sort(key=lambda card: (card.card_type, card.name))
    
    
    # save file with all card names and its quantities 
    output_file = os.path.join(OUTPUT_DIR, CARD_LIST_OUTPUT)
    save_card_list(cards, output_file)

    if not args.list_all_deck_and_tokens:
        fillUpCardPageWithRandomCards(cards, args.page_size)

        print("Downloading images...")
        download_images(cards)

        # After downloading images, scale them
        print("Scaling UP images...")
        upscale_image(cards)  # Scale all images in the cache folder

        print("Generating collages...")
        generate_collages(cards, args.page_size, is_mtg_back=args.mtg_back)

if __name__ == "__main__":
    main()