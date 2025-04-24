import random
import re

def generate_random_numeric_string(length=8):
    return ''.join(random.choice("0123456789") for _ in range(length))

def extract_tournament_id_from_url(url: str) -> str:
    match = re.search(r'/tournaments/([a-f0-9-]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Tournament ID not found in URL.") 