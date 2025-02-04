import unicodedata
import re


def sanitize_filename(name: str) -> str:
    """Sanitize a file name to avoid invalid characters and normalize accents."""
    
    # Normalize the string to remove accents and special characters
    name_normalized = unicodedata.normalize('NFKD', name)
    name_without_accents = ''.join([c for c in name_normalized if not unicodedata.combining(c)])
    
    # Replace invalid filename characters with underscores
    sanitized_name = re.sub(r'[<>:"\'/\\|?* ]+', '_', name_without_accents)
    
    return sanitized_name