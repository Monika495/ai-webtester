"""
PERFECT Parser - Real Login/Signup with Smart Field Detection + Random Data
Validates actual login success and extracts ALL required fields
FIXED for Twitter/X, Amazon, LinkedIn + Wikipedia
ENHANCED: Fixed field extraction and random data logic
"""

import os
import json
import re
import random
import time
from typing import List, Dict, Any

# Import random data generator
try:
    from agent.random_data import get_random_data, get_random_profile
    RANDOM_DATA_AVAILABLE = True
except ImportError:
    print("⚠️ Random data module not available")
    RANDOM_DATA_AVAILABLE = False
    def get_random_data(field_name):
        return f"random_{field_name}"
    def get_random_profile():
        return {}


class UniversalParser:
    """
    Production parser with SMART field extraction + Random Data Support
    FIXED for all websites including Wikipedia
    ENHANCED: Fixed field extraction and LinkedIn handling
    """
    
    def __init__(self, api_key=None, use_random_data=False):
        self.use_ai = False
        self.client = None
        self.model_name = "gemini-1.5-flash"
        self.use_random_data = use_random_data
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._init_ai()
        
        # Known websites with specific requirements
        self.site_configs = {
            "facebook": {
                "url": "https://facebook.com",
                "login_url": "https://facebook.com",
                "login_fields": ["email", "password"],
                "signup_fields": ["first_name", "last_name", "email", "password", "birth_day", "birth_month", "birth_year", "gender"],
                "signup_flow": "facebook"
            },
            "twitter": {
                "url": "https://twitter.com",
                "login_url": "https://twitter.com/i/flow/login",
                "signup_url": "https://twitter.com/i/flow/signup",
                "login_fields": ["username", "password"],
                "signup_fields": ["name", "email", "password", "birth_month", "birth_day", "birth_year"],
                "signup_flow": "twitter_step_by_step"
            },
            "x.com": {
                "url": "https://x.com",
                "login_url": "https://x.com/i/flow/login",
                "signup_url": "https://x.com/i/flow/signup",
                "login_fields": ["username", "password"],
                "signup_fields": ["name", "email", "password", "birth_month", "birth_day", "birth_year"],
                "signup_flow": "twitter_step_by_step"
            },
            "instagram": {
                "url": "https://instagram.com",
                "login_url": "https://instagram.com/accounts/login/",
                "signup_fields": ["email", "name", "username", "password"],
                "signup_flow": "instagram"
            },
            "linkedin": {
                "url": "https://linkedin.com",
                "login_url": "https://linkedin.com/login",
                "signup_url": "https://linkedin.com/signup",
                "login_fields": ["email", "password"],
                "signup_fields": ["first_name", "last_name", "email", "password"],
                "signup_flow": "linkedin",
                "required_for_signup": ["email", "password"]
            },
            "amazon": {
                "url": "https://amazon.com",
                "login_url": "https://amazon.com/ap/signin",
                "search_selector": "#twotabsearchtextbox, input[name='field-keywords']",
                "signup_fields": ["name", "email", "password"],
                "signup_flow": "generic"
            },
            "flipkart": {
                "url": "https://flipkart.com",
                "search_selector": "input[name='q'], input[title='Search for products, brands and more']",
                "signup_fields": ["email", "password"],
                "signup_flow": "generic"
            },
            "google": {
                "url": "https://google.com",
                "login_url": "https://accounts.google.com",
                "search_selector": "textarea[name='q'], input[name='q']",
                "signup_fields": ["first_name", "last_name", "email", "password"],
                "signup_flow": "generic"
            },
            "youtube": {
                "url": "https://youtube.com",
                "search_selector": "input[name='search_query'], input[id='search']",
            },
            "wikipedia": {
                "url": "https://wikipedia.org",
                "search_selector": "#searchInput, input[name='search']",
                "signup_flow": "generic"
            },
            "wiki": {
                "url": "https://wikipedia.org",
                "search_selector": "#searchInput, input[name='search']",
                "signup_flow": "generic"
            },
            "reddit": {
                "url": "https://reddit.com",
                "signup_fields": ["email", "username", "password"],
                "signup_flow": "generic"
            },
            "github": {
                "url": "https://github.com",
                "signup_fields": ["email", "username", "password"],
                "signup_flow": "generic"
            }
        }
    
    def _init_ai(self):
        """Initialize Gemini AI"""
        if not self.api_key:
            print("⚠️ No GEMINI_API_KEY. Using regex mode.")
            return
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Say OK"
            )
            
            if response.text and "OK" in response.text.upper():
                self.use_ai = True
                print("🤖 AI MODE ENABLED")
        except:
            print("⚠️ Using regex mode.")
    
    def _get_field_value(self, field_name: str, extracted_fields: Dict, site: str = None) -> str:
        """
        Get field value with smart random data support
        1. Always uses provided fields first
        2. Generates random data for missing fields when use_random_data is True
        3. Special handling for LinkedIn email uniqueness
        """
        # Check if user provided this field
        if field_name in extracted_fields and extracted_fields[field_name]:
            print(f"✅ Using provided field: {field_name} = {extracted_fields[field_name][:20]}...")
            return extracted_fields[field_name]
        
        # If field is missing and random data is enabled, generate it
        if self.use_random_data and RANDOM_DATA_AVAILABLE:
            print(f"🎲 Generating random data for missing field: {field_name}")
            
            # Special handling for email to ensure uniqueness
            if field_name == "email":
                timestamp = int(time.time())
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
                domains = ["gmail.com", "yahoo.com", "outlook.com", "mail.com", "protonmail.com", "hotmail.com"]
                
                # Site-specific email formatting
                if site == "linkedin":
                    return f"linkedin_test_{timestamp}_{random_str}@{random.choice(domains)}"
                elif site == "twitter":
                    return f"twitter_test_{timestamp}_{random_str}@{random.choice(domains)}"
                else:
                    return f"test{timestamp}_{random_str}@{random.choice(domains)}"
            
            # Special handling for password to ensure strength
            elif field_name == "password":
                chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
                return ''.join(random.choices(chars, k=12))
            
            # For name fields
            elif field_name in ["first_name", "name"]:
                first_names = ["John", "Jane", "David", "Sarah", "Michael", "Emily", "Robert", "Lisa", "William", "Maria"]
                return random.choice(first_names)
            
            elif field_name == "last_name":
                last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]
                return random.choice(last_names)
            
            elif field_name == "username":
                timestamp = int(time.time())
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
                return f"user_{timestamp}_{random_str}"
            
            # For other fields, use random data generator if available
            return get_random_data(field_name)
        
        # Field is missing and no random data
        print(f"⚠️ Missing field: {field_name} (random data not enabled)")
        return None
    
    def parse(self, instruction: str) -> List[Dict[str, Any]]:
        """Parse any natural language instruction"""
        instruction = instruction.strip()
        
        if not instruction:
            return [{"action": "error", "error": "Empty instruction"}]
        
        # Try AI first
        if self.use_ai and self.client:
            try:
                return self._parse_with_ai(instruction)
            except Exception as e:
                print(f"⚠️ AI failed, using smart parser...")
        
        # Smart regex parser
        return self._parse_with_smart_regex(instruction)
    
    def _parse_with_ai(self, instruction: str) -> List[Dict[str, Any]]:
        """AI-powered parsing"""
        
        prompt = f"""Convert to browser actions with CORRECT SELECTORS.

INSTRUCTION: "{instruction}"

IMPORTANT FIXES:
1. LinkedIn: Use "input[name='email-address']" for email in signup
2. LinkedIn: Use "input[name='first-name']" for first name
3. LinkedIn: Use "input[name='last-name']" for last name
4. For signup: Always include first_name and last_name fields
5. Check if required fields are provided

Return ONLY JSON array of actions."""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        
        try:
            actions = json.loads(text)
            print(f"✅ AI parsed {len(actions)} actions")
            return actions
        except:
            print("⚠️ AI parse failed, using smart regex")
            return self._parse_with_smart_regex(instruction)
    
    def _parse_with_smart_regex(self, instruction: str) -> List[Dict[str, Any]]:
        """SMART regex parser - FIXED field extraction"""
        print(f"🔍 Smart regex mode... (Random Data: {'ON' if self.use_random_data else 'OFF'})")
        
        inst = instruction.lower().strip()
        actions = []
        
        # Extract site
        site_key = self._extract_site_key(inst)
        
        # Detect action type
        is_login = any(kw in inst for kw in ["login", "signin", "sign in", "log in"])
        is_signup = any(kw in inst for kw in ["signup", "register", "sign up", "join", "create account", "create"])
        is_search = any(kw in inst for kw in ["search", "find", "look for"])
        is_shopping = any(kw in inst for kw in ["add to cart", "add", "buy", "purchase", "order"])
        
        # Extract ALL credentials from user input - FIXED EXTRACTION
        extracted_fields = self._extract_all_fields(instruction)  # Use original instruction (case-sensitive for email)
        
        print(f"📋 Extracted fields: {list(extracted_fields.keys())}")
        print(f"🔍 Site: {site_key}, Login: {is_login}, Signup: {is_signup}, Search: {is_search}")
        
        # ==================== LOGIN ACTION ====================
        if is_login:
            if site_key in self.site_configs:
                login_url = self.site_configs[site_key].get("login_url", self.site_configs[site_key]["url"])
                actions.append({"action": "navigate", "url": login_url})
            else:
                url = self._get_site_url(site_key)
                actions.append({"action": "navigate", "url": url})
            
            actions.append({"action": "wait", "seconds": 5})
            
            if site_key in ["twitter", "x.com"]:
                actions.extend(self._parse_twitter_login(inst, site_key, extracted_fields))
            elif site_key == "facebook":
                actions.extend(self._parse_facebook_login(inst, site_key, extracted_fields))
            elif site_key == "linkedin":
                actions.extend(self._parse_linkedin_login(inst, site_key, extracted_fields))
            else:
                actions.extend(self._parse_generic_login(inst, site_key, extracted_fields))
            
            return actions
        
        # ==================== SIGNUP ACTION ====================
        elif is_signup:
            print(f"🎯 SIGNUP DETECTED for {site_key}")
            
            # Check what fields we have
            has_email = "email" in extracted_fields and extracted_fields["email"]
            has_password = "password" in extracted_fields and extracted_fields["password"]
            
            print(f"📊 Field check - Email: {has_email}, Password: {has_password}")
            
            # Get site-specific required fields
            required_fields = self.site_configs.get(site_key, {}).get("signup_fields", ["email", "password"])
            if "email" not in required_fields and has_email:
                required_fields.append("email")
            if "password" not in required_fields and has_password:
                required_fields.append("password")
            
            print(f"🔧 Required fields for {site_key}: {required_fields}")
            
            # Check if we have minimum required fields
            missing_fields = []
            for field in required_fields:
                if field not in extracted_fields or not extracted_fields[field]:
                    # Check if we can generate it
                    if not self.use_random_data:
                        missing_fields.append(field)
                    elif field in ["email", "password", "first_name", "last_name", "name", "username"]:
                        # These can be generated with random data
                        continue
                    else:
                        missing_fields.append(field)
            
            # If we have missing fields and no random data, return error
            if missing_fields and not self.use_random_data:
                error_msg = f"Signup failed: Missing required fields: {', '.join(missing_fields)}. "
                error_msg += "Enable 'Use Random Data' to auto-generate missing fields or provide them in the instruction."
                
                return [{
                    "action": "error",
                    "error": error_msg,
                    "missing_fields": missing_fields,
                    "details": f"Example: 'signup on {site_key} with email user@example.com password MyPass123 first_name John last_name Doe'",
                    "suggestion": "Enable Random Data or provide all required fields"
                }]
            
            # If we're here, either we have all fields or random data is enabled
            if site_key in ["twitter", "x.com"]:
                signup_url = self.site_configs[site_key].get("signup_url", "https://x.com/i/flow/signup")
                actions.append({"action": "navigate", "url": signup_url})
                actions.append({"action": "wait", "seconds": 5})
                actions.extend(self._parse_twitter_signup(inst, site_key, extracted_fields))
            elif site_key == "facebook":
                actions.append({"action": "navigate", "url": "https://facebook.com"})
                actions.append({"action": "wait", "seconds": 3})
                actions.extend(self._parse_facebook_signup(inst, site_key, extracted_fields))
            elif site_key == "linkedin":
                actions.append({"action": "navigate", "url": "https://linkedin.com/signup"})
                actions.append({"action": "wait", "seconds": 3})
                actions.extend(self._parse_linkedin_signup(inst, site_key, extracted_fields))
            else:
                if site_key != "unknown":
                    url = self._get_site_url(site_key)
                    actions.append({"action": "navigate", "url": url})
                    actions.append({"action": "wait", "seconds": 3})
                actions.extend(self._parse_generic_signup(inst, site_key, extracted_fields))
            
            return actions
        
        # ==================== SEARCH ACTION ====================
        elif is_search:
            if site_key != "unknown":
                url = self._get_site_url(site_key)
                actions.append({"action": "navigate", "url": url})
                actions.append({"action": "wait", "seconds": 3})
            
            query = self._extract_search_query(inst)
            if query:
                # Get site-specific search selector
                search_selector = self._get_search_selector(site_key)
                actions.append({
                    "action": "search", 
                    "query": query,
                    "selector": search_selector
                })
                actions.append({"action": "wait", "seconds": 3})
                
                # Add to cart functionality
                if is_shopping:
                    actions.append({"action": "wait", "seconds": 5})
                    
                    # For e-commerce sites, click on first product
                    if site_key in ["flipkart", "amazon"]:
                        product_selector = {
                            "flipkart": "a[href*='/p/'], ._1fQZEK, div[data-tkid]",
                            "amazon": "a[href*='/dp/'], .s-result-item h2 a, .s-title-instructions-style h2 a"
                        }.get(site_key, "a")
                        
                        actions.append({
                            "action": "click",
                            "selector": product_selector,
                            "text": "Product",
                            "description": "Click on first product"
                        })
                        actions.append({"action": "wait", "seconds": 5})
                    
                    # Site-specific Add to Cart selectors
                    add_cart_selectors = {
                        "amazon": "#add-to-cart-button, #addToCart, input[name='submit.add-to-cart']",
                        "flipkart": "button:has-text('ADD TO CART'), button._2KpZ6l, ._3v1-ww",
                        "default": "button:has-text('Add to Cart'), #add-to-cart-button"
                    }
                    
                    selector = add_cart_selectors.get(site_key, add_cart_selectors["default"])
                    actions.append({
                        "action": "click",
                        "selector": selector,
                        "text": "Add to Cart",
                        "description": "Click Add to Cart button"
                    })
                    actions.append({"action": "wait", "seconds": 3})
                    
                    # Validate cart addition
                    actions.append({
                        "action": "validate_page",
                        "type": "shopping",
                        "text": "Added to Cart,Cart,Added,Proceed to checkout",
                        "min_indicators": 1,
                        "description": "Verify item added to cart"
                    })
            
            return actions
        
        # ==================== NAVIGATION ONLY ====================
        nav_keywords = ["go to", "go", "open", "visit", "launch", "navigate", "move to"]
        if any(kw in inst for kw in nav_keywords) or site_key != "unknown":
            url = self._get_site_url(site_key)
            actions.append({"action": "navigate", "url": url})
            actions.append({"action": "wait", "seconds": 3})
            return actions
        
        # ==================== FALLBACK ====================
        return [{
            "action": "error",
            "error": f"Could not understand: {instruction}",
            "suggestion": "Try: 'login to x.com with username myuser password mypass', 'signup on reddit with email demo@mail.com password mypass', 'search laptop on amazon', 'search quantum physics on wikipedia', 'create an account on linkedin' (requires random data)"
        }]
    
    def _get_search_selector(self, site_key: str) -> str:
        """Get search selector for site"""
        if site_key in self.site_configs:
            return self.site_configs[site_key].get("search_selector", 
                "input[type='search'], input[name='search'], input[type='text'], textarea[name='q'], input[name='q']")
        
        return "input[type='search'], input[name='search'], #search, .search-input, input[placeholder*='search' i], input[type='text']"
    
    def _extract_site_key(self, instruction: str) -> str:
        """Extract website key from instruction"""
        instruction_lower = instruction.lower()
        
        # Check for Wikipedia explicitly
        if "wikipedia" in instruction_lower or "wiki" in instruction_lower:
            return "wikipedia"
        
        # Check for LinkedIn variations
        if "linkedin" in instruction_lower or "linked in" in instruction_lower:
            return "linkedin"
        
        # Check other sites
        for site in self.site_configs.keys():
            if site in instruction_lower:
                return site
        
        # Check for domains
        words = instruction_lower.split()
        for word in words:
            clean_word = word.strip(".,;:!?()")
            if "." in clean_word and not clean_word.startswith("."):
                domain = clean_word.replace("www.", "").split(".")[0]
                if domain in self.site_configs:
                    return domain
                return domain
        
        return "unknown"
    
    def _get_site_url(self, site: str) -> str:
        """Get URL for site"""
        if site in self.site_configs:
            return self.site_configs[site]["url"]
        elif "." in site:
            return f"https://{site}" if not site.startswith("http") else site
        else:
            return f"https://{site}.com"
    
    def _extract_all_fields(self, instruction: str) -> Dict[str, str]:
        """Extract ALL fields from instruction - FIXED VERSION"""
        fields = {}
        
        # FIXED: Use original instruction for email extraction (case-sensitive)
        # Email patterns - more robust
        email_patterns = [
            r"email\s+(?:is\s+|as\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"with\s+email\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                email_match = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if "@" in email_match:
                    fields["email"] = email_match
                    print(f"✅ Extracted email: {email_match}")
                    break
        
        # Password patterns - more robust
        pass_patterns = [
            r"password\s+(?:is\s+|as\s+)?(\S+)",
            r"pass\s+(?:is\s+|as\s+)?(\S+)",
            r"with\s+password\s+(\S+)"
        ]
        
        for pattern in pass_patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                password = match.group(1)
                # Clean up password (remove trailing punctuation)
                password = password.rstrip('.,;:!?')
                fields["password"] = password
                print(f"✅ Extracted password: {password[:6]}******")
                break
        
        # Username patterns
        user_patterns = [
            r"username\s+(?:is\s+|as\s+)?(\S+)",
            r"user\s+(?:is\s+|as\s+)?(\S+)",
            r"with\s+username\s+(\S+)"
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                username = match.group(1).rstrip('.,;:!?')
                fields["username"] = username
                print(f"✅ Extracted username: {username}")
                break
        
        # Name patterns
        name_patterns = [
            r"name\s+(?:is\s+|as\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            r"with\s+name\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                name = match.group(1)
                fields["name"] = name
                print(f"✅ Extracted name: {name}")
                break
        
        # First name patterns
        first_patterns = [
            r"first[\s_-]?name\s+(?:is\s+|as\s+)?([a-zA-Z]+)",
            r"first\s+name\s+([a-zA-Z]+)"
        ]
        
        for pattern in first_patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                first_name = match.group(1)
                fields["first_name"] = first_name
                print(f"✅ Extracted first_name: {first_name}")
                break
        
        # Last name patterns
        last_patterns = [
            r"last[\s_-]?name\s+(?:is\s+|as\s+)?([a-zA-Z]+)",
            r"last\s+name\s+([a-zA-Z]+)"
        ]
        
        for pattern in last_patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                last_name = match.group(1)
                fields["last_name"] = last_name
                print(f"✅ Extracted last_name: {last_name}")
                break
        
        return fields
    
    def _extract_search_query(self, instruction: str) -> str:
        """Extract search query"""
        patterns = [
            r"search\s+(?:for\s+)?(.+?)\s+on\s+wikipedia",
            r"find\s+(.+?)\s+on\s+wikipedia",
            r"search\s+(?:for\s+)?(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)",
            r"find\s+(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)",
            r"look for\s+(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction.lower())
            if match:
                query = match.group(1).strip()
                # Remove site names and action words
                remove_words = list(self.site_configs.keys()) + [
                    "add to cart", "add", "buy", "purchase", "and then", 
                    "login", "signup", "then", "wikipedia", "wiki"
                ]
                for word in remove_words:
                    query = query.replace(word, " ")
                return " ".join(query.split()).strip()
        
        return ""
    
    def _parse_twitter_login(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse Twitter/X login actions"""
        actions = []
        
        username = self._get_field_value("username", fields, site)
        password = self._get_field_value("password", fields, site)
        
        missing = []
        if not username:
            missing.append("username or email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"{site.capitalize()} login failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing,
                "details": f"Required: {', '.join(missing)}"
            }]
        
        # Type username/email
        actions.append({
            "action": "type",
            "selector": "input[autocomplete='username'], input[name='text'], input[type='text']",
            "value": username,
            "field_type": "username",
            "description": f"Enter username: {username}"
        })
        actions.append({"action": "wait", "seconds": 2})
        
        # Click Next
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next'), span:has-text('Next')",
            "text": "Next",
            "description": "Click Next button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        # Type password
        actions.append({
            "action": "type",
            "selector": "input[type='password'], input[name='password'], input[data-testid='LoginForm_Login_Button'] ~ input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 2})
        
        # Click Log in
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button[data-testid*='Login'], button:has-text('Log in'), div[role='button']:has-text('Log in')",
            "text": "Log in",
            "description": "Click Login button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Validate login
        actions.append({
            "action": "validate_page",
            "type": "login",
            "text": "@",
            "min_indicators": 1,
            "description": "Verify login successful"
        })
        
        return actions
    
    def _parse_twitter_signup(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse Twitter/X signup"""
        actions = []
        
        name = self._get_field_value("name", fields, site)
        email = self._get_field_value("email", fields, site)
        password = self._get_field_value("password", fields, site)
        birth_month = self._get_field_value("birth_month", fields, site) or "January"
        birth_day = self._get_field_value("birth_day", fields, site) or "1"
        birth_year = self._get_field_value("birth_year", fields, site) or "1990"
        
        missing = []
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"Twitter signup failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        # Name field
        actions.append({
            "action": "type",
            "selector": "input[name='name'], input[placeholder*='name']",
            "value": name,
            "field_type": "name",
            "description": f"Enter name: {name}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        # Email field
        actions.append({
            "action": "type",
            "selector": "input[name='email'], input[type='email']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        # Click Next
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        # Birthday selection
        actions.append({
            "action": "select",
            "selector": "select[aria-label='Month']",
            "value": birth_month,
            "field_type": "birth_month",
            "description": f"Select birth month: {birth_month}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "select",
            "selector": "select[aria-label='Day']",
            "value": birth_day,
            "field_type": "birth_day",
            "description": f"Select birth day: {birth_day}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "select",
            "selector": "select[aria-label='Year']",
            "value": birth_year,
            "field_type": "birth_year",
            "description": f"Select birth year: {birth_year}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        # Click Next after birthday
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next after birthday"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        # Password field
        actions.append({
            "action": "type",
            "selector": "input[name='password'], input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        # Click Next
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next after password"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Validate signup
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Verify",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions
    
    def _parse_linkedin_login(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse LinkedIn login"""
        actions = []
        
        email = self._get_field_value("email", fields, site) or self._get_field_value("username", fields, site)
        password = self._get_field_value("password", fields, site)
        
        missing = []
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"LinkedIn login failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        actions.append({
            "action": "type",
            "selector": "input[name='session_key'], input[id='username'], input[type='text']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "type",
            "selector": "input[name='session_password'], input[id='password'], input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Sign in')",
            "text": "Sign in",
            "description": "Click Sign in button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "login",
            "text": "Feed",
            "min_indicators": 2,
            "description": "Verify login successful"
        })
        
        return actions
    
    def _parse_linkedin_signup(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse LinkedIn signup - FIXED VERSION"""
        actions = []
        
        # Get or generate values with site context
        first_name = self._get_field_value("first_name", fields, site)
        last_name = self._get_field_value("last_name", fields, site)
        email = self._get_field_value("email", fields, site)
        password = self._get_field_value("password", fields, site)
        
        print(f"🔧 LinkedIn Signup Fields - First: {first_name}, Last: {last_name}, Email: {email}, Password: {'*' * 8 if password else 'None'}")
        
        # LinkedIn requires first_name, last_name, email, password
        missing = []
        required_fields = ["first_name", "last_name", "email", "password"]
        
        for field in required_fields:
            field_value = None
            if field == "first_name":
                field_value = first_name
            elif field == "last_name":
                field_value = last_name
            elif field == "email":
                field_value = email
            elif field == "password":
                field_value = password
            
            if not field_value:
                missing.append(field)
        
        if missing:
            error_msg = f"LinkedIn signup failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing,
                "suggestion": "For LinkedIn signup, you need: first_name, last_name, email, password"
            }]
        
        print(f"✅ All LinkedIn fields available or generated")
        
        # First name
        actions.append({
            "action": "type",
            "selector": "input[name='first-name'], input[id='first-name']",
            "value": first_name,
            "field_type": "first_name",
            "description": f"Enter first name: {first_name}",
            "is_random_data": "first_name" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Last name
        actions.append({
            "action": "type",
            "selector": "input[name='last-name'], input[id='last-name']",
            "value": last_name,
            "field_type": "last_name",
            "description": f"Enter last name: {last_name}",
            "is_random_data": "last_name" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Email - LinkedIn uses 'email-address'
        actions.append({
            "action": "type",
            "selector": "input[name='email-address'], input[id='email-address']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}",
            "is_random_data": "email" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Password
        actions.append({
            "action": "type",
            "selector": "input[name='password'], input[id='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password",
            "is_random_data": "password" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Submit button
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Agree & Join'), button:has-text('Join now')",
            "text": "Agree & Join",
            "description": "Click Agree & Join button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Validate signup
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Verify,Check your email,Enter confirmation code,Welcome",
            "min_indicators": 1,
            "description": "Verify signup successful (even if email verification needed)"
        })
        
        return actions
    
    def _parse_facebook_login(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse Facebook login"""
        actions = []
        
        email = self._get_field_value("email", fields, site) or self._get_field_value("username", fields, site)
        password = self._get_field_value("password", fields, site)
        
        missing = []
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"Facebook login failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        actions.append({
            "action": "type",
            "selector": "input[name='email'], input[type='email'], input[id='email']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "type",
            "selector": "input[name='pass'], input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[name='login'], button[type='submit']",
            "text": "Log in",
            "description": "Click Login button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "login",
            "text": "Profile",
            "min_indicators": 2,
            "description": "Verify login successful"
        })
        
        return actions
    
    def _parse_facebook_signup(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse Facebook signup"""
        actions = []
        
        first_name = self._get_field_value("first_name", fields, site)
        last_name = self._get_field_value("last_name", fields, site)
        email = self._get_field_value("email", fields, site)
        password = self._get_field_value("password", fields, site)
        birth_day = self._get_field_value("birth_day", fields, site) or "1"
        birth_month = self._get_field_value("birth_month", fields, site) or "January"
        birth_year = self._get_field_value("birth_year", fields, site) or "1990"
        gender = self._get_field_value("gender", fields, site) or "female"
        
        missing = []
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"Facebook signup failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        # Click Create Account button
        actions.append({
            "action": "click",
            "selector": "a[data-testid='open-registration-form-button']",
            "text": "Create Account",
            "description": "Click Create Account button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        # First name
        actions.append({
            "action": "type",
            "selector": "input[name='firstname']",
            "value": first_name,
            "field_type": "first_name",
            "description": f"Enter first name: {first_name}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Last name
        actions.append({
            "action": "type", 
            "selector": "input[name='lastname']",
            "value": last_name,
            "field_type": "last_name",
            "description": f"Enter last name: {last_name}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Email
        actions.append({
            "action": "type",
            "selector": "input[name='reg_email__']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Email confirmation
        actions.append({
            "action": "type",
            "selector": "input[name='reg_email_confirmation__']",
            "value": email,
            "field_type": "email_confirm",
            "description": "Confirm email"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Password
        actions.append({
            "action": "type",
            "selector": "input[name='reg_passwd__']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Birthday
        actions.append({
            "action": "select",
            "selector": "select[name='birthday_day']",
            "value": birth_day,
            "field_type": "birth_day",
            "description": f"Select birth day: {birth_day}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "select",
            "selector": "select[name='birthday_month']",
            "value": birth_month,
            "field_type": "birth_month",
            "description": f"Select birth month: {birth_month}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "select",
            "selector": "select[name='birthday_year']",
            "value": birth_year,
            "field_type": "birth_year",
            "description": f"Select birth year: {birth_year}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Gender
        gender_value = "2" if gender and gender.lower() == "male" else "1"
        actions.append({
            "action": "click",
            "selector": f"input[value='{gender_value}']",
            "text": gender.capitalize() if gender else "Female",
            "field_type": "gender",
            "description": f"Select gender: {gender or 'Female'}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        # Submit
        actions.append({
            "action": "click",
            "selector": "button[name='websubmit']",
            "text": "Sign Up",
            "description": "Click Sign Up button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Validate signup
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Confirm",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions
    
    def _parse_generic_login(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse generic login"""
        actions = []
        
        email = self._get_field_value("email", fields, site) or self._get_field_value("username", fields, site)
        password = self._get_field_value("password", fields, site)
        
        missing = []
        if not email:
            missing.append("email or username")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"Login failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        if fields.get("email") or (email and "@" in email):
            actions.append({
                "action": "type",
                "selector": "input[type='email'], input[name='email'], input[placeholder*='email']",
                "value": email,
                "field_type": "email",
                "description": f"Enter email: {email}"
            })
        else:
            actions.append({
                "action": "type",
                "selector": "input[name='username'], input[placeholder*='username']",
                "value": email,
                "field_type": "username",
                "description": f"Enter username: {email}"
            })
        
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "type",
            "selector": "input[type='password'], input[name='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Log in'), button:has-text('Sign in')",
            "text": "Log in",
            "description": "Click Login button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "login",
            "text": "Profile",
            "min_indicators": 2,
            "description": "Verify login successful"
        })
        
        return actions
    
    def _parse_generic_signup(self, instruction: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Parse generic signup"""
        actions = []
        
        name = self._get_field_value("name", fields, site)
        email = self._get_field_value("email", fields, site)
        password = self._get_field_value("password", fields, site)
        
        missing = []
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        
        if missing:
            error_msg = f"Signup failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing
            }]
        
        # Click signup button
        actions.append({
            "action": "click",
            "selector": "a:has-text('Sign up'), a:has-text('Create New Account'), button:has-text('Sign up'), button:has-text('Join')",
            "text": "Sign up",
            "description": "Click Sign up button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        # Name
        if name:
            actions.append({
                "action": "type",
                "selector": "input[name='name'], input[placeholder*='name']",
                "value": name,
                "field_type": "name",
                "description": f"Enter name: {name}"
            })
            actions.append({"action": "wait", "seconds": 0.5})
        
        # Email
        actions.append({
            "action": "type",
            "selector": "input[type='email'], input[name='email']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Password
        actions.append({
            "action": "type",
            "selector": "input[type='password'], input[name='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        # Submit
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Sign up'), button:has-text('Next'), button:has-text('Join')",
            "text": "Sign up",
            "description": "Click Sign up button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Validate signup
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Confirm",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("Testing Universal Parser with Enhanced Logic")
    print('='*60)
    
    # Test cases
    test_cases = [
        ("signup on linkedin with email test@mail.com password test123", False, "Should SUCCEED - provided credentials"),
        ("signup on linkedin with email test@mail.com password test123", True, "Should SUCCEED - provided credentials + random"),
        ("create an account on linkedin", False, "Should FAIL - missing credentials"),
        ("create an account on linkedin", True, "Should SUCCEED - random data"),
        ("signup on twitter with email test@mail.com", True, "Should SUCCEED - mixed data"),
    ]
    
    for instruction, use_random, expected in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {instruction}")
        print(f"Random Data: {use_random}")
        print(f"Expected: {expected}")
        print('-'*50)
        
        parser = UniversalParser(use_random_data=use_random)
        actions = parser.parse(instruction)
        
        if actions and actions[0].get("action") == "error":
            print(f"❌ Result: ERROR - {actions[0].get('error')}")
        else:
            print(f"✅ Result: SUCCESS - {len(actions)} actions generated")
            for i, action in enumerate(actions[:3], 1):
                desc = action.get('description', action.get('action', 'Unknown'))
                print(f"  {i}. {desc}")
            if len(actions) > 3:
                print(f"  ... and {len(actions)-3} more actions")