import re
import unicodedata
import html

def remove_emoji(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE
    )

    return emoji_pattern.sub("", text)

def normalize_repetition(text):
    return re.sub(r'(.)\1{2,}', r'\1\1', text)

def preprocess_text(text):

    text = str(text)

    text = text.strip().lower()

    text = re.sub(r"http\S+|www\.\S+", " ", text)

    text = re.sub(r"@\w+", " ", text)

    text = remove_emoji(text)

    text = unicodedata.normalize(
        "NFKD",
        text
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "utf-8",
        "ignore"
    )

    text = re.sub(r"[^a-zA-Z0-9\s.,:;()/&-]"," ",text)

    text = re.sub(r"doi:\s*\S+"," ",text,flags=re.IGNORECASE)

    text = normalize_repetition(text)

    text = html.unescape(text)

    text = re.sub(r"\s+", " ", text).strip()

    return text