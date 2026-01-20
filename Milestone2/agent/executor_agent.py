from playwright.sync_api import sync_playwright
import time

class Executor:
    """
    Executes test actions using Playwright browser automation
    """
    
    def __init__(self):
        # Site-specific selectors for popular websites
        self.site_selectors = {
            "google": [
                "textarea[name='q']",
                "input[name='q']",
                "input[type='search']",
                "input[title='Search']"
            ],
            "amazon": [
                "#twotabsearchtextbox",
                "input#twotabsearchtextbox",
                "input[name='field-keywords']",
                "input.nav-input"
            ],
            "wikipedia": [
                "input[name='search']",
                "#searchInput",
                "input[type='search']"
            ],
            "youtube": [
                "input#search",
                "input[name='search_query']"
            ],
            "bing": [
                "input#sb_form_q",
                "input[name='q']"
            ]
        }

    def find_input_element(self, page, url):
        """
        Intelligently find search input on any website
        """
        url_lower = url.lower()
        
        # Step 1: Try site-specific selectors
        for site_name, selectors in self.site_selectors.items():
            if site_name in url_lower:
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000, state="visible")
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            return selector
                    except:
                        continue
        
        # Step 2: Try generic selectors
        generic_selectors = [
            "input[type='text']",
            "input[type='search']",
            "input[name*='search']",
            "input[name*='q']",
            "textarea[name*='search']"
        ]
        
        for selector in generic_selectors:
            try:
                elements = page.query_selector_all(selector)
                for element in elements:
                    if element.is_visible() and element.is_enabled():
                        # Get unique selector
                        elem_id = element.get_attribute("id")
                        if elem_id:
                            return f"#{elem_id}"
                        
                        name = element.get_attribute("name")
                        if name:
                            tag = element.evaluate("el => el.tagName.toLowerCase()")
                            return f"{tag}[name='{name}']"
                        
                        return selector
            except:
                continue
        
        # Step 3: Find any visible input
        try:
            all_inputs = page.query_selector_all("input, textarea")
            for inp in all_inputs:
                if inp.is_visible() and inp.is_enabled():
                    input_type = inp.get_attribute("type") or "text"
                    if input_type in ["text", "search", "email", ""]:
                        elem_id = inp.get_attribute("id")
                        if elem_id:
                            return f"#{elem_id}"
                        return "input"
        except:
            pass
        
        return None

    def run(self, parsed_actions, headless=True):
        """
        Execute all actions and return results
        """
        results = []
        current_url = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            page.set_default_timeout(30000)

            for action in parsed_actions:
                act = action["action"]
                target = action.get("target", {})
                description = action.get("description", "")

                try:
                    if act == "open_url":
                        url = target
                        current_url = url
                        
                        # Open the website
                        page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        time.sleep(2)  # Wait for page to stabilize
                        
                        results.append({
                            "action": act,
                            "status": "Passed",
                            "details": f"Successfully navigated to {url}",
                            "description": description
                        })

                    elif act == "type_text":
                        value = target.get("value", "")
                        
                        # Find the search input
                        selector = self.find_input_element(page, current_url or "")
                        
                        if not selector:
                            raise Exception("Could not find search input box")
                        
                        # Save the selector for code generation
                        target["selector"] = selector
                        
                        # Wait for element
                        page.wait_for_selector(selector, state="visible", timeout=5000)
                        
                        # Clear and type
                        page.fill(selector, "")
                        page.fill(selector, value)
                        time.sleep(0.5)
                        
                        # Press Enter to search
                        page.keyboard.press("Enter")
                        
                        # Wait for results
                        try:
                            page.wait_for_load_state("domcontentloaded", timeout=5000)
                        except:
                            pass
                        
                        results.append({
                            "action": act,
                            "status": "Passed",
                            "details": f"Typed '{value}' in search box [{selector}]",
                            "description": description
                        })

                    elif act == "click":
                        selector = target.get("selector")
                        page.wait_for_selector(selector, state="visible")
                        page.click(selector)
                        
                        results.append({
                            "action": act,
                            "status": "Passed",
                            "details": f"Clicked element: {selector}",
                            "description": description
                        })

                    elif act == "unknown":
                        results.append({
                            "action": act,
                            "status": "Failed",
                            "details": "Could not parse instruction",
                            "description": description
                        })

                except Exception as e:
                    results.append({
                        "action": act,
                        "status": "Failed",
                        "details": f"Error: {str(e)}",
                        "description": description
                    })

            browser.close()

        return results
