"""
Assertion utilities for test validation
"""

class AssertionGenerator:
    """
    Generate test assertions
    """
    
    @staticmethod
    def generate_text_assertion(expected_text: str):
        return {
            "action": "assert_text",
            "target": {
                "value": expected_text,
                "type": "contains"
            },
            "description": f"Verify page contains: '{expected_text}'"
        }
    
    @staticmethod
    def generate_url_assertion(expected_url: str):
        return {
            "action": "assert_url",
            "target": {
                "value": expected_url,
                "type": "contains"
            },
            "description": f"Verify URL contains: '{expected_url}'"
        }


def generate_contains_assertion(text: str):
    """
    Helper function for text assertions
    """
    return AssertionGenerator.generate_text_assertion(text)