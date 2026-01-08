import re

class InstructionParser:
    """
    Parses natural language instructions into structured actions.
    Example: "open google.com and search iphone" -> [open_url, type_text]
    """
    
    def __init__(self):
        pass

    def parse(self, instruction: str):
        """
        Convert natural language to structured actions
        """
        instruction = instruction.strip()
        instruction_lower = instruction.lower()
        actions = []

        # Pattern: "open <website> and search <query>"
        match = re.search(r"open\s+([\w\.-]+)\s+and\s+search\s+(.+)", instruction_lower)
        
        if match:
            site = match.group(1).strip()
            query = match.group(2).strip()
            
            # Add https:// if not present
            if not site.startswith("http"):
                url = f"https://{site}"
            else:
                url = site
            
            # Action 1: Open the website
            actions.append({
                "action": "open_url",
                "target": url,
                "description": f"Navigate to {url}"
            })
            
            # Action 2: Search for the query
            actions.append({
                "action": "type_text",
                "target": {
                    "value": query,
                    "selector": None  # Will be auto-detected
                },
                "description": f"Search for '{query}'"
            })
            
            return actions
        
        # Pattern: "navigate to <website> and search <query>"
        match = re.search(r"navigate\s+to\s+([\w\.-]+)\s+and\s+search\s+(.+)", instruction_lower)
        
        if match:
            site = match.group(1).strip()
            query = match.group(2).strip()
            
            if not site.startswith("http"):
                url = f"https://{site}"
            else:
                url = site
            
            actions.append({
                "action": "open_url",
                "target": url,
                "description": f"Navigate to {url}"
            })
            
            actions.append({
                "action": "type_text",
                "target": {
                    "value": query,
                    "selector": None
                },
                "description": f"Search for '{query}'"
            })
            
            return actions
        
        # Pattern: Just "open <website>"
        match = re.search(r"open\s+([\w\.-]+)", instruction_lower)
        
        if match:
            site = match.group(1).strip()
            if not site.startswith("http"):
                url = f"https://{site}"
            else:
                url = site
            
            actions.append({
                "action": "open_url",
                "target": url,
                "description": f"Navigate to {url}"
            })
            
            return actions
        
        # Fallback: treat as unknown
        actions.append({
            "action": "unknown",
            "target": instruction,
            "description": "Could not parse instruction"
        })
        
        return actions