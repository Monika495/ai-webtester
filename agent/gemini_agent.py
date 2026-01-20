"""
Gemini AI Agent for Natural Language Understanding
Uses Google's Gemini AI to parse any natural language instruction into structured actions
"""
import os
import google.generativeai as genai
import re
from typing import Dict, List, Any
import json

class GeminiAgent:
    """
    Main agent that uses Gemini AI to understand any natural language instruction
    """
    
    def __init__(self, api_key=None):
        # Try to get API key from environment or use placeholder
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found. Using fallback parser.")
            self.use_gemini = False
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.use_gemini = True
        
        # Site configuration patterns
        self.site_patterns = {
            "login": {
                "facebook": {
                    "url": "https://www.facebook.com/login",
                    "username_selector": "#email",
                    "password_selector": "#pass",
                    "submit_selector": "#loginbutton",
                    "patterns": ["facebook", "fb"]
                },
                "instagram": {
                    "url": "https://www.instagram.com/accounts/login/",
                    "username_selector": "input[name='username']",
                    "password_selector": "input[name='password']",
                    "submit_selector": "button[type='submit']",
                    "patterns": ["instagram", "insta"]
                },
                "twitter": {
                    "url": "https://twitter.com/i/flow/login",
                    "username_selector": "input[name='text']",
                    "password_selector": "input[name='password']",
                    "submit_selector": "button[data-testid='LoginForm_Login_Button']",
                    "patterns": ["twitter", "x.com", "tweet"]
                },
                "gmail": {
                    "url": "https://accounts.google.com/",
                    "username_selector": "#identifierId",
                    "next_selector": "#identifierNext",
                    "password_selector": "input[name='password']",
                    "submit_selector": "#passwordNext",
                    "patterns": ["gmail", "google account"]
                },
                "linkedin": {
                    "url": "https://www.linkedin.com/login",
                    "username_selector": "#username",
                    "password_selector": "#password",
                    "submit_selector": "button[type='submit']",
                    "patterns": ["linkedin"]
                }
            },
            "signup": {
                "facebook": {
                    "url": "https://www.facebook.com/r.php",
                    "patterns": ["facebook signup", "fb register"]
                },
                "twitter": {
                    "url": "https://twitter.com/i/flow/signup",
                    "patterns": ["twitter signup", "twitter register"]
                },
                "instagram": {
                    "url": "https://www.instagram.com/accounts/emailsignup/",
                    "patterns": ["instagram signup"]
                }
            },
            "shopping": {
                "amazon": {
                    "url": "https://www.amazon.com",
                    "search_selector": "#twotabsearchtextbox",
                    "patterns": ["amazon", "amazon.in", "amazon.com"]
                },
                "flipkart": {
                    "url": "https://www.flipkart.com",
                    "search_selector": "input[name='q']",
                    "patterns": ["flipkart"]
                }
            },
            "search": {
                "google": {
                    "url": "https://www.google.com",
                    "search_selector": "textarea[name='q'], input[name='q']",
                    "patterns": ["google"]
                },
                "youtube": {
                    "url": "https://www.youtube.com",
                    "search_selector": "input[name='search_query']",
                    "patterns": ["youtube", "yt"]
                },
                "bing": {
                    "url": "https://www.bing.com",
                    "search_selector": "#sb_form_q",
                    "patterns": ["bing"]
                },
                "wikipedia": {
                    "url": "https://www.wikipedia.org",
                    "search_selector": "#searchInput",
                    "patterns": ["wikipedia", "wiki"]
                }
            }
        }

    def parse_with_gemini(self, instruction: str) -> Dict[str, Any]:
        """
        Parse any natural language instruction using Gemini AI
        """
        prompt = f"""
        You are an AI test automation parser. Convert this natural language instruction into structured JSON.
        
        Instruction: "{instruction}"
        
        Output MUST be valid JSON with this exact structure:
        {{
            "primary_action": "login|signup|search|navigate|shop|click|type|scroll|wait|validate",
            "secondary_actions": [
                {{
                    "action": "open_url|type_text|click|scroll|wait|validate",
                    "target": "URL or selector",
                    "value": "text to type (if applicable)",
                    "description": "human readable description"
                }}
            ],
            "parameters": {{
                "site": "website name",
                "username": "username if provided",
                "password": "password if provided",
                "search_query": "search term if provided",
                "product": "product name if shopping"
            }}
        }}
        
        Rules:
        1. Identify the main action (primary_action)
        2. Break down into sequential steps (secondary_actions)
        3. Extract all parameters from the instruction
        4. For login/signup: include username/password
        5. For search: include search_query
        6. For shopping: include product name
        7. Use generic selectors if site-specific not known
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_str = self._extract_json(response.text)
            return json.loads(json_str)
        except Exception as e:
            print(f"Gemini parsing failed: {e}")
            # Fallback to rule-based parsing
            return self.parse_with_rules(instruction)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from Gemini response"""
        # Look for JSON pattern
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group()
        
        # If no JSON found, create a basic structure
        return json.dumps({
            "primary_action": "unknown",
            "secondary_actions": [],
            "parameters": {}
        })
    
    def parse_with_rules(self, instruction: str) -> Dict[str, Any]:
        """
        Fallback rule-based parser when Gemini is not available
        """
        instruction_lower = instruction.lower()
        
        # Check for login patterns
        for site, config in self.site_patterns["login"].items():
            for pattern in config["patterns"]:
                if pattern in instruction_lower and ("login" in instruction_lower or "signin" in instruction_lower):
                    # Extract credentials
                    username = self._extract_username(instruction)
                    password = self._extract_password(instruction)
                    
                    return {
                        "primary_action": "login",
                        "secondary_actions": [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site} login page"
                            },
                            {
                                "action": "type_text",
                                "target": config.get("username_selector", "input[type='text'], input[type='email']"),
                                "value": username,
                                "description": f"Enter username: {username}"
                            },
                            {
                                "action": "type_text",
                                "target": config.get("password_selector", "input[type='password']"),
                                "value": password,
                                "description": "Enter password"
                            },
                            {
                                "action": "click",
                                "target": config.get("submit_selector", "button[type='submit']"),
                                "value": "",
                                "description": "Click login button"
                            }
                        ],
                        "parameters": {
                            "site": site,
                            "username": username,
                            "password": password
                        }
                    }
        
        # Check for signup patterns
        for site, config in self.site_patterns["signup"].items():
            for pattern in config["patterns"]:
                if pattern in instruction_lower and ("signup" in instruction_lower or "register" in instruction_lower or "create account" in instruction_lower):
                    username = self._extract_username(instruction)
                    password = self._extract_password(instruction)
                    
                    return {
                        "primary_action": "signup",
                        "secondary_actions": [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site} signup page"
                            }
                        ],
                        "parameters": {
                            "site": site,
                            "username": username,
                            "password": password
                        }
                    }
        
        # Check for shopping patterns
        for site, config in self.site_patterns["shopping"].items():
            for pattern in config["patterns"]:
                if pattern in instruction_lower:
                    product = self._extract_product(instruction)
                    
                    if "add to cart" in instruction_lower:
                        actions = [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site}"
                            },
                            {
                                "action": "type_text",
                                "target": config["search_selector"],
                                "value": product,
                                "description": f"Search for {product}"
                            },
                            {
                                "action": "press_key",
                                "target": "",
                                "value": "Enter",
                                "description": "Press Enter to search"
                            },
                            {
                                "action": "click",
                                "target": "div[data-component-type='s-search-result']:first-child",
                                "value": "",
                                "description": "Click first product"
                            },
                            {
                                "action": "click",
                                "target": "#add-to-cart-button, input[value='Add to Cart']",
                                "value": "",
                                "description": "Add to cart"
                            }
                        ]
                    elif "buy now" in instruction_lower or "order now" in instruction_lower:
                        actions = [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site}"
                            },
                            {
                                "action": "type_text",
                                "target": config["search_selector"],
                                "value": product,
                                "description": f"Search for {product}"
                            },
                            {
                                "action": "press_key",
                                "target": "",
                                "value": "Enter",
                                "description": "Press Enter to search"
                            },
                            {
                                "action": "click",
                                "target": "div[data-component-type='s-search-result']:first-child",
                                "value": "",
                                "description": "Click first product"
                            },
                            {
                                "action": "click",
                                "target": "#buy-now-button, input[value='Buy Now']",
                                "value": "",
                                "description": "Click Buy Now"
                            }
                        ]
                    else:
                        # Just search
                        actions = [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site}"
                            },
                            {
                                "action": "type_text",
                                "target": config["search_selector"],
                                "value": product,
                                "description": f"Search for {product}"
                            },
                            {
                                "action": "press_key",
                                "target": "",
                                "value": "Enter",
                                "description": "Press Enter to search"
                            }
                        ]
                    
                    return {
                        "primary_action": "shop",
                        "secondary_actions": actions,
                        "parameters": {
                            "site": site,
                            "product": product,
                            "action": "add_to_cart" if "add to cart" in instruction_lower else "buy_now" if "buy now" in instruction_lower else "search"
                        }
                    }
        
        # Check for search patterns
        for site, config in self.site_patterns["search"].items():
            for pattern in config["patterns"]:
                if pattern in instruction_lower or "search" in instruction_lower:
                    # Extract search query
                    search_query = self._extract_search_query(instruction)
                    
                    return {
                        "primary_action": "search",
                        "secondary_actions": [
                            {
                                "action": "open_url",
                                "target": config["url"],
                                "value": "",
                                "description": f"Navigate to {site}"
                            },
                            {
                                "action": "type_text",
                                "target": config["search_selector"],
                                "value": search_query,
                                "description": f"Search for: {search_query}"
                            },
                            {
                                "action": "press_key",
                                "target": "",
                                "value": "Enter",
                                "description": "Press Enter to search"
                            }
                        ],
                        "parameters": {
                            "site": site,
                            "search_query": search_query
                        }
                    }
        
        # Default: simple navigation
        if "open" in instruction_lower or "go to" in instruction_lower or "navigate" in instruction_lower:
            url = self._extract_url(instruction)
            if not url.startswith("http"):
                url = f"https://{url}"
            
            return {
                "primary_action": "navigate",
                "secondary_actions": [
                    {
                        "action": "open_url",
                        "target": url,
                        "value": "",
                        "description": f"Navigate to {url}"
                    }
                ],
                "parameters": {
                    "url": url
                }
            }
        
        # Unknown instruction
        return {
            "primary_action": "unknown",
            "secondary_actions": [
                {
                    "action": "unknown",
                    "target": instruction,
                    "value": "",
                    "description": "Could not parse instruction"
                }
            ],
            "parameters": {}
        }
    
    def _extract_username(self, instruction: str) -> str:
        """Extract username from instruction"""
        patterns = [
            r'username\s+(\w+)',
            r'with\s+username\s+(\w+)',
            r'username:\s*(\w+)',
            r'user\s+(\w+)',
            r'email\s+([\w\.-]+@[\w\.-]+)',
            r'with\s+email\s+([\w\.-]+@[\w\.-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "testuser"  # Default username
    
    def _extract_password(self, instruction: str) -> str:
        """Extract password from instruction"""
        patterns = [
            r'password\s+(\w+)',
            r'with\s+password\s+(\w+)',
            r'password:\s*(\w+)',
            r'pass\s+(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "test123"  # Default password
    
    def _extract_product(self, instruction: str) -> str:
        """Extract product name from shopping instruction"""
        # Remove shopping keywords
        text = instruction.lower()
        for keyword in ["add to cart", "buy now", "order now", "search", "go to", "open", "visit", "browse"]:
            text = text.replace(keyword, "")
        
        # Remove site names
        for site in ["amazon", "flipkart", "ebay", "walmart"]:
            text = text.replace(site, "")
        
        # Remove and, for, on, etc
        for word in ["and", "for", "on", "to", "the", "a", "an"]:
            text = text.replace(f" {word} ", " ")
        
        return text.strip()
    
    def _extract_search_query(self, instruction: str) -> str:
        """Extract search query from instruction"""
        if "search" in instruction.lower():
            parts = instruction.lower().split("search")
            if len(parts) > 1:
                query = parts[1].strip()
                # Remove "on X" patterns
                for site in ["google", "youtube", "bing", "wikipedia"]:
                    query = query.replace(f"on {site}", "").replace(f"in {site}", "")
                return query.strip()
        return instruction
    
    def _extract_url(self, instruction: str) -> str:
        """Extract URL from navigation instruction"""
        patterns = [
            r'open\s+([\w\.-]+\.\w+)',
            r'go\s+to\s+([\w\.-]+\.\w+)',
            r'navigate\s+to\s+([\w\.-]+\.\w+)',
            r'visit\s+([\w\.-]+\.\w+)',
            r'browse\s+to\s+([\w\.-]+\.\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # If no URL found, try to extract domain from instruction
        words = instruction.lower().split()
        for word in words:
            if '.' in word and ' ' not in word:
                return word
        
        return "google.com"  # Default
    
    def parse(self, instruction: str) -> Dict[str, Any]:
        """Main parsing method - tries Gemini first, falls back to rules"""
        if self.use_gemini:
            try:
                return self.parse_with_gemini(instruction)
            except Exception as e:
                print(f"⚠️ Gemini failed, using rule-based: {e}")
                return self.parse_with_rules(instruction)
        else:
            return self.parse_with_rules(instruction)