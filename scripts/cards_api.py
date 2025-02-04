import os
import requests
from typing import List
from scripts.cache_utils import get_with_cache
from scripts.string_utils import sanitize_filename
from scripts.constants import CACHE_DIR
from enum import Enum
from scripts.card_class import Card
from scripts.pagesizeenum_class import PageSizeEnum



def __fetch_card_lang__(name: str, code: str, number: int) -> Card:
    """Fetch card in PT language."""
    base_url_search = "https://api.scryfall.com/cards"
    response_cards = {}

    # Step 2: Search for the card in Portuguese    
    response_cards = get_with_cache(f"{base_url_search}/{number}/{code}/pt")
    print(f"-INFO: {response_cards.url}")

    if response_cards.status_code != 200:
        print(f"!WARNING: Fallback to EN: {name}")
        response_cards = get_with_cache(f"{base_url_search}/{number}/{code}")
        print(f"-INFO: {response_cards.url}")
    
    #elif response_cards.json().get('image_status') == "placeholder":  
    elif response_cards.content.get('image_status') in ("placeholder", "missing"):
        print(f"!WARNING: No valid Image found. Fallback to EN: {name}")
        response_cards = get_with_cache(f"{base_url_search}/{number}/{code}")
        print(f"-INFO: {response_cards.url}")

    if response_cards.status_code != 200:
        print(f"$ERROR: Failed to fetch card lang: {name}")
        return

    card_data = response_cards.content
    card = Card
    if 'image_uris' in card_data: 
        name = card_data.get("printed_name", card_data["name"])
        card = Card(
                name=name,
                lang=card_data["lang"],
                image_url=card_data["image_uris"].get("png") or card_data["image_uris"].get("large") or card_data["image_uris"].get("normal"),
                card_type=card_data["type_line"].split(" ")[0],
                border_color=(0,0,0),
                image_quality=card_data.get("image_status"),
                image_quality_score=-1
            )
    elif 'card_faces' in card_data: 
        for card_face in card_data['card_faces']:
            name = card_face.get("printed_name", card_face["name"])
            card = Card(
                name=name,
                lang=card_face.get("lang", "en"),
                image_url=card_face["image_uris"].get("png") or card_face["image_uris"].get("large") or card_face["image_uris"].get("normal"),
                card_type=card_face["type_line"].split(" ")[0],
                border_color=(0,0,0),
                image_quality=card_data.get("image_status"),
                image_quality_score=-1
            )

    print(f"-INFO: Fetched card details: {repr(card)}")    
    return card

    


def fetch_cards(card_names: List[str], find_tokens: bool = False, url: str = "") -> List[Card]:
    """Fetch card details from Scryfall API."""
    base_url_named = "https://api.scryfall.com/cards/named"   
    mtg_back_url = "https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg/revision/latest?cb=20140813141013"

    cards: List[Card] = []
   
    for name in card_names:
        # try get from cache instead of doing a get from scryfall
        if name.lower() == "mtg back":
            cards.append(Card( name="MTG Back",
                               lang="en",
                               image_url=mtg_back_url,
                               card_type="Token")
                        )     
        else:
            # Step 1: Fetch English card details from named endpoint
            print(f"-INFO: Fetching card {name} info")
            if url:
                response_named = get_with_cache(url)
            else:
                response_named = get_with_cache(base_url_named, params={"fuzzy": name})
            
            print(f"-INFO: {response_named.url}")
            if response_named.status_code != 200:
                print(f"$ERROR: Failed to fetch card details: {name}")
                continue

            card_data = response_named.content
            code = card_data["collector_number"]
            number = card_data["set"]

            fetched_card = __fetch_card_lang__(name, code, number)
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


def download_images(cards: List[Card]):
    """Download high-definition images for each card."""
    for card in cards:
        image_path = os.path.join(CACHE_DIR, sanitize_filename(f"{card.name}[{card.lang}].png"))
        if not os.path.exists(image_path):
            response = requests.get(card.image_url, stream=True)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
            card.image_path = image_path
            print(f"-INFO: Downloaded: {card.name} | {card.lang}")            

        else:
            print(f"-INFO: Image already exists: {card.name}")
            card.image_path = image_path


def getRandomCards(quantity: int) -> List[Card]:
    """Get random cards from Scryfall API."""
    base_url_random = "https://api.scryfall.com/cards/random"
    card_names = []

    while len(card_names) < quantity:
        response_cards = requests.get(base_url_random)
        print(f"-INFO: {response_cards.url}")

        if response_cards.status_code != 200:
            print(f"$ERROR: Failed to fetch random cards")
            return
        card_name = response_cards.json()['name']
        card_names.append(card_name)
        print(f"-INFO: Fetched random card: {card_name}")

    cards = fetch_cards(card_names, False)
    return cards


def fillUpCardPageWithRandomCards(cards: List[Card], page_size: PageSizeEnum):
    page_size_enum = PageSizeEnum
    # Fill up the page with random cards
    if page_size == page_size_enum.A4:
        cards_per_page = 9
    elif page_size == page_size_enum.A3:
        cards_per_page = 18
    
    #perfect lenght
    if len(cards) % cards_per_page == 0:
        return
    
    cards_to_fill = cards_per_page - (len(cards) % cards_per_page)
    random_cards = getRandomCards(cards_to_fill)
    cards.extend(random_cards)
    