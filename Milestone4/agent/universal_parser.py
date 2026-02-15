"""
PERFECT Parser - Fixed Simple Instruction Parsing + Smart Field Detection
Maintains all existing functionality but fixes parsing issues
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
    FIXED Parser: Simple instructions work correctly + maintains all features
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
        """Parse any natural language instruction - FIXED SIMPLE PARSING"""
        instruction = instruction.strip()
        
        if not instruction:
            return [{"action": "error", "error": "Empty instruction"}]
        
        print(f"\n🔍 Parsing: '{instruction}'")
        print(f"🎲 Random Data: {'ON' if self.use_random_data else 'OFF'}")
        
        # First, try AI if available
        if self.use_ai and self.client:
            try:
                return self._parse_with_ai(instruction)
            except Exception as e:
                print(f"⚠️ AI parsing failed: {e}")
                print("🔄 Falling back to smart parser...")
        
        # Use the new simplified parser that works for all cases
        return self._parse_simple(instruction)
    
    def _parse_simple(self, instruction: str) -> List[Dict[str, Any]]:
        """
        SIMPLE PARSER - Fixes all parsing issues
        This parser handles everything correctly
        """
        instruction_lower = instruction.lower()
        actions = []
        
        print(f"🔄 Using simple parser for: '{instruction}'")
        
        # ==================== STEP 1: EXTRACT ALL FIELDS ====================
        extracted_fields = {}
        
        # Extract email
        email_patterns = [
            r'email\s+(?:is\s+|as\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'with\s+email\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                email = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if "@" in email:
                    extracted_fields["email"] = email
                    print(f"📧 Extracted email: {email}")
                    break
        
        # Extract password
        pass_patterns = [
            r'password\s+(?:is\s+|as\s+)?(\S+)',
            r'pass\s+(?:is\s+|as\s+)?(\S+)',
            r'with\s+password\s+(\S+)'
        ]
        
        for pattern in pass_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                password = match.group(1).rstrip('.,;:!?')
                extracted_fields["password"] = password
                print(f"🔑 Extracted password: {password[:6]}******")
                break
        
        # Extract username
        user_patterns = [
            r'username\s+(?:is\s+|as\s+)?(\S+)',
            r'user\s+(?:is\s+|as\s+)?(\S+)',
            r'with\s+username\s+(\S+)'
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                username = match.group(1).rstrip('.,;:!?')
                extracted_fields["username"] = username
                print(f"👤 Extracted username: {username}")
                break
        
        # Extract name
        name_patterns = [
            r'name\s+(?:is\s+|as\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            r'with\s+name\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                name = match.group(1)
                extracted_fields["name"] = name
                print(f"📛 Extracted name: {name}")
                break
        
        # Extract first name
        first_patterns = [
            r'first[\s_-]?name\s+(?:is\s+|as\s+)?([a-zA-Z]+)',
            r'first\s+name\s+([a-zA-Z]+)'
        ]
        
        for pattern in first_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                first_name = match.group(1)
                extracted_fields["first_name"] = first_name
                print(f"📛 Extracted first_name: {first_name}")
                break
        
        # Extract last name
        last_patterns = [
            r'last[\s_-]?name\s+(?:is\s+|as\s+)?([a-zA-Z]+)',
            r'last\s+name\s+([a-zA-Z]+)'
        ]
        
        for pattern in last_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                last_name = match.group(1)
                extracted_fields["last_name"] = last_name
                print(f"📛 Extracted last_name: {last_name}")
                break
        
        # ==================== STEP 2: DETECT SITE ====================
        site = self._detect_site(instruction_lower)
        print(f"🌐 Detected site: {site}")
        
        # ==================== STEP 3: DETECT ACTION TYPE ====================
        action_type = self._detect_action_type(instruction_lower)
        print(f"🎯 Detected action: {action_type}")
        
        # ==================== STEP 4: HANDLE EACH ACTION TYPE ====================
        if action_type == "search":
            return self._handle_search(instruction, instruction_lower, site, extracted_fields)
        
        elif action_type == "login":
            return self._handle_login(instruction, instruction_lower, site, extracted_fields)
        
        elif action_type == "signup":
            return self._handle_signup(instruction, instruction_lower, site, extracted_fields)
        
        elif action_type == "navigate":
            return self._handle_navigation(instruction, instruction_lower, site, extracted_fields)
        
        else:
            # Default: try to navigate to the site
            if site != "unknown":
                url = self._get_site_url(site)
                return [{"action": "navigate", "url": url}]
            else:
                return [{
                    "action": "error",
                    "error": f"Could not understand: {instruction}",
                    "suggestion": "Try: 'login to facebook with email test@mail.com password pass123' or 'search laptop on amazon'"
                }]
    
    def _detect_site(self, instruction_lower: str) -> str:
        """Detect which website is mentioned"""
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
    
    def _detect_action_type(self, instruction_lower: str) -> str:
        """Detect what action is being requested"""
        if any(kw in instruction_lower for kw in ["search", "find", "look for"]):
            return "search"
        elif any(kw in instruction_lower for kw in ["login", "signin", "sign in", "log in"]):
            return "login"
        elif any(kw in instruction_lower for kw in ["signup", "register", "sign up", "join", "create account", "create"]):
            return "signup"
        elif any(kw in instruction_lower for kw in ["go to", "open", "visit", "navigate", "launch", "move to"]):
            return "navigate"
        else:
            return "unknown"
    
    def _handle_search(self, instruction: str, instruction_lower: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Handle search actions"""
        actions = []
        
        # Get URL
        url = self._get_site_url(site)
        actions.append({"action": "navigate", "url": url})
        actions.append({"action": "wait", "seconds": 3})
        
        # Extract search query
        query = self._extract_search_query(instruction)
        
        if query:
            search_selector = self._get_search_selector(site)
            actions.append({
                "action": "search",
                "query": query,
                "selector": search_selector,
                "description": f"Search for {query} on {site}"
            })
            actions.append({"action": "wait", "seconds": 3})
            
            # Handle add to cart
            if "add to cart" in instruction_lower or "add" in instruction_lower:
                actions.append({"action": "wait", "seconds": 5})
                
                if site in ["flipkart", "amazon"]:
                    product_selector = {
                        "flipkart": "a[href*='/p/'], ._1fQZEK, div[data-tkid]",
                        "amazon": "a[href*='/dp/'], .s-result-item h2 a, .s-title-instructions-style h2 a"
                    }.get(site, "a")
                    
                    actions.append({
                        "action": "click",
                        "selector": product_selector,
                        "text": "Product",
                        "description": "Click on first product"
                    })
                    actions.append({"action": "wait", "seconds": 5})
                
                add_cart_selectors = {
                    "amazon": "#add-to-cart-button, #addToCart, input[name='submit.add-to-cart']",
                    "flipkart": "button:has-text('ADD TO CART'), button._2KpZ6l, ._3v1-ww",
                    "default": "button:has-text('Add to Cart'), #add-to-cart-button"
                }
                
                selector = add_cart_selectors.get(site, add_cart_selectors["default"])
                actions.append({
                    "action": "click",
                    "selector": selector,
                    "text": "Add to Cart",
                    "description": "Click Add to Cart button"
                })
                actions.append({"action": "wait", "seconds": 3})
                
                actions.append({
                    "action": "validate_page",
                    "type": "shopping",
                    "text": "Added to Cart,Cart,Added,Proceed to checkout",
                    "min_indicators": 1,
                    "description": "Verify item added to cart"
                })
        
        return actions
    
    def _handle_login(self, instruction: str, instruction_lower: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Handle login actions"""
        actions = []
        
        # Get login URL
        if site in self.site_configs:
            login_url = self.site_configs[site].get("login_url", self.site_configs[site]["url"])
            actions.append({"action": "navigate", "url": login_url})
        else:
            url = self._get_site_url(site)
            actions.append({"action": "navigate", "url": url})
        
        actions.append({"action": "wait", "seconds": 5})
        
        # Check for required credentials
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
                "missing_fields": missing,
                "details": f"Required: {', '.join(missing)}"
            }]
        
        # Site-specific login handling
        if site in ["twitter", "x.com"]:
            actions.extend(self._handle_twitter_login(email, password, site))
        elif site == "facebook":
            actions.extend(self._handle_facebook_login(email, password, site))
        elif site == "linkedin":
            actions.extend(self._handle_linkedin_login(email, password, site))
        else:
            actions.extend(self._handle_generic_login(email, password, site))
        
        return actions
    
    def _handle_signup(self, instruction: str, instruction_lower: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Handle signup actions"""
        actions = []
        
        print(f"🎯 SIGNUP DETECTED for {site}")
        print(f"📋 Available fields: {list(fields.keys())}")
        
        # Get required fields for this site
        required_fields = self.site_configs.get(site, {}).get("signup_fields", ["email", "password"])
        print(f"🔧 Required fields for {site}: {required_fields}")
        
        # Get or generate values
        generated_fields = {}
        for field in required_fields:
            value = self._get_field_value(field, fields, site)
            if value:
                generated_fields[field] = value
        
        # Check if we have minimum required fields
        has_email = "email" in generated_fields and generated_fields["email"]
        has_password = "password" in generated_fields and generated_fields["password"]
        
        print(f"📊 Field check - Email: {has_email}, Password: {has_password}")
        
        # For LinkedIn, we need first_name and last_name too
        if site == "linkedin":
            if "first_name" not in required_fields:
                required_fields.append("first_name")
            if "last_name" not in required_fields:
                required_fields.append("last_name")
            
            # Get these fields
            for field in ["first_name", "last_name"]:
                value = self._get_field_value(field, fields, site)
                if value:
                    generated_fields[field] = value
        
        # Check missing fields
        missing = []
        for field in required_fields:
            if field not in generated_fields or not generated_fields[field]:
                missing.append(field)
        
        if missing:
            error_msg = f"Signup failed: Missing required fields: {', '.join(missing)}"
            if not self.use_random_data:
                error_msg += ". Enable 'Use Random Data' to auto-fill missing fields."
            
            return [{
                "action": "error",
                "error": error_msg,
                "missing_fields": missing,
                "suggestion": f"For {site} signup, you need: {', '.join(required_fields)}"
            }]
        
        # Get signup URL
        if site in self.site_configs:
            signup_url = self.site_configs[site].get("signup_url", self.site_configs[site]["url"])
            actions.append({"action": "navigate", "url": signup_url})
        else:
            url = self._get_site_url(site)
            actions.append({"action": "navigate", "url": url})
        
        actions.append({"action": "wait", "seconds": 3})
        
        # Site-specific signup handling
        if site in ["twitter", "x.com"]:
            actions.extend(self._handle_twitter_signup(generated_fields, site))
        elif site == "facebook":
            actions.extend(self._handle_facebook_signup(generated_fields, site))
        elif site == "linkedin":
            actions.extend(self._handle_linkedin_signup(generated_fields, site))
        else:
            actions.extend(self._handle_generic_signup(generated_fields, site))
        
        return actions
    
    def _handle_navigation(self, instruction: str, instruction_lower: str, site: str, fields: Dict) -> List[Dict[str, Any]]:
        """Handle simple navigation"""
        if site != "unknown":
            url = self._get_site_url(site)
            return [
                {"action": "navigate", "url": url},
                {"action": "wait", "seconds": 3}
            ]
        else:
            # Try to extract URL from instruction
            url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+|\S+\.(com|org|net|in)[^\s]*)', instruction)
            if url_match:
                url = url_match.group(0)
                if not url.startswith("http"):
                    url = f"https://{url}"
                return [
                    {"action": "navigate", "url": url},
                    {"action": "wait", "seconds": 3}
                ]
            else:
                return [{
                    "action": "error",
                    "error": f"Could not find URL in: {instruction}",
                    "suggestion": "Try: 'go to google.com' or 'open wikipedia.org'"
                }]
    
    def _extract_search_query(self, instruction: str) -> str:
        """Extract search query from instruction"""
        patterns = [
            r'search\s+(?:for\s+)?(.+?)\s+on\s+wikipedia',
            r'find\s+(.+?)\s+on\s+wikipedia',
            r'search\s+(?:for\s+)?(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)',
            r'find\s+(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)',
            r'look for\s+(.+?)(?:\s+on|\s+in|\s+and|\s+then|$)',
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
    
    def _get_search_selector(self, site: str) -> str:
        """Get search selector for site"""
        if site in self.site_configs:
            return self.site_configs[site].get("search_selector", 
                "input[type='search'], input[name='search'], input[type='text'], textarea[name='q'], input[name='q']")
        
        return "input[type='search'], input[name='search'], #search, .search-input, input[placeholder*='search' i], input[type='text']"
    
    def _get_site_url(self, site: str) -> str:
        """Get URL for site"""
        if site in self.site_configs:
            return self.site_configs[site]["url"]
        elif "." in site:
            return f"https://{site}" if not site.startswith("http") else site
        else:
            return f"https://{site}.com"
    
    # ==================== SITE-SPECIFIC HANDLERS ====================
    
    def _handle_twitter_login(self, email: str, password: str, site: str) -> List[Dict[str, Any]]:
        """Handle Twitter/X login"""
        actions = []
        
        actions.append({
            "action": "type",
            "selector": "input[autocomplete='username'], input[name='text'], input[type='text']",
            "value": email,
            "field_type": "username",
            "description": f"Enter username: {email}"
        })
        actions.append({"action": "wait", "seconds": 2})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next'), span:has-text('Next')",
            "text": "Next",
            "description": "Click Next button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        actions.append({
            "action": "type",
            "selector": "input[type='password'], input[name='password'], input[data-testid='LoginForm_Login_Button'] ~ input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 2})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button[data-testid*='Login'], button:has-text('Log in'), div[role='button']:has-text('Log in')",
            "text": "Log in",
            "description": "Click Login button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "login",
            "text": "@",
            "min_indicators": 1,
            "description": "Verify login successful"
        })
        
        return actions
    
    def _handle_twitter_signup(self, fields: Dict, site: str) -> List[Dict[str, Any]]:
        """Handle Twitter/X signup"""
        actions = []
        
        name = fields.get("name", "Test User")
        email = fields.get("email", "")
        password = fields.get("password", "")
        birth_month = fields.get("birth_month", "January")
        birth_day = fields.get("birth_day", "1")
        birth_year = fields.get("birth_year", "1990")
        
        actions.append({
            "action": "type",
            "selector": "input[name='name'], input[placeholder*='name']",
            "value": name,
            "field_type": "name",
            "description": f"Enter name: {name}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "type",
            "selector": "input[name='email'], input[type='email']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
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
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next after birthday"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        actions.append({
            "action": "type",
            "selector": "input[name='password'], input[type='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Next'), div[role='button']:has-text('Next')",
            "text": "Next",
            "description": "Click Next after password"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Verify",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions
    
    def _handle_linkedin_login(self, email: str, password: str, site: str) -> List[Dict[str, Any]]:
        """Handle LinkedIn login"""
        actions = []
        
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
    
    def _handle_linkedin_signup(self, fields: Dict, site: str) -> List[Dict[str, Any]]:
        """Handle LinkedIn signup"""
        actions = []
        
        first_name = fields.get("first_name", "Test")
        last_name = fields.get("last_name", "User")
        email = fields.get("email", "")
        password = fields.get("password", "")
        
        print(f"🔧 LinkedIn Signup - First: {first_name}, Last: {last_name}, Email: {email}, Password: {'*' * 8}")
        
        actions.append({
            "action": "type",
            "selector": "input[name='first-name'], input[id='first-name']",
            "value": first_name,
            "field_type": "first_name",
            "description": f"Enter first name: {first_name}",
            "is_random_data": "first_name" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='last-name'], input[id='last-name']",
            "value": last_name,
            "field_type": "last_name",
            "description": f"Enter last name: {last_name}",
            "is_random_data": "last_name" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='email-address'], input[id='email-address']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}",
            "is_random_data": "email" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='password'], input[id='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password",
            "is_random_data": "password" not in fields
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Agree & Join'), button:has-text('Join now')",
            "text": "Agree & Join",
            "description": "Click Agree & Join button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Verify,Check your email,Enter confirmation code,Welcome",
            "min_indicators": 1,
            "description": "Verify signup successful (even if email verification needed)"
        })
        
        return actions
    
    def _handle_facebook_login(self, email: str, password: str, site: str) -> List[Dict[str, Any]]:
        """Handle Facebook login"""
        actions = []
        
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
    
    def _handle_facebook_signup(self, fields: Dict, site: str) -> List[Dict[str, Any]]:
        """Handle Facebook signup"""
        actions = []
        
        first_name = fields.get("first_name", "Test")
        last_name = fields.get("last_name", "User")
        email = fields.get("email", "")
        password = fields.get("password", "")
        birth_day = fields.get("birth_day", "1")
        birth_month = fields.get("birth_month", "January")
        birth_year = fields.get("birth_year", "1990")
        gender = fields.get("gender", "female")
        
        actions.append({
            "action": "click",
            "selector": "a[data-testid='open-registration-form-button']",
            "text": "Create Account",
            "description": "Click Create Account button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        actions.append({
            "action": "type",
            "selector": "input[name='firstname']",
            "value": first_name,
            "field_type": "first_name",
            "description": f"Enter first name: {first_name}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type", 
            "selector": "input[name='lastname']",
            "value": last_name,
            "field_type": "last_name",
            "description": f"Enter last name: {last_name}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='reg_email__']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='reg_email_confirmation__']",
            "value": email,
            "field_type": "email_confirm",
            "description": "Confirm email"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[name='reg_passwd__']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
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
        
        gender_value = "2" if gender and gender.lower() == "male" else "1"
        actions.append({
            "action": "click",
            "selector": f"input[value='{gender_value}']",
            "text": gender.capitalize() if gender else "Female",
            "field_type": "gender",
            "description": f"Select gender: {gender or 'Female'}"
        })
        actions.append({"action": "wait", "seconds": 1})
        
        actions.append({
            "action": "click",
            "selector": "button[name='websubmit']",
            "text": "Sign Up",
            "description": "Click Sign Up button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Confirm",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions
    
    def _handle_generic_login(self, email: str, password: str, site: str) -> List[Dict[str, Any]]:
        """Handle generic login"""
        actions = []
        
        if "@" in email:
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
    
    def _handle_generic_signup(self, fields: Dict, site: str) -> List[Dict[str, Any]]:
        """Handle generic signup"""
        actions = []
        
        name = fields.get("name", "Test User")
        email = fields.get("email", "")
        password = fields.get("password", "")
        
        actions.append({
            "action": "click",
            "selector": "a:has-text('Sign up'), a:has-text('Create New Account'), button:has-text('Sign up'), button:has-text('Join')",
            "text": "Sign up",
            "description": "Click Sign up button"
        })
        actions.append({"action": "wait", "seconds": 3})
        
        if name:
            actions.append({
                "action": "type",
                "selector": "input[name='name'], input[placeholder*='name']",
                "value": name,
                "field_type": "name",
                "description": f"Enter name: {name}"
            })
            actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[type='email'], input[name='email']",
            "value": email,
            "field_type": "email",
            "description": f"Enter email: {email}"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "type",
            "selector": "input[type='password'], input[name='password']",
            "value": password,
            "field_type": "password",
            "description": "Enter password"
        })
        actions.append({"action": "wait", "seconds": 0.5})
        
        actions.append({
            "action": "click",
            "selector": "button[type='submit'], button:has-text('Sign up'), button:has-text('Next'), button:has-text('Join')",
            "text": "Sign up",
            "description": "Click Sign up button"
        })
        
        actions.append({"action": "wait", "seconds": 5})
        
        actions.append({
            "action": "validate_page",
            "type": "signup",
            "text": "Confirm",
            "min_indicators": 1,
            "description": "Verify signup successful"
        })
        
        return actions
    
    def _parse_with_ai(self, instruction: str) -> List[Dict[str, Any]]:
        """AI-powered parsing - kept for backward compatibility"""
        try:
            from google import genai
            
            prompt = f"""Convert to browser actions with CORRECT SELECTORS.

INSTRUCTION: "{instruction}"

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
            
            actions = json.loads(text)
            print(f"✅ AI parsed {len(actions)} actions")
            return actions
        
        except Exception as e:
            print(f"⚠️ AI parse failed: {e}")
            return self._parse_simple(instruction)


# ==================== TEST THE FIXED PARSER ====================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("🧪 Testing FIXED Universal Parser")
    print('='*60)
    
    # Test cases that should work perfectly
    test_cases = [
        # Simple searches (should work without credentials)
        ("search python on google", False),
        ("search laptop on amazon", False),
        ("search quantum physics on wikipedia", False),
        ("go to facebook.com", False),
        ("open youtube", False),
        
        # With provided credentials (should work)
        ("signup on linkedin with email test@mail.com password test123", False),
        ("login to twitter with username myuser password mypass", False),
        
        # With random data (should work)
        ("create an account on linkedin", True),
        ("signup on github", True),
        
        # Shopping tests
        ("search laptop on amazon and add to cart", False),
        ("buy iphone on flipkart", False),
    ]
    
    for instruction, use_random in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: '{instruction}'")
        print(f"Random Data: {use_random}")
        print('-'*50)
        
        parser = UniversalParser(use_random_data=use_random)
        actions = parser.parse(instruction)
        
        if actions and actions[0].get("action") == "error":
            error_msg = actions[0].get("error", "Unknown error")
            print(f"❌ Result: ERROR - {error_msg}")
            
            suggestion = actions[0].get("suggestion", "")
            if suggestion:
                print(f"💡 Suggestion: {suggestion}")
        else:
            print(f"✅ Result: SUCCESS - {len(actions)} actions generated")
            for i, action in enumerate(actions[:5], 1):
                desc = action.get('description', action.get('action', 'Unknown'))
                print(f"  {i}. {desc}")
            if len(actions) > 5:
                print(f"  ... and {len(actions)-5} more actions")
    
    print(f"\n{'='*60}")
    print("✅ Fixed parser ready!")
    print('='*60)