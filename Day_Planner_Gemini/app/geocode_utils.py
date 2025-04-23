# app/geocode_utils.py

import re
import spacy
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Load spaCy model and geolocator once
nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="yelp-locator")

def resolve_state(token: str) -> str:
    """
    Normalize a state token:
    - If two letters, uppercase (e.g. 'fl' → 'FL')
    - Else title‑case (e.g. 'florida' → 'Florida')
    """
    t = str(token).strip()
    if len(t) == 2:
        return t.upper()
    return t.title()

def extract_city_state(text: str) -> tuple[str,str]:
    """
    Extract (city, state) from free‑form text.
    1) Title‑case the input so spaCy recognizes GPEs.
    2) If spaCy finds ≥2 GPEs, take the last two.
    3) If it finds exactly 1, split on spaces (city vs state).
    4) Else fall back to regex: “in City, ST” or “in City ST”.
    """
    title_text = str(text).title()
    doc        = nlp(title_text)
    gpes       = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    if len(gpes) >= 2:
        city, state = gpes[-2], gpes[-1]
        return city, resolve_state(state)

    if len(gpes) == 1:
        parts = gpes[0].split()
        if len(parts) >= 2:
            city = " ".join(parts[:-1])
            state = parts[-1]
            return city, resolve_state(state)
        return gpes[0], ""

    # Regex fallback: look for “in <City> <State>”
    m = re.search(r"in\s+([A-Za-z\s]+?)(?:,|\s)\s*([A-Za-z]{2,})", title_text, re.I)
    if m:
        city  = m.group(1).strip().title()
        state = m.group(2).strip().title()
        return city, resolve_state(state)

    return "", ""

def get_coordinates(city: str, state: str) -> tuple[float,float] | None:
    """Geocode “City, State” to (lat, lon), or return None if not found."""
    if not city:
        return None
    query = f"{city}, {state}" if state else city
    loc   = geolocator.geocode(query)
    return (loc.latitude, loc.longitude) if loc else None

def filter_by_radius(df, center: tuple[float,float], miles: float = 30):
    """
    Keep only those rows in df whose LATITUDE/LONGITUDE lie within `miles`
    of `center`. If center is None, returns df unchanged.
    """
    if not center or {"LATITUDE","LONGITUDE"} - set(df.columns):
        return df
    return df[df.apply(
        lambda r: geodesic(center, (r["LATITUDE"], r["LONGITUDE"])) <= miles,
        axis=1
    )]
