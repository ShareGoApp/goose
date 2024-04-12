# path: utils/time.py
from datetime import datetime

def convert_to_unix(timestamp) -> float:
    datetime_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    unix_time = datetime_obj.timestamp()
    return unix_time