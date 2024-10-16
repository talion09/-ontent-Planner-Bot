import hashlib
import re
from datetime import datetime, timedelta


def is_telegram_channel_link(text: str) -> bool:
    pattern = re.compile(r"https?://(t\.me|telegram\.me)/[^\s]+")
    return bool(pattern.match(text))

def is_private_channel_link(text:str) -> bool:
    if 'https://t.me/+' in text:
        return True
    return False

def extract_channel_username(url: str) -> str:
    if url.startswith("https://t.me/"):
        return "@" + url.split("/")[-1]


def days_in_current_month():
    now = datetime.utcnow()

    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    last_day_of_current_month = next_month - timedelta(days=1)

    return last_day_of_current_month.day


def generate_sign(currency: str,paysystem:str,oper_id:str,amount:str, pass1:str):
    string_to_sign = f"{currency}-{paysystem}-{oper_id}-{amount}-{pass1}"
    md5_hash = hashlib.md5(string_to_sign.encode()).hexdigest()
    return md5_hash


def count_characters(s):
    return len(s.encode('utf-16-le')) // 2