from typing import List
from reportlab.lib.pagesizes import A4, A3
from reportlab.pdfgen import canvas
from PIL import Image
from scripts.constants import MARGIN_DPI, SCALE
from scripts.pagesizeenum_class import PageSizeEnum

def convert_images_to_pdf(images: List[str], output_pdf: str, page_size: PageSizeEnum):
    """
    Converts a list of images to a PDF file with specified page size.
    Args:
        images (list): List of file paths to the images to be converted.
        output_pdf (str): File path for the output PDF.
        page_size (str): Page size for the PDF. Supported values are "A4" and "A3".
    Raises:
        ValueError: If an unsupported page size is provided.
        Exception: If there is an error processing an image or adding the card list.
    Returns:
        None
    """
    
    # Determine page size (A4 or A3 landscape)
    # Define the page sizes for A4 and A3 (landscape)
    A4_PORTRAIT = A4  # A4 portrait
    A3_LANDSCAPE = (A3[1], A3[0])  # A3 landscape (rotate to landscape)

    if page_size == PageSizeEnum.A4:
        page_width, page_height = A4_PORTRAIT
    elif page_size == PageSizeEnum.A3:
        page_width, page_height = A3_LANDSCAPE

    page_width *= SCALE
    page_height *= SCALE
    
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
            c.drawImage(image_path, x_offset, y_offset, width=new_width, height=new_height, preserveAspectRatio=True)
            #c.drawImage(image_path, x_offset, y_offset, page_width - x_offset, page_height - x_offset, preserveAspectRatio=True)
            c.showPage()  # Add a new page

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    # Add card list if it exists        
    # card_list_path = os.path.join(OUTPUT_DIR, CARD_LIST_OUTPUT)  # Use os.path.join for clarity
    # if card_list_path and os.path.exists(card_list_path):
    #     try:
    #         with open(card_list_path, "r") as f:
    #             card_list_text = f.read()
            
    #         c.setFont("Helvetica", 10)
    #         text_margin = 40  # Margin for text placement
    #         text_y = page_height - text_margin
            
    #         for line in card_list_text.splitlines():
    #             c.drawString(text_margin, text_y, line)
    #             text_y -= 12  # Move to the next line
            
    #         c.showPage()  # Add a page for the card list
    #     except Exception as e:
    #         print(f"Error adding card list to PDF: {e}")

    # Save the PDF
    c.save()
    print(f"PDF created: {output_pdf}")        
    