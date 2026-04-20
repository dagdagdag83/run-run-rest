from enum import Enum

class DistanceCategory(str, Enum):
    ONE_K = "1k"
    ONE_MILE = "1mi"
    THREE_K = "3k"
    FIVE_K = "5k"
    TEN_K = "10k"
    FIFTEEN_K = "15k"
    TEN_MILE = "10mi"
    HALF_MARATHON = "Half-Marathon"
    MARATHON = "Marathon"
    FIFTY_K = "50k"

def parse_time_to_seconds(time_str: str) -> int:
    """
    Parses a time string like '24:30' or '1:45:15' into total seconds.
    """
    if not time_str:
        raise ValueError("time_str cannot be empty")
        
    parts = time_str.strip().split(':')
    
    try:
        if len(parts) == 3:
            # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            # Just seconds if it's an integer
            return int(parts[0])
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    except ValueError as e:
        raise ValueError(f"Invalid time format or non-integer parsing error in: {time_str}") from e
