"""
Simple Universal Executor - Executes ANY parsed action
"""

from playwright.sync_api import sync_playwright
import time


class Executor:
    """
    Simple executor for any browser action
    """
    
    def __init__(self):
        # Common selectors
        self.selectors = {
            "search": [
                "input[type='search']",
                "input[name='q']",
                "textarea[name='q']",
                "input[name='search']",
                "input[placeholder*='Search' i]",
                "input[type='text']",
                "input"
            ],
            "username": [
                "input[name='username']",
                "input[name='user']",
                "input[name='email']",
                "input[type='email']",
                "input[id*='username']",
                "input[id*='email']",
                "input[placeholder*='username' i]",
                "input[placeholder*='email' i]"
            ],
            "password": [
                "input[type='password']",
                "input[name='password']",
                "input[name='pass']",
                "input[placeholder*='password' i]"
            ]
        }
    
    def run(self, parsed_actions, headless=True):
        """Execute all actions"""
        results = []
        
        if not parsed_actions:
            results.append({
                "action": "error",
                "status": "Failed",
                "details": "No actions to execute"
            })
            return results
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            page.set_default_timeout(30000)
            
            for action in parsed_actions:
                act = action.get("action", "unknown")
                
                try:
                    # ========== NAVIGATE ==========
                    if act == "navigate":
                        url = action.get("url", "")
                        
                        if not url:
                            raise Exception("No URL provided")
                        
                        page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        time.sleep(2)
                        
                        results.append({
                            "action": act,
                            "status": "Passed",
                            "details": f"Navigated to {url}"
                        })
                    
                    # ========== SEARCH ==========
                    elif act == "search":
                        query = action.get("query", "")
                        
                        if not query:
                            raise Exception("No search query")
                        
                        found = False
                        for selector in self.selectors["search"]:
                            try:
                                page.wait_for_selector(selector, timeout=3000, state="visible")
                                page.fill(selector, "")
                                page.fill(selector, query)
                                page.keyboard.press("Enter")
                                time.sleep(2)
                                found = True
                                break
                            except:
                                continue
                        
                        if found:
                            results.append({
                                "action": act,
                                "status": "Passed",
                                "details": f"Searched for: {query}"
                            })
                        else:
                            raise Exception("Could not find search box")
                    
                    # ========== TYPE ==========
                    elif act == "type":
                        field = action.get("field", "search")
                        value = action.get("value", "")
                        
                        if not value:
                            raise Exception("No value to type")
                        
                        selectors = self.selectors.get(field, self.selectors["search"])
                        
                        found = False
                        for selector in selectors:
                            try:
                                page.wait_for_selector(selector, timeout=3000, state="visible")
                                page.fill(selector, value)
                                found = True
                                break
                            except:
                                continue
                        
                        if found:
                            results.append({
                                "action": act,
                                "status": "Passed",
                                "details": f"Typed in {field}: {value}"
                            })
                        else:
                            raise Exception(f"Could not find {field} field")
                    
                    # ========== CLICK ==========
                    elif act == "click":
                        text = action.get("text", "")
                        
                        if not text:
                            raise Exception("No text to click")
                        
                        clicked = False
                        
                        strategies = [
                            f"button:has-text('{text}')",
                            f"a:has-text('{text}')",
                            f"text={text}",
                            f"[aria-label*='{text}' i]",
                            "button[type='submit']"
                        ]
                        
                        for strategy in strategies:
                            try:
                                page.click(strategy, timeout=3000)
                                clicked = True
                                time.sleep(2)
                                break
                            except:
                                continue
                        
                        if clicked:
                            results.append({
                                "action": act,
                                "status": "Passed",
                                "details": f"Clicked: {text}"
                            })
                        else:
                            raise Exception(f"Could not find: {text}")
                    
                    # ========== WAIT ==========
                    elif act == "wait":
                        seconds = action.get("seconds", 2)
                        time.sleep(seconds)
                        
                        results.append({
                            "action": act,
                            "status": "Passed",
                            "details": f"Waited {seconds}s"
                        })
                    
                    # ========== UNKNOWN ==========
                    else:
                        results.append({
                            "action": act,
                            "status": "Failed",
                            "details": f"Unknown action: {act}"
                        })
                
                except Exception as e:
                    results.append({
                        "action": act,
                        "status": "Failed",
                        "details": f"Error: {str(e)}"
                    })
            
            browser.close()
        
        return results


# TEST
if __name__ == "__main__":
    executor = Executor()
    
    test_actions = [
        {"action": "navigate", "url": "https://google.com"},
        {"action": "search", "query": "python"}
    ]
    
    results = executor.run(test_actions, headless=False)
    
    for r in results:
        print(f"{r['action']}: {r['status']} - {r['details']}")