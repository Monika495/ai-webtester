"""
Advanced AI Parser with Support for Complex Multi-Step Actions
Handles login, signup, shopping, forms, etc.
"""

import os
import json
import re


class InstructionParser:
    """
    AI-Powered parser for complex browser automation
    """
    
    def __init__(self, api_key=None):
        self.use_ai = False
        self.client = None
        self.model_name = "gemini-1.5-flash"
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._init_ai()
    
    def _init_ai(self):
        """Initialize Gemini AI"""
        if not self.api_key:
            print("⚠️ No GEMINI_API_KEY found. Using regex fallback.")
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
                print("🤖 AI MODE ENABLED - Advanced Multi-Action Understanding")
            else:
                print("⚠️ AI test failed. Using regex fallback.")
        
        except Exception as e:
            print(f"⚠️ AI init failed: {str(e)[:100]}")
            print("⚠️ Using regex fallback.")
    
    def parse(self, instruction: str):
        """Parse ANY natural language instruction"""
        instruction = instruction.strip()
        
        # Try AI first
        if self.use_ai and self.client:
            try:
                return self._parse_with_ai(instruction)
            except Exception as e:
                print(f"⚠️ AI parsing failed: {str(e)[:100]}")
                print("⚠️ Falling back to regex...")
        
        # Fallback to regex
        return self._parse_with_regex(instruction)
    
    def _parse_with_ai(self, instruction: str):
        """Use Gemini to understand complex instructions"""
        
        prompt = f"""You are a browser automation expert. Convert user instructions into executable browser actions.

USER INSTRUCTION:
"{instruction}"

AVAILABLE ACTIONS:

1. navigate - Go to a website
   {{"action": "navigate", "url": "https://example.com", "description": "..."}}

2. search - Search on current page
   {{"action": "search", "query": "search term", "description": "..."}}

3. login - Login to a website (IMPORTANT: This is ONE action that handles the full login flow)
   {{"action": "login", "site": "facebook", "username": "user", "password": "pass", "description": "..."}}

4. signup - Register on a website (IMPORTANT: This is ONE action that handles the full signup flow)
   {{"action": "signup", "site": "twitter", "username": "user", "password": "pass", "email": "user@email.com", "description": "..."}}

5. click - Click a button/link
   {{"action": "click", "text": "button text", "description": "..."}}

6. fill_field - Fill a single form field
   {{"action": "fill_field", "field_type": "username|password|email", "value": "...", "description": "..."}}

7. add_to_cart - Add item to shopping cart
   {{"action": "add_to_cart", "item": "product name", "description": "..."}}

8. checkout - Proceed to checkout
   {{"action": "checkout", "description": "..."}}

9. wait - Wait for seconds
   {{"action": "wait", "seconds": 2, "description": "..."}}

CRITICAL UNDERSTANDING RULES:

🔐 LOGIN/SIGNUP:
- "login to X", "signin to X", "sign in to X" → login action
- "signup on X", "register on X", "create account on X" → signup action
- Login/signup is ONE COMPLETE action (not navigate + click + fill)
- Extract: site, username, password, email

🛒 SHOPPING:
- "search X and add to cart" → search + add_to_cart
- "search X and buy" → search + add_to_cart + checkout
- "order X", "buy X" → search + add_to_cart + checkout

🔍 SEARCH:
- "search X on Y" → navigate + search
- "find X on Y" → navigate + search
- "look for X" → search (on current page)

EXAMPLES:

Input: "login to facebook with username john password secret"
Output: [
  {{"action": "login", "site": "facebook", "username": "john", "password": "secret", "description": "Login to Facebook with credentials"}}
]

Input: "signup on twitter with username test password pass123 email test@email.com"
Output: [
  {{"action": "signup", "site": "twitter", "username": "test", "password": "pass123", "email": "test@email.com", "description": "Create account on Twitter"}}
]

Input: "register on gmail with email john@gmail.com password mypass"
Output: [
  {{"action": "signup", "site": "gmail", "email": "john@gmail.com", "password": "mypass", "description": "Register on Gmail"}}
]

Input: "go to amazon and search laptop and add to cart"
Output: [
  {{"action": "navigate", "url": "https://amazon.com", "description": "Navigate to Amazon"}},
  {{"action": "search", "query": "laptop", "description": "Search for laptop"}},
  {{"action": "add_to_cart", "item": "laptop", "description": "Add laptop to cart"}}
]

Input: "open amazon and search phone and click buy now"
Output: [
  {{"action": "navigate", "url": "https://amazon.com", "description": "Navigate to Amazon"}},
  {{"action": "search", "query": "phone", "description": "Search for phone"}},
  {{"action": "add_to_cart", "item": "phone", "description": "Add phone to cart"}},
  {{"action": "checkout", "description": "Proceed to checkout"}}
]

Input: "search python on google"
Output: [
  {{"action": "navigate", "url": "https://google.com", "description": "Navigate to Google"}},
  {{"action": "search", "query": "python", "description": "Search for python"}}
]

IMPORTANT:
- Return ONLY JSON array
- No markdown, no explanations
- Add https:// to URLs
- Login/signup are SINGLE actions (not multi-step)
- Shopping involves search + add_to_cart + optional checkout

Convert the instruction above:"""

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
        
        if not actions:
            raise Exception("AI returned empty actions")
        
        print(f"✅ AI parsed {len(actions)} actions")
        return actions
    
    def _parse_with_regex(self, instruction: str):
        """Regex fallback for common patterns"""
        print("🔍 Using regex fallback parser...")
        
        instruction_lower = instruction.lower().strip()
        actions = []
        
        # ==================== LOGIN ====================
        login_match = re.search(
            r"(login|signin|sign in)\s+to\s+([\w\.]+)(?:.*?username\s+([\w]+))?(?:.*?password\s+([\w]+))?",
            instruction_lower
        )
        
        if login_match:
            site = login_match.group(2)
            username = login_match.group(3) or "testuser"
            password = login_match.group(4) or "testpass"
            
            actions.append({
                "action": "login",
                "site": site,
                "username": username,
                "password": password,
                "description": f"Login to {site}"
            })
            
            print(f"✅ Regex parsed login action")
            return actions
        
        # ==================== SIGNUP ====================
        signup_match = re.search(
            r"(signup|register|sign up|create account)\s+on\s+([\w\.]+)(?:.*?username\s+([\w]+))?(?:.*?password\s+([\w]+))?(?:.*?email\s+([\w@\.]+))?",
            instruction_lower
        )
        
        if signup_match:
            site = signup_match.group(2)
            username = signup_match.group(3) or "testuser"
            password = signup_match.group(4) or "testpass"
            email = signup_match.group(5) or "test@email.com"
            
            actions.append({
                "action": "signup",
                "site": site,
                "username": username,
                "password": password,
                "email": email,
                "description": f"Signup on {site}"
            })
            
            print(f"✅ Regex parsed signup action")
            return actions
        
        # ==================== SHOPPING ====================
        shopping_match = re.search(
            r"(?:go to|open|visit)\s+([\w\.]+)\s+and\s+search\s+(.+?)\s+and\s+(add to cart|buy|order|checkout|click buy)",
            instruction_lower
        )
        
        if shopping_match:
            site = shopping_match.group(1)
            query = shopping_match.group(2).strip()
            action_type = shopping_match.group(3)
            
            url = site if site.startswith("http") else f"https://{site}"
            
            actions.append({
                "action": "navigate",
                "url": url,
                "description": f"Navigate to {site}"
            })
            
            actions.append({
                "action": "search",
                "query": query,
                "description": f"Search for {query}"
            })
            
            actions.append({
                "action": "add_to_cart",
                "item": query,
                "description": f"Add {query} to cart"
            })
            
            if "buy" in action_type or "order" in action_type or "checkout" in action_type:
                actions.append({
                    "action": "checkout",
                    "description": "Proceed to checkout"
                })
            
            print(f"✅ Regex parsed shopping actions")
            return actions
        
        # ==================== SIMPLE SEARCH ====================
        search_match = re.search(
            r"(search|find)\s+(.+?)\s+(on|in)\s+([\w\.-]+)",
            instruction_lower
        )
        
        if search_match:
            query = search_match.group(2).strip()
            site = search_match.group(4).strip()
            
            url = site if site.startswith("http") else f"https://{site}"
            
            actions.append({
                "action": "navigate",
                "url": url,
                "description": f"Navigate to {url}"
            })
            
            actions.append({
                "action": "search",
                "query": query,
                "description": f"Search for {query}"
            })
            
            print(f"✅ Regex parsed search actions")
            return actions
        
        # ==================== SIMPLE NAVIGATION ====================
        nav_match = re.search(
            r"(open|visit|go to|navigate to)\s+([\w\.-]+)(?:\s+and\s+(search|find)\s+(.+))?",
            instruction_lower
        )
        
        if nav_match:
            site = nav_match.group(2).strip()
            query = nav_match.group(4).strip() if nav_match.group(4) else None
            
            url = site if site.startswith("http") else f"https://{site}"
            
            actions.append({
                "action": "navigate",
                "url": url,
                "description": f"Navigate to {url}"
            })
            
            if query:
                actions.append({
                    "action": "search",
                    "query": query,
                    "description": f"Search for {query}"
                })
            
            print(f"✅ Regex parsed navigation actions")
            return actions
        
        # ==================== FALLBACK ====================
        print("❌ Could not parse instruction")
        actions.append({
            "action": "unknown",
            "target": instruction,
            "description": "Could not parse instruction"
        })
        
        return actions