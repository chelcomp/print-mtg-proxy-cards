import os
import json
from scripts.constants import CACHE_FILE
import hashlib
import requests
from urllib.parse import urlencode
from typing import Dict, Any, Tuple


__response_cache__ = {}
    
class CacheEntry:
    def __init__(self, 
                 url: str, 
                 params: Dict[str, Any], 
                 status_code: int, 
                 content: Any, 
                 border_color: Tuple[int,int,int] = (0, 0, 0), 
                 image_quality_score: int = -1, 
                 image_quality: str = "unknown"):
        self.url = url
        self.params = params
        self.status_code = status_code
        self.content = content
        self.border_color = border_color
        self.image_quality_score = image_quality_score
        self.image_quality = image_quality

    def to_dict(self):
        return {
            "url": self.url,
            "params": self.params,
            "status_code": self.status_code,
            "content": self.content,
            "border_color": self.border_color,
            "image_quality_score": self.image_quality_score,
            "image_quality": self.image_quality            
        }    

def __load_cache__() -> Dict[str, CacheEntry]:
    global response_cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            __response_cache__ = {k: CacheEntry(**v) for k, v in data.items()}
    else:
        response_cache = {}

def __save_cache__():
    global response_cache
    with open(CACHE_FILE, "w") as f:
        json.dump({k: v.to_dict() for k, v in __response_cache__.items()}, f, indent=4)


def generate_cache_key(url: str) -> str:
    key_data = f"{url}".encode('utf-8')
    return hashlib.md5(key_data).hexdigest()


def get_with_cache(url, params=None):
    global response_cache
    if __response_cache__ == {}: 
        __load_cache__()

    if params:
        url = f"{url}?{urlencode(params)}"        

    cache_key = generate_cache_key(url)
    
    if cache_key in __response_cache__:
        print("Returning cached response")
        return __response_cache__[cache_key]

    response = requests.get(url)
    __response_cache__Entry = CacheEntry(
        url=url,
        params=params,
        status_code=response.status_code,
        content=response.json()
    )
    __response_cache__[cache_key] = __response_cache__Entry
    __save_cache__()
    return __response_cache__Entry