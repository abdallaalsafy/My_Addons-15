# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import _

def fnc_editstring(slf):
    """
    Edit Arabic string by replacing specific characters and formatting.
    
    Args:
        slf: Input string to be edited
    
    Returns:
        str: Edited string with normalized Arabic characters
    """
    if slf:
        xdctnry = {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ي ": "ى "}
        vrb = str(slf)
        vrb = vrb + " "
        for xx in xdctnry:
            vrb = vrb.replace(xx, xdctnry[xx])
        xlist = vrb.split(" ")
        vrb = ""
        for x in xlist:
            if x == "":
                continue
            vrb = vrb + x
            if (x != "ابو") and (x != "عبد"):
                vrb = vrb + " "
        return vrb.strip().lower()
    return ""


def get_birth_date_from_national_id(national_id: str) -> date:
    """
    Extract birth date from Egyptian national ID.
    
    Args:
        national_id: 14-digit Egyptian national ID number
        
    Returns:
        date: Birth date extracted from the ID
        
    Raises:
        ValueError: If the ID format is invalid
    """
    # Extract date components
    day = int(national_id[5:7])
    month = int(national_id[3:5])
    
    century_code = national_id[0]
    year_part = int(national_id[1:3])
    
    # Determine century based on first digit
    if century_code == "2":
        year = 1900 + year_part
    elif century_code == "3":
        year = 2000 + year_part
    else:
        year = 2100 + year_part

    return date(year, month, day)


def get_detailed_age(national_id: str = None, birth_date: date = None):
    """
    Calculate detailed age in years, months, and days from Egyptian national ID or birth date.
    
    Args:
        national_id: 14-digit Egyptian national ID number (optional)
        birth_date: Birth date (optional)
        
    Returns:
        str: Age formatted as "X years, Y months, Z days" with translation support
        
    Note:
        If both parameters are provided, national ID takes priority.
        If neither is provided, returns "Not specified".
    """
    # Try to get birth date from national ID first
    if national_id and not is_invalid_national_id(national_id):
        try:
            birth_date = get_birth_date_from_national_id(national_id)
        except:
            pass
    
    # If no valid birth date, return not specified
    if not birth_date:
        return _("Not specified")
    
    today = date.today()
    
    # Calculate years
    years = today.year - birth_date.year
    
    # Calculate months and days
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    
    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
        months += 12
    
    # Adjust days if negative
    if days < 0:
        months -= 1
        # Get days in previous month
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        # Calculate days in previous month
        import calendar
        days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]
        days += days_in_prev_month
    
    # Build age string with translatable terms
    age_parts = []
    if years > 0:
        age_parts.append(f"{years} {_('year') if years == 1 else _('years')}")
    if months > 0:
        age_parts.append(f"{months} {_('month') if months == 1 else _('months')}")
    if days > 0:
        age_parts.append(f"{days} {_('day') if days == 1 else _('days')}")
    
    return ", ".join(age_parts) if age_parts else _("0 days"),years,months,days


def get_gender_from_national_id(national_id: str) -> str:
    """
    Extract gender from Egyptian national ID.
    
    Args:
        national_id: 14-digit Egyptian national ID number
        
    Returns:
        str: Gender in Arabic ("m" for male, "f" for female)
    """
    digit = int(national_id[12])
    return "f" if digit % 2 == 0 else "m"


def is_invalid_national_id(national_id: str) -> bool:
    """
    Validate Egyptian national ID format and logic.
    
    Args:
        national_id: 14-digit Egyptian national ID number
        
    Returns:
        bool: True if ID is invalid, False if valid
    """
    # Check length and null
    if not national_id or len(national_id) != 14:
        return True

    # Check century code (must be 2 or 3 for valid IDs)
    if national_id[0] not in ["2", "3"]:
        return True

    # Extract date components
    month = int(national_id[3:5])
    day = int(national_id[5:7])

    # Validate month range
    if month < 1 or month > 12:
        return True

    # Validate day range
    if day < 1 or day > 31:
        return True

    # Check last digit (should not be 0)
    if int(national_id[13]) == 0:
        return True

    # Check months with 31 days
    full_months = [1, 3, 5, 7, 8, 10, 12]
    if day == 31 and month not in full_months:
        return True

    # February validation
    if month == 2:
        year = int(("19" if national_id[0] == "2" else "20") + national_id[1:3])

        # Leap year check
        is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

        if (is_leap and day > 29) or (not is_leap and day > 28):
            return True

    # Check for future date
    try:
        birth_date = get_birth_date_from_national_id(national_id)
        if birth_date > date.today():
            return True
    except:
        return True

    return False
