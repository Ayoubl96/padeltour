from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Tuple, Union

def ensure_timezone_compatible(dt1: datetime, dt2: datetime) -> Tuple[datetime, datetime]:
    """
    Ensures two datetime objects have compatible timezone info for comparison.
    Either both will be timezone-aware or both will be timezone-naive.
    """
    if dt1 is None or dt2 is None:
        return dt1, dt2
        
    # If one has timezone and the other doesn't, make them compatible
    if dt1.tzinfo is not None and dt2.tzinfo is None:
        # Make dt2 timezone-aware
        dt2 = dt2.replace(tzinfo=dt1.tzinfo)
    elif dt1.tzinfo is None and dt2.tzinfo is not None:
        # Make dt1 timezone-aware
        dt1 = dt1.replace(tzinfo=dt2.tzinfo)
        
    return dt1, dt2

def parse_iso_date(date_str: str, default_timezone: Optional[timezone] = None) -> datetime:
    """
    Parse a date string in ISO format to a datetime object.
    Handles both date-only and datetime formats.
    """
    if not date_str:
        return None
        
    try:
        # Handle 'Z' suffix (UTC timezone)
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
            
        # Try parsing as a full datetime
        dt = datetime.fromisoformat(date_str)
        
        # If timezone info is missing and default_timezone is provided, apply it
        if dt.tzinfo is None and default_timezone is not None:
            dt = dt.replace(tzinfo=default_timezone)
            
        return dt
    except ValueError:
        # Try parsing as date only (YYYY-MM-DD)
        try:
            d = date.fromisoformat(date_str)
            dt = datetime.combine(d, time.min)
            
            # Apply default timezone if provided
            if default_timezone is not None:
                dt = dt.replace(tzinfo=default_timezone)
                
            return dt
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).")

def end_of_day(dt: datetime) -> datetime:
    """Returns the same date at the end of the day (23:59:59.999999)"""
    if dt is None:
        return None
    return datetime.combine(dt.date(), time.max, tzinfo=dt.tzinfo)

def start_of_day(dt: datetime) -> datetime:
    """Returns the same date at the start of the day (00:00:00)"""
    if dt is None:
        return None
    return datetime.combine(dt.date(), time.min, tzinfo=dt.tzinfo)

def date_range(start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
    """
    Normalizes a date range.
    If end_date is not provided, it will be set to the end of start_date's day.
    """
    if not start_date:
        raise ValueError("Start date is required")
        
    # If no end date, use the end of start_date's day
    if not end_date:
        end_date = end_of_day(start_date)
        
    # Ensure they're timezone compatible
    start_date, end_date = ensure_timezone_compatible(start_date, end_date)
    
    return start_date, end_date

def safe_max(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[datetime]:
    """Safely get the maximum of two datetime objects, handling None values"""
    if dt1 is None:
        return dt2
    if dt2 is None:
        return dt1
        
    dt1, dt2 = ensure_timezone_compatible(dt1, dt2)
    return max(dt1, dt2)

def safe_min(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[datetime]:
    """Safely get the minimum of two datetime objects, handling None values"""
    if dt1 is None:
        return dt2
    if dt2 is None:
        return dt1
        
    dt1, dt2 = ensure_timezone_compatible(dt1, dt2)
    return min(dt1, dt2)

def add_time_buffer(dt: datetime, minutes: int) -> datetime:
    """Add a buffer time to a datetime"""
    if dt is None:
        return None
    return dt + timedelta(minutes=minutes) 