import random
import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def has_psw(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def generate_random_numeric_string(length=8):
    return ''.join(random.choice("0123456789") for _ in range(length))

def extract_tournament_id_from_url(url: str) -> str:
    match = re.search(r'/tournaments/([a-f0-9-]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("ID torneo non trovato nella URL.")