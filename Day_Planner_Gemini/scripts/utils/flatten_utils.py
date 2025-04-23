# scripts/utils/flatten_utils.py

import json

def flatten_attributes(attr_json: dict) -> str:
    if not isinstance(attr_json, dict):
        return ""
    pieces = []
    for k, v in attr_json.items():
        vl = str(v).lower()
        if vl in ("true", "yes"):
            if k.startswith("Ambience_"):
                pieces.append(f"Ambience is {k.split('_')[-1]}")
            elif "BusinessParking" in k:
                pieces.append(f"Has {k.split('_')[-1]} parking")
            else:
                pieces.append(f"{k.replace('_',' ')} available")
        elif vl not in ("false", "no", "null"):
            pieces.append(f"{k.replace('_',' ')} is {v}")
    return ". ".join(pieces)

def hours_to_text(hours_json: dict) -> str:
    if not isinstance(hours_json, dict):
        return ""
    lines = []
    for day, times in hours_json.items():
        if times and times != "0:0-0:0":
            open_t, close_t = times.split("-")
            lines.append(f"Open on {day} from {open_t}:00 to {close_t}:00")
    return ". ".join(lines)

def escape_str(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return s.replace("'", "''").replace("\n", " ").replace("\r", " ")
