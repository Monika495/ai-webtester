"""
Random Data Generator for NovaQA
Generates realistic random data for testing signup/login forms
"""
import random
import string
from datetime import datetime, timedelta

# First Names Pool
FIRST_NAMES_MALE = [
    "John", "Michael", "David", "James", "Robert", "William", "Richard", "Thomas",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward",
    "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas"
]

FIRST_NAMES_FEMALE = [
    "Mary", "Jennifer", "Linda", "Patricia", "Elizabeth", "Susan", "Jessica",
    "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley",
    "Dorothy", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda",
    "Melissa", "Deborah", "Stephanie", "Rebecca", "Laura", "Sharon", "Cynthia"
]

# Last Names Pool
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green"
]

# Email Domains
EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.com",
    "protonmail.com", "icloud.com", "aol.com", "zoho.com", "test.com"
]

# Password Components
PASSWORD_WORDS = [
    "Secure", "Strong", "Power", "Super", "Safe", "Fast", "Quick", "Easy",
    "Happy", "Lucky", "Magic", "Cool", "Smart", "Brave", "Swift", "Mighty"
]

def get_random_first_name(gender=None):
    """Get random first name"""
    if gender and gender.lower() == "male":
        return random.choice(FIRST_NAMES_MALE)
    elif gender and gender.lower() == "female":
        return random.choice(FIRST_NAMES_FEMALE)
    else:
        return random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)

def get_random_last_name():
    """Get random last name"""
    return random.choice(LAST_NAMES)

def get_random_full_name(gender=None):
    """Get random full name"""
    first = get_random_first_name(gender)
    last = get_random_last_name()
    return f"{first} {last}"

def get_random_username(base_name=None):
    """Get random username"""
    if not base_name:
        first = get_random_first_name().lower()
        last = get_random_last_name().lower()
        base_name = f"{first}{last}"
    
    number = random.randint(10, 9999)
    return f"{base_name}{number}"

def get_random_email(username=None):
    """Get random email"""
    if not username:
        first = get_random_first_name().lower()
        last = get_random_last_name().lower()
        username = f"{first}.{last}{random.randint(10, 999)}"
    
    domain = random.choice(EMAIL_DOMAINS)
    return f"{username}@{domain}"

def get_random_password(length=10):
    """Get random secure password"""
    word = random.choice(PASSWORD_WORDS)
    number = random.randint(100, 9999)
    special = random.choice(['!', '@', '#', '$', '%'])
    
    return f"{word}{number}{special}"

def get_random_phone():
    """Get random phone number"""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1-{area}-{prefix}-{line}"

def get_random_birth_date():
    """Get random birth date (18-60 years old)"""
    today = datetime.now()
    min_age = 18
    max_age = 60
    
    years_ago = random.randint(min_age, max_age)
    birth_year = today.year - years_ago
    birth_month = random.randint(1, 12)
    
    # Handle days based on month
    if birth_month in [4, 6, 9, 11]:
        birth_day = random.randint(1, 30)
    elif birth_month == 2:
        birth_day = random.randint(1, 28)
    else:
        birth_day = random.randint(1, 31)
    
    return {
        "day": str(birth_day),
        "month": str(birth_month),
        "year": str(birth_year),
        "full": f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    }

def get_random_gender():
    """Get random gender"""
    return random.choice(["male", "female"])

def get_random_address():
    """Get random address"""
    street_num = random.randint(100, 9999)
    streets = ["Main St", "Oak Ave", "Maple Dr", "Park Rd", "Cedar Ln", "Elm St"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "MI", "GA"]
    
    return {
        "street": f"{street_num} {random.choice(streets)}",
        "city": random.choice(cities),
        "state": random.choice(states),
        "zip": str(random.randint(10000, 99999))
    }

def get_random_profile():
    """Get complete random profile"""
    gender = get_random_gender()
    first_name = get_random_first_name(gender)
    last_name = get_random_last_name()
    username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 999)}"
    birth = get_random_birth_date()
    address = get_random_address()
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "name": f"{first_name} {last_name}",
        "username": username,
        "email": f"{username}@{random.choice(EMAIL_DOMAINS)}",
        "password": get_random_password(),
        "phone": get_random_phone(),
        "gender": gender,
        "birth_day": birth["day"],
        "birth_month": birth["month"],
        "birth_year": birth["year"],
        "birth_date": birth["full"],
        "address": address["street"],
        "city": address["city"],
        "state": address["state"],
        "zip": address["zip"]
    }

def get_random_data(field_name):
    """
    Get random data for a specific field
    
    Supported fields:
    - first_name, last_name, name
    - username
    - email
    - password
    - phone
    - gender
    - birth_day, birth_month, birth_year, birth_date
    - address, city, state, zip
    """
    field_name = field_name.lower()
    
    if field_name == "first_name":
        return get_random_first_name()
    elif field_name == "last_name":
        return get_random_last_name()
    elif field_name == "name":
        return get_random_full_name()
    elif field_name == "username":
        return get_random_username()
    elif field_name == "email":
        return get_random_email()
    elif field_name == "password":
        return get_random_password()
    elif field_name == "phone":
        return get_random_phone()
    elif field_name == "gender":
        return get_random_gender()
    elif field_name in ["birth_day", "birthday_day"]:
        return get_random_birth_date()["day"]
    elif field_name in ["birth_month", "birthday_month"]:
        return get_random_birth_date()["month"]
    elif field_name in ["birth_year", "birthday_year"]:
        return get_random_birth_date()["year"]
    elif field_name in ["birth_date", "birthday"]:
        return get_random_birth_date()["full"]
    elif field_name == "address":
        return get_random_address()["street"]
    elif field_name == "city":
        return get_random_address()["city"]
    elif field_name == "state":
        return get_random_address()["state"]
    elif field_name == "zip":
        return get_random_address()["zip"]
    else:
        # Default: generate random string
        return f"random_{field_name}_{random.randint(100, 999)}"


# TEST
if __name__ == "__main__":
    print("=" * 60)
    print("Random Data Generator - Test")
    print("=" * 60)
    
    print("\n📋 Complete Profile:")
    profile = get_random_profile()
    for key, value in profile.items():
        print(f"  {key}: {value}")
    
    print("\n📧 Random Emails:")
    for _ in range(5):
        print(f"  {get_random_email()}")
    
    print("\n🔒 Random Passwords:")
    for _ in range(5):
        print(f"  {get_random_password()}")
    
    print("\n👤 Random Names:")
    for _ in range(5):
        print(f"  {get_random_full_name()}")
    
    print("\n🎂 Random Birth Dates:")
    for _ in range(5):
        birth = get_random_birth_date()
        print(f"  {birth['full']} (Y: {birth['year']}, M: {birth['month']}, D: {birth['day']})")
    
    print("\n✅ Random Data Generator Working!")