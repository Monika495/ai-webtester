"""
Universal AI Parser - Understands ANY Natural Language Instruction
Uses Gemini AI with structured JSON output
"""

import os
import json
import re


class InstructionParser:
    """
    AI-Powered parser that understands ANY natural language
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
            print("⚠️ No GEMINI_API_KEY. Using regex fallback.")
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
                print("🤖 AI ENABLED - Universal NL Understanding")
            else:
                print("⚠️ AI test failed. Using regex.")
        
        except Exception as e:
            print(f"⚠️ AI init failed: {str(e)[:100]}")
            print("⚠️ Using regex.")
    
    def parse(self, instruction: str):
        """Parse ANY natural language instruction"""
        instruction = instruction.strip()
        
        if self.use_ai and self.client:
            try:
                return self._parse_with_ai(instruction)
            except Exception as e:
                print(f"⚠️ AI failed: {str(e)[:100]}")
                print("⚠️ Fallback to regex...")
        
        return self._parse_with_regex(instruction)
    
    def _parse_with_ai(self, instruction: str):
        """Use Gemini to understand ANY instruction"""
        
        prompt = f"""You are a browser automation AI. Convert ANY user instruction into browser automation steps.

USER INSTRUCTION:
"{instruction}"

RULES:
1. Understand the USER'S INTENT
2. Generate SIMPLE, EXECUTABLE actions
3. Return ONLY valid JSON array
4. NO explanations, NO markdown

AVAILABLE ACTIONS:

{{"action": "navigate", "url": "https://site.com"}}
- Use for: open, go to, visit, navigate, browse, reach, access ANY website
- ALWAYS add https:// if missing
- Examples: "google.com" → "https://google.com"

{{"action": "search", "query": "search term"}}
- Use for: search, find, look for, query, lookup anything on current page

{{"action": "click", "text": "button/link text"}}
- Use for: click, press, tap any button or link

{{"action": "type", "field": "username|password|email|search", "value": "text"}}
- Use for: type, enter, fill any text field

{{"action": "wait", "seconds": 2}}
- Use for: wait, pause, sleep

EXAMPLES:

Input: "navigate to google.com"
[{{"action": "navigate", "url": "https://google.com"}}]

Input: "go to youtube"
[{{"action": "navigate", "url": "https://youtube.com"}}]

Input: "open facebook"
[{{"action": "navigate", "url": "https://facebook.com"}}]

Input: "visit amazon.in"
[{{"action": "navigate", "url": "https://amazon.in"}}]

Input: "search python on google"
[
  {{"action": "navigate", "url": "https://google.com"}},
  {{"action": "search", "query": "python"}}
]

Input: "find machine learning on youtube"
[
  {{"action": "navigate", "url": "https://youtube.com"}},
  {{"action": "search", "query": "machine learning"}}
]

Input: "login to facebook with username john password secret"
[
  {{"action": "navigate", "url": "https://facebook.com/login"}},
  {{"action": "type", "field": "username", "value": "john"}},
  {{"action": "type", "field": "password", "value": "secret"}},
  {{"action": "click", "text": "Login"}}
]

Input: "go to amazon and search laptop"
[
  {{"action": "navigate", "url": "https://amazon.com"}},
  {{"action": "search", "query": "laptop"}}
]

NOW CONVERT THIS INSTRUCTION:
"{instruction}"

Return ONLY the JSON array:"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Clean response
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        
        if start >= 0 and end > start:
            text = text[start:end]
        
        actions = json.loads(text)
        
        if not actions:
            raise Exception("AI returned empty")
        
        print(f"✅ AI parsed {len(actions)} actions")
        return actions
    
    def _parse_with_regex(self, instruction: str):
        """Regex fallback"""
        print("🔍 Regex parser...")
        
        inst = instruction.lower().strip()
        actions = []
        
        # Simple navigation: "go to X", "open X", "visit X", "navigate to X"
        nav_match = re.search(
            r"(go to|open|visit|navigate to|browse to|access|reach)\s+([\w\.-]+)",
            inst
        )
        
        if nav_match:
            site = nav_match.group(2).strip()
            url = site if site.startswith("http") else f"https://{site}"
            
            actions.append({
                "action": "navigate",
                "url": url
            })
            
            print(f"✅ Regex: navigate to {url}")
            return actions
        
        # Search pattern: "search X on Y"
        search_match = re.search(
            r"(search|find|look for)\s+(.+?)\s+(on|in)\s+([\w\.-]+)",
            inst
        )
        
        if search_match:
            query = search_match.group(2).strip()
            site = search_match.group(4).strip()
            url = site if site.startswith("http") else f"https://{site}"
            
            actions.append({
                "action": "navigate",
                "url": url
            })
            actions.append({
                "action": "search",
                "query": query
            })
            
            print(f"✅ Regex: search {query} on {site}")
            return actions
        
        # Unknown
        print("❌ Could not parse")
        actions.append({
            "action": "unknown",
            "instruction": instruction
        })
        
        return actions


# TEST
if __name__ == "__main__":
    parser = InstructionParser()
    
    tests = [
        "navigate to google.com",
        "go to youtube",
        "open facebook",
        "visit amazon.in",
        "search python on google",
        "find AI on youtube",
    ]
    
    for test in tests:
        print(f"\n📝 {test}")
        actions = parser.parse(test)
        for a in actions:
            print(f"   → {a}")