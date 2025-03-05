from reportlab.lib.pagesizes import A4, A3
from reportlab.lib.units import inch
from scripts.pagesizeenum_class import PageSizeEnum

# Constants

OUTPUT_DIR = "magic_cards"
CACHE_DIR = f"{OUTPUT_DIR}\\cache"
DEFAULT_PAGE_SIZE = "A4"
CACHE_FILE = f"{CACHE_DIR}\\cards_fetched.cache"

CARD_LIST_OUTPUT = "printed_card_list_with_tokens.txt"
CARD_SPACING = 1  # Margin between cards
COLLAGE_COLOR = "white"  # Background color for the collage
MARGIN_CM = 0.5
SCALE = 2
DPI = 300 * SCALE # 1 x is 300 DPI

MARGIN_DPI = int(( MARGIN_CM / 2.54 ) * DPI )  # 1cm margin in mm to dpi

PAGE_SIZES_DPI_DELTA = (72) 
PAGE_SIZES_DPI = {
    PageSizeEnum.A4: {"width": (int(round(A4[0] / inch, 1) * DPI) - MARGIN_DPI), "height": (int(round(A4[1] / inch, 1) * DPI)- MARGIN_DPI)},
    PageSizeEnum.A3: {"width": (int(round(A3[1] / inch, 1) * DPI) - MARGIN_DPI), "height": (int(round(A3[0] / inch, 1) * DPI) - MARGIN_DPI)}
}


BLEED = round(0.10 / 2.54 * DPI)  # in cm
# MTG CARD 2,5 inc (6,35 cm) X 3,5 inc (8,8 cm)
CARD_WIDTH = round(6.35 / 2.54 * DPI) #750 * SCALE # Card width at 300 DPI
CARD_HEIGHT = round(8.8 / 2.54 * DPI) #1050 * SCALE # Card height at 300 DPI

