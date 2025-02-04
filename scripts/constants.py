
from reportlab.lib.pagesizes import A4, A3
from scripts.pagesizeenum_class import PageSizeEnum

# Constants

OUTPUT_DIR = "magic_cards"
CACHE_DIR = f"{OUTPUT_DIR}\\cache"
DEFAULT_PAGE_SIZE = "A4"
CACHE_FILE = f"{CACHE_DIR}\\cards_fetched.cache"

CARD_LIST_OUTPUT = "printed_card_list_with_tokens.txt"
CARD_SPACING = 20  # Margin between cards
COLLAGE_COLOR = "white"  # Background color for the collage
MARGIN_CM = 0
SCALE = 2
DPI = int(300 * SCALE) # 1 x is 300 DPI

MARGIN_DPI = int(( MARGIN_CM / 2.54 ) * DPI )  # 1cm margin in mm to dpi

PAGE_SIZES_DPI_DELTA = (72) 
PAGE_SIZES_DPI = {
    PageSizeEnum.A4: {"width": (int(A4[0] / PAGE_SIZES_DPI_DELTA * DPI)), "height": (int(A4[1] / PAGE_SIZES_DPI_DELTA * DPI))},
    PageSizeEnum.A3: {"width": (int(A3[1] / PAGE_SIZES_DPI_DELTA * DPI)), "height": (int(A4[0] / PAGE_SIZES_DPI_DELTA * DPI))}
}


# MTG CARD 2,5 inc (6,3 cm) X 3,5 inc (8,8 cm)
CARD_WIDTH = int(2.5 * DPI) #750 * SCALE # Card width at 300 DPI
CARD_HEIGHT = int(3.5 * DPI) #1050 * SCALE # Card height at 300 DPI

