class CodeGenerator:
    """
    Generates Playwright test code from actions
    """
    
    def generate(self, parsed_actions):
        """
        Create executable Python/Playwright code
        """
        lines = [
            "from playwright.sync_api import sync_playwright",
            "import time",
            "",
            "def run_test(headless=True):",
            "    with sync_playwright() as p:",
            "        browser = p.chromium.launch(headless=headless)",
            "        context = browser.new_context(",
            "            viewport={'width': 1280, 'height': 720}",
            "        )",
            "        page = context.new_page()",
            "        page.set_default_timeout(30000)",
            ""
        ]

        for action in parsed_actions:
            act = action["action"]
            target = action.get("target", {})
            description = action.get("description", "")

            if description:
                lines.append(f"        # {description}")

            if act == "open_url":
                url = target
                lines.append(f"        page.goto('{url}', wait_until='domcontentloaded')")
                lines.append("        time.sleep(2)")
                lines.append("")

            elif act == "type_text":
                value = target.get("value", "")
                selector = target.get("selector")
                
                if selector:
                    lines.append(f"        page.wait_for_selector('{selector}', state='visible')")
                    lines.append(f"        page.fill('{selector}', '{value}')")
                    lines.append("        time.sleep(0.5)")
                    lines.append("        page.keyboard.press('Enter')")
                else:
                    lines.append(f"        # TODO: Find selector for input")
                    lines.append(f"        # page.fill('<selector>', '{value}')")
                lines.append("")

            elif act == "click":
                selector = target.get("selector", "")
                lines.append(f"        page.wait_for_selector('{selector}', state='visible')")
                lines.append(f"        page.click('{selector}')")
                lines.append("")

        lines.append("        browser.close()")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    run_test(headless=False)")

        return "\n".join(lines)
