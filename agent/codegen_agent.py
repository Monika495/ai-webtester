"""
Enhanced Code Generator for NovaQA
Generates Playwright code with smart selectors and error handling
"""

class CodeGenerator:
    """Generates Playwright code with site-specific selectors"""
    
    def generate(self, parsed_actions):
        """Generate Python/Playwright code with smart selectors"""
        lines = [
            "# NovaQA - Auto-generated Test Script",
            "from playwright.sync_api import sync_playwright, TimeoutError",
            "import time",
            "import re",
            "",
            "def run_test(headless=True):",
            "    with sync_playwright() as p:",
            "        browser = p.chromium.launch(headless=headless)",
            "        page = browser.new_page()",
            "        page.set_default_timeout(30000)",
            ""
        ]
        
        # Add helper functions
        lines.extend([
            "        # Helper functions",
            "        def find_and_click(selector):",
            "            try:",
            "                page.wait_for_selector(selector, timeout=5000)",
            "                page.click(selector)",
            "                time.sleep(1)",
            "                return True",
            "            except:",
            "                return False",
            "",
            "        def find_and_type(selector, text):",
            "            try:",
            "                page.wait_for_selector(selector, timeout=5000)",
            "                page.fill(selector, text)",
            "                time.sleep(0.5)",
            "                return True",
            "            except:",
            "                return False",
            "",
            "        def handle_cookies():",
            "            cookie_selectors = [",
            "                'button:has-text(\"Accept all cookies\")',",
            "                'button:has-text(\"Accept cookies\")',",
            "                'button:has-text(\"I accept\")',",
            "                '#sp-cc-accept',  # Amazon",
            "            ]",
            "            for selector in cookie_selectors:",
            "                if find_and_click(selector):",
            "                    print(f'Clicked cookie banner: {selector}')",
            "                    break",
            "",
        ])
        
        action_count = 0
        for action in parsed_actions:
            action_count += 1
            act = action.get("action", "unknown")
            description = action.get("description", "")
            
            if act == "navigate":
                url = action.get("url", "")
                lines.append(f"        # Step {action_count}: Navigate to {url}")
                if description:
                    lines.append(f"        # {description}")
                lines.append(f"        page.goto('{url}')")
                lines.append("        time.sleep(2)")
                lines.append("        handle_cookies()")
                lines.append("")
            
            elif act == "search":
                query = action.get("query", "")
                selector = action.get("selector", "input[name='q']")
                lines.append(f"        # Step {action_count}: Search for '{query}'")
                if description:
                    lines.append(f"        # {description}")
                lines.append(f"        search_selectors = [{selector}]")
                lines.append("        for selector in search_selectors:")
                lines.append("            if find_and_type(selector, f'{query}'):")
                lines.append("                page.keyboard.press('Enter')")
                lines.append("                time.sleep(2)")
                lines.append("                break")
                lines.append("")
            
            elif act == "type":
                field_type = action.get("field_type", "text")
                value = action.get("value", "")
                selector = action.get("selector", "")
                lines.append(f"        # Step {action_count}: Type {field_type}")
                if description:
                    lines.append(f"        # {description}")
                
                if selector:
                    lines.append(f"        selectors = [{selector}]")
                else:
                    # Generate selectors based on field type
                    if field_type == "email":
                        lines.append("        selectors = [")
                        lines.append("            'input[type=\"email\"]',")
                        lines.append("            'input[name=\"email\"]',")
                        lines.append("            'input[placeholder*=\"email\"]',")
                        lines.append("        ]")
                    elif field_type == "password":
                        lines.append("        selectors = [")
                        lines.append("            'input[type=\"password\"]',")
                        lines.append("            'input[name=\"password\"]',")
                        lines.append("        ]")
                    elif field_type == "username":
                        lines.append("        selectors = [")
                        lines.append("            'input[name=\"username\"]',")
                        lines.append("            'input[autocomplete=\"username\"]',")
                        lines.append("        ]")
                    elif field_type == "name":
                        lines.append("        selectors = [")
                        lines.append("            'input[name=\"name\"]',")
                        lines.append("            'input[placeholder*=\"name\"]',")
                        lines.append("        ]")
                    else:
                        lines.append("        selectors = ['input[type=\"text\"]']")
                
                lines.append("        for selector in selectors:")
                lines.append(f"            if find_and_type(selector, '{value}'):")
                lines.append("                break")
                lines.append("")
            
            elif act == "click":
                text = action.get("text", "")
                selector = action.get("selector", "")
                lines.append(f"        # Step {action_count}: Click '{text}'")
                if description:
                    lines.append(f"        # {description}")
                
                if selector:
                    lines.append(f"        selectors = [{selector}]")
                elif text:
                    lines.append(f"        selectors = [")
                    lines.append(f"            'button:has-text(\"{text}\")',")
                    lines.append(f"            'a:has-text(\"{text}\")',")
                    lines.append(f"            'div[role=\"button\"]:has-text(\"{text}\")',")
                    lines.append(f"        ]")
                else:
                    lines.append("        selectors = ['button[type=\"submit\"]']")
                
                lines.append("        for selector in selectors:")
                lines.append("            if find_and_click(selector):")
                lines.append("                break")
                lines.append("")
            
            elif act == "wait":
                seconds = action.get("seconds", 2)
                lines.append(f"        # Step {action_count}: Wait {seconds} seconds")
                lines.append(f"        time.sleep({seconds})")
                lines.append("")
            
            elif act == "select":
                field_type = action.get("field_type", "")
                value = action.get("value", "")
                selector = action.get("selector", "")
                lines.append(f"        # Step {action_count}: Select {field_type}")
                if description:
                    lines.append(f"        # {description}")
                lines.append(f"        try:")
                lines.append(f"            page.wait_for_selector('{selector}', timeout=5000)")
                lines.append(f"            page.select_option('{selector}', value='{value}')")
                lines.append(f"            time.sleep(0.5)")
                lines.append(f"        except:")
                lines.append(f"            print('Failed to select {field_type}')")
                lines.append("")
            
            elif act == "validate_page":
                validation_type = action.get("type", "generic")
                text = action.get("text", "")
                lines.append(f"        # Step {action_count}: Validate page")
                if description:
                    lines.append(f"        # {description}")
                lines.append("        time.sleep(2)")
                lines.append("        page_content = page.content().lower()")
                lines.append("        page_text = page.inner_text('body').lower()")
                lines.append("        full_content = page_content + ' ' + page_text")
                lines.append("")
                
                if validation_type == "login":
                    lines.append("        # Check for login success indicators")
                    lines.append("        success_patterns = [")
                    lines.append("            r'@[a-zA-Z0-9_]{1,15}',")
                    lines.append("            'profile',")
                    lines.append("            'logout',")
                    lines.append("            'dashboard',")
                    lines.append("        ]")
                    lines.append("        for pattern in success_patterns:")
                    lines.append("            if re.search(pattern, full_content, re.IGNORECASE):")
                    lines.append("                print(f'Found login indicator: {pattern}')")
                    lines.append("")
                
                elif validation_type == "signup":
                    lines.append("        # Check for signup success indicators")
                    lines.append("        success_patterns = [")
                    lines.append("            'confirm your email',")
                    lines.append("            'verify your email',")
                    lines.append("            'check your inbox',")
                    lines.append("            'account created',")
                    lines.append("        ]")
                    lines.append("        for pattern in success_patterns:")
                    lines.append("            if re.search(pattern, full_content, re.IGNORECASE):")
                    lines.append("                print(f'Found signup indicator: {pattern}')")
                    lines.append("")
                
                if text:
                    lines.append(f"        # Check for specific text: '{text}'")
                    lines.append(f"        if '{text.lower()}' in full_content:")
                    lines.append(f"            print('Found text: {text}')")
                    lines.append("")
            
            else:
                lines.append(f"        # Step {action_count}: Unknown action - {act}")
                lines.append("        print(f'Unknown action: {act}')")
                lines.append("")
        
        # Add completion and cleanup
        lines.extend([
            "        # Test completion",
            "        print('Test execution completed')",
            "        time.sleep(2)",
            "        browser.close()",
            "",
            "if __name__ == '__main__':",
            "    print('Starting NovaQA generated test...')",
            "    run_test(headless=False)",
            "    print('Test finished!')",
        ])
        
        return "\n".join(lines)


# Test the code generator
if __name__ == "__main__":
    generator = CodeGenerator()
    
    # Test with sample actions
    test_actions = [
        {
            "action": "navigate",
            "url": "https://amazon.com",
            "description": "Navigate to Amazon"
        },
        {
            "action": "search",
            "query": "laptop",
            "selector": "#twotabsearchtextbox",
            "description": "Search for laptop"
        },
        {
            "action": "wait",
            "seconds": 3
        }
    ]
    
    code = generator.generate(test_actions)
    print("Generated Code:")
    print("=" * 60)
    print(code)
    print("=" * 60)