from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo


def convert_utc_to_local(utc_input, local_timezone_str="America/New_York"):
    """
    Converts a UTC datetime, date, or time to local time using zoneinfo.

    Parameters:
        utc_input (datetime | date | time): The UTC input to convert.
        local_timezone_str (str): IANA timezone string, e.g., 'America/New_York'.

    Returns:
        datetime | time: Localized datetime or time object.
    """
    local_tz = ZoneInfo(local_timezone_str)

    if isinstance(utc_input, datetime):
        # Make sure it's timezone-aware
        if utc_input.tzinfo is None:
            utc_input = utc_input.replace(tzinfo=timezone.utc)
        return utc_input.astimezone(local_tz)

    elif isinstance(utc_input, date):
        utc_dt = datetime.combine(utc_input, time.min, tzinfo=timezone.utc)
        return utc_dt.astimezone(local_tz)

    elif isinstance(utc_input, time):
        # Combine with today's date to convert time properly
        today_utc = datetime.now(timezone.utc).date()
        utc_dt = datetime.combine(today_utc, utc_input, tzinfo=timezone.utc)
        return utc_dt.astimezone(local_tz).time()

    else:
        raise ValueError("Input must be a datetime, date, or time object.")
