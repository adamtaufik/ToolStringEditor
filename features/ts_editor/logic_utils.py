import re

def get_number(value):
    """Extracts a number from a string, e.g., '10 ft' -> 10.0."""
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", value)
        return float(match.group()) if match else 0.0
    except Exception as e:
        print(f"⚠️ ERROR in get_number: {e}")
        return 0.0
