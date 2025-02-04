from typing import List, Tuple

class Card:
    def __init__(self, name: str, 
                 lang: str, 
                 image_url: str, 
                 card_type: str, 
                 border_color: Tuple[int,int,int] = (0, 0, 0), 
                 image_quality: str = "unknown",
                 image_quality_score: int = -1):
        self.name = name
        self.lang = lang
        self.image_url = image_url
        self.card_type = card_type
        self.border_color = border_color
        self.image_quality_score = image_quality_score
        self.image_quality = image_quality



    def __repr__(self):
        return f"Card(name={self.name}, lang={self.lang}, image_url={self.image_url}, card_type={self.card_type}, border_color={self.border_color}, image_quality={self.image_quality}, image_quality_score={self.image_quality_score})"
    def __str__(self):
        return f"Card: {self.name} ({self.lang}) - {self.card_type}"
