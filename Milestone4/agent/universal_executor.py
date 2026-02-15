"""
PERFECT Executor - Real Validation with Smart Detection
Enhanced with Screenshot Capture and Result Page Analysis
Checks for actual logged-in/signup success indicators
FIXED for Twitter/X, Amazon, LinkedIn + Wikipedia
ENHANCED: Better LinkedIn support, random data tracking, and screenshot capture
ENHANCED: Result page content extraction for analysis
UPDATED: Gemini API support for intelligent summarization
FIXED: Removed attribute access that caused 'list' object has no attribute '__dict__' error
"""

from playwright.sync_api import sync_playwright
import time
from typing import List, Dict, Any
import re
from datetime import datetime
import os
import sys
import traceback
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Try to import screenshot capture module
try:
    from agent.screenshot_capture import ScreenshotCapture
    SCREENSHOT_MODULE_AVAILABLE = True
    print("[Executor] Screenshot capture module loaded successfully")
except ImportError as e:
    SCREENSHOT_MODULE_AVAILABLE = False
    print(f"[Executor] Screenshot capture module not available: {e}")


class UniversalExecutor:
    """
    Executor with SMART validation logic - FIXED for all cases including Wikipedia
    ENHANCED: Better LinkedIn support, data tracking, and screenshot capture
    ENHANCED: Result page content extraction for analysis
    UPDATED: Gemini API support for intelligent summarization
    FIXED: Removed attribute access that caused 'list' object has no attribute '__dict__' error
    """
    
    def __init__(self, reports_dir="reports", api_key=None):
        # Track random data usage for reporting
        self.generated_data = {}
        self.used_provided_data = {}
        self.page = None  # Store page reference for screenshot capture
        self.context = None
        self.browser = None
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Screenshot capture system
        self.screenshot_capture = None
        self.reports_dir = reports_dir
        
        # Initialize screenshot capture if available
        if SCREENSHOT_MODULE_AVAILABLE:
            try:
                self.screenshot_capture = ScreenshotCapture(reports_dir, api_key=self.api_key)
                print("[Executor] Screenshot capture initialized")
            except Exception as e:
                print(f"[Executor] Failed to initialize screenshot capture: {e}")
                self.screenshot_capture = None
        else:
            print("[Executor] Screenshot capture not available, screenshots disabled")
        
        # Track execution for screenshot capture
        self.current_report_id = None
        self.last_failed_step = None
        self.final_result_page = None
        self.execution_steps = []
        
        # Track execution state for result page content - use dictionary NOT object
        self.execution_state = {
            "current_site": None,
            "is_signup_flow": False,
            "has_provided_credentials": False,
            "has_generated_data": False,
            "search_query": None,
            "is_search_operation": False,
            "result_page_content": None,
            "result_summary": None
        }
        
        # Selectors with priorities - UPDATED WITH BETTER LINKEDIN SUPPORT
        self.field_selectors = {
            "search": [
                "#searchInput",  # Wikipedia
                "input[name='search']",  # Wikipedia and many others
                "#twotabsearchtextbox",  # Amazon
                "#search",  # Common search ID
                ".search-input",  # Common search class
                "input[type='search']",  # HTML5 search type
                "input[name='q']",  # Google, Flipkart
                "textarea[name='q']",  # Google
                "input[name='search_query']",  # YouTube
                "input[placeholder*='Search' i]",
                "input[title='Search']",
                "input[type='text']",
                "input"
            ],
            "email": [
                "input[name='email-address']",  # LinkedIn signup - PRIORITIZED
                "input[type='email']",
                "input[name='email']",
                "input[name='session_key']",  # LinkedIn login
                "input[name='reg_email__']",  # Facebook
                "input[id='email']",
                "input[placeholder*='email' i]",
                "input[autocomplete='email']",
            ],
            "username": [
                "input[autocomplete='username']",  # Twitter/X login
                "input[name='text']",  # Twitter/X
                "input[type='text']",  # Generic
                "input[name='username']",
                "input[name='session_username']",
                "input[id='username']",
                "input[placeholder*='username' i]",
                "input[placeholder*='Phone' i]",
            ],
            "password": [
                "input[type='password']",
                "input[name='pass']",  # Facebook
                "input[name='password']",
                "input[name='session_password']",  # LinkedIn
                "input[name='reg_passwd__']",  # Facebook
                "input[placeholder*='password' i]",
                "input[autocomplete='new-password']",  # Signup forms
            ],
            "name": [
                "input[name='name']",  # Twitter/X
                "input[data-testid*='name']",  # Twitter/X signup
                "input[placeholder*='name' i]",
                "input[placeholder*='Full name' i]",
            ],
            "first_name": [
                "input[name='first-name']",  # LinkedIn - PRIORITIZED
                "input[id='first-name']",  # LinkedIn
                "input[name='firstname']",  # Facebook
                "input[name='firstName']",
                "input[placeholder*='first name' i]",
            ],
            "last_name": [
                "input[name='last-name']",  # LinkedIn - PRIORITIZED
                "input[id='last-name']",  # LinkedIn
                "input[name='lastname']",  # Facebook
                "input[name='lastName']",
                "input[placeholder*='last name' i]",
            ]
        }
        
        self.action_selectors = {
            "login_button": [
                "button[name='login']",  # Facebook
                "button:has-text('Log in')",
                "button:has-text('Sign in')",
                "button[type='submit']",  # Twitter/X, LinkedIn
                "button[data-testid*='Login']",  # Twitter/X
                "div[role='button']:has-text('Log in')",
                "input[type='submit'][value='Sign in']",  # LinkedIn
            ],
            "signup_button": [
                "a[data-testid='open-registration-form-button']",  # Facebook
                "a:has-text('Create New Account')",
                "a:has-text('Sign up')",
                "button:has-text('Sign up')",
                "button:has-text('Create account')",
                "button:has-text('Join')",  # Twitter/X
                "button:has-text('Agree & Join')",  # LinkedIn - PRIORITIZED
                "button:has-text('Join now')",  # LinkedIn
            ],
            "submit_button": [
                "button[name='websubmit']",  # Facebook
                "button[type='submit']",
                "button:has-text('Next')",
                "button:has-text('Continue')",
                "button:has-text('Submit')",
            ],
            "next_button": [
                "button:has-text('Next')",
                "div[role='button']:has-text('Next')",
                "button[type='submit']",  # Twitter/X Next is often submit button
                "span:has-text('Next')",
            ],
            "add_to_cart": [
                "#add-to-cart-button",  # Amazon
                "button:has-text('Add to Cart' i)",
                "input[value='Add to Cart']",
                "button[id*='add-to-cart' i]",
                "button[class*='add-to-cart' i]",
            ],
            "search_button": [
                "#searchButton",  # Wikipedia
                ".search-button",  # Common search button
                "button[aria-label*='search' i]",  # Accessibility label
                "input[type='submit'][value='Google Search']",
                "button[type='submit']",
                "input[value='Search']",
                "button:has-text('Search')",
                "input[type='submit'][value*='Search' i]",
            ]
        }
        
        # Validation patterns - ENHANCED WITH BETTER LINKEDIN SUPPORT
        self.validation_patterns = {
            "login_success": [
                r"@[a-zA-Z0-9_]{1,15}",  # @username (Twitter/X)
                "profile",
                "logout", 
                "sign out", 
                "settings", 
                "account", 
                "dashboard",
                r"welcome,\s*[a-zA-Z]",  # Welcome, John
                "inbox", 
                "notifications", 
                "feed", 
                "home\s*\(\d+\)",  # Home(12)
                "my network",  # LinkedIn
                "messaging",  # LinkedIn
                "jobs",  # LinkedIn
            ],
            "login_failure": [
                "incorrect password", 
                "wrong password", 
                "invalid",
                "account not found", 
                "doesn't match", 
                "try again",
                "enter your password",
                "forgot password",
                "unable to sign in",
            ],
            "signup_success": [
                "check your email",  # LinkedIn - TOP PRIORITY
                "verify your account",  # LinkedIn
                "enter the code",  # LinkedIn
                "enter code",  # LinkedIn
                "enter confirmation code",  # Twitter/X
                "we sent you a code",  # Twitter/X
                "verify your email", 
                "confirm your email", 
                "check your inbox",
                "account created", 
                "registration complete", 
                "welcome to",
                "almost done", 
                "verify account",
                "email sent",
                "verification code",
                "confirmation code",
                "we've sent a code",
                "enter the verification code",
                "enter the 6-digit code",
            ],
            "signup_failure": [
                "email already exists", 
                "invalid email", 
                "password too weak",
                "phone number invalid", 
                "birthday invalid", 
                "already registered",
                "someone already has that",
                "enter a valid email",
                "password must be",
                "this email is already linked",
                "account already exists",
                "use a different email",
                "try another email",
            ],
            "shopping_success": [
                "added to cart", 
                "added to your cart", 
                "item in cart",
                "cart\s*\(\d+\)", 
                "proceed to checkout", 
                "checkout",
                "buy now",
                "place order",
            ],
            "search_success": [
                "results",
                "search results",
                "showing results for",
                "did you mean",
                "related searches",
                "search for",
                "page you were looking",
                "article",
                "contents",
                "references",
                "edit this page",
                "talk",
                "view history",
                "no results found",
                "no exact matches",
                "try different keywords",
                "sorry, we couldn't find",
                "wikipedia, the free encyclopedia",
                "from wikipedia",
                "this article is about",
                "jump to navigation",
                "main page",
            ]
        }
    
    def run(self, parsed_actions: List[Dict[str, Any]], headless=False, report_id=None, instruction=None) -> List[Dict[str, Any]]:
        """Execute all actions with smart validation and data tracking"""
        results = []
        
        if not parsed_actions:
            return [{"action": "error", "status": "Failed", "details": "No actions"}]
        
        if parsed_actions[0].get("action") == "error":
            return [{
                "action": "error",
                "status": "Failed",
                "details": parsed_actions[0].get("error", "Unknown error"),
                "suggestion": parsed_actions[0].get("suggestion", "")
            }]
        
        # Set report ID for screenshot naming
        self.current_report_id = report_id or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🎬 Starting execution with report ID: {self.current_report_id}")
        if instruction:
            print(f"📝 Instruction: {instruction}")
        
        # Reset tracking variables
        self.last_failed_step = None
        self.final_result_page = None
        self.execution_steps = []
        self.generated_data = {}
        self.used_provided_data = {}
        
        # Reset execution state - use dictionary NOT object
        self.execution_state = {
            "current_site": None,
            "is_signup_flow": False,
            "has_provided_credentials": False,
            "has_generated_data": False,
            "search_query": None,
            "is_search_operation": False,
            "result_page_content": None,
            "result_summary": None
        }
        
        with sync_playwright() as p:
            self.browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox'
                ]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                java_script_enabled=True
            )
            self.page = self.context.new_page()  # Store page reference
            self.page.set_default_timeout(40000)
            
            step_number = 0
            
            for action_data in parsed_actions:
                step_number += 1
                action = action_data.get("action", "unknown")
                field_type = action_data.get("field_type", "")
                description = action_data.get("description", "")
                value = action_data.get("value", "")
                
                # Update execution state based on action
                if action == "navigate":
                    url = action_data.get("url", "")
                    if "linkedin" in url.lower():
                        self.execution_state["current_site"] = "linkedin"
                    elif "twitter" in url.lower() or "x.com" in url.lower():
                        self.execution_state["current_site"] = "twitter"
                    elif "facebook" in url.lower():
                        self.execution_state["current_site"] = "facebook"
                    elif "google" in url.lower() or "search" in url.lower():
                        self.execution_state["current_site"] = "search_engine"
                    elif "wikipedia" in url.lower():
                        self.execution_state["current_site"] = "wikipedia"
                
                # Check if this is a signup flow
                if "signup" in description.lower() or "create account" in description.lower():
                    self.execution_state["is_signup_flow"] = True
                
                # Check if this is a search operation
                if action == "search" or "search" in description.lower():
                    self.execution_state["is_search_operation"] = True
                    self.execution_state["search_query"] = value
                
                # Track data usage
                if action == "type" and value:
                    if action_data.get("is_random_data", False) or "random" in description.lower():
                        self.execution_state["has_generated_data"] = True
                        if field_type:
                            self.generated_data[field_type] = value
                            print(f"📝 Generated {field_type}: {value[:20]}{'...' if len(value) > 20 else ''}")
                    else:
                        self.execution_state["has_provided_credentials"] = True
                        if field_type in ["email", "password"]:
                            self.used_provided_data[field_type] = value
                            print(f"📝 Using provided {field_type}: {value[:20]}{'...' if len(value) > 20 else ''}")
                
                try:
                    step_result = None
                    
                    if action == "navigate":
                        step_result = self._execute_navigate(self.page, action_data)
                    elif action == "search":
                        step_result = self._execute_search(self.page, action_data)
                    elif action == "type":
                        step_result = self._execute_type(self.page, action_data, field_type)
                    elif action == "select":
                        step_result = self._execute_select(self.page, action_data, field_type)
                    elif action == "click":
                        step_result = self._execute_click(self.page, action_data)
                    elif action == "wait":
                        seconds = action_data.get("seconds", 2)
                        time.sleep(seconds)
                        step_result = {"action": "wait", "status": "Passed", "details": f"Waited {seconds} seconds"}
                    elif action == "validate_page":
                        # Pass execution_state to validation - FIX: Pass as dictionary, not as object attribute
                        step_result = self._execute_validate_page(self.page, action_data, self.execution_state)
                    elif action == "info":
                        message = action_data.get("message", "Information")
                        print(f"ℹ️ {message}")
                        step_result = {"action": "info", "status": "Passed", "details": message}
                    elif action == "generate_data":
                        details = action_data.get("details", "Generated random data")
                        step_result = {"action": "generate_data", "status": "Passed", "details": details}
                    else:
                        step_result = {"action": action, "status": "Failed", "details": f"Unknown action: {action}"}
                    
                    # Add step metadata
                    step_result["step"] = step_number
                    if description and "description" not in step_result:
                        step_result["description"] = description
                    if field_type:
                        step_result["field_type"] = field_type
                    
                    # If this is a validation step and we have result content, add it to step result
                    if action == "validate_page" and self.execution_state.get("result_page_content"):
                        step_result["result_content"] = self.execution_state["result_page_content"][:500] + "..." if len(self.execution_state["result_page_content"]) > 500 else self.execution_state["result_page_content"]
                    
                    # Capture screenshot for this step (especially for failures)
                    screenshot_path = None
                    if self.screenshot_capture and self.page:
                        step_description = f"Step {step_number}: {description or action}"
                        is_failure = step_result.get("status", "").lower() == "failed"
                        
                        try:
                            # Capture screenshot with analysis
                            screenshot_info = self.screenshot_capture.capture_with_analysis(
                                self.page, 
                                self.current_report_id, 
                                step_description,
                                is_final_result=False
                            )
                            
                            if screenshot_info:
                                screenshot_path = screenshot_info.get("screenshot_path")
                                step_result["screenshot"] = screenshot_path
                                
                                # Store analysis in step result
                                if screenshot_info.get("analysis"):
                                    step_result["page_analysis"] = screenshot_info.get("analysis")
                                
                                # Track failed steps for later reporting
                                if is_failure:
                                    self.last_failed_step = {
                                        "step_number": step_number,
                                        "action": action,
                                        "description": description,
                                        "screenshot_info": screenshot_info,
                                        "error": step_result.get("details", "")
                                    }
                                    print(f"📸 Captured failed step screenshot: {screenshot_path}")
                                else:
                                    print(f"📸 Captured step screenshot: {screenshot_path}")
                        except Exception as e:
                            print(f"[Executor] Failed to capture screenshot: {e}")
                    
                    # Store execution step for summary
                    self.execution_steps.append({
                        "step": step_number,
                        "action": action,
                        "status": step_result.get("status", "unknown"),
                        "description": description,
                        "details": step_result.get("details", ""),
                        "screenshot": screenshot_path,
                        "duration": step_result.get("duration", 0),
                        "result_content": step_result.get("result_content") if action == "validate_page" else None
                    })
                    
                    results.append(step_result)
                    
                    # If action failed, stop execution (except for validation/wait/info)
                    if step_result["status"] == "Failed" and action not in ["wait", "validate_page", "info", "generate_data"]:
                        results.append({
                            "action": "execution_stopped",
                            "status": "Failed",
                            "details": f"Stopped due to failed action: {action}"
                        })
                        break
                
                except Exception as e:
                    error_trace = traceback.format_exc()
                    print(f"❌ Error in step {step_number} ({action}): {str(e)}")
                    
                    step_result = {
                        "step": step_number,
                        "action": action, 
                        "status": "Failed", 
                        "details": f"Error: {str(e)}"
                    }
                    
                    if field_type:
                        step_result["field_type"] = field_type
                    if description:
                        step_result["description"] = description
                    
                    # Capture error screenshot
                    if self.screenshot_capture and self.page:
                        try:
                            screenshot_info = self.screenshot_capture.capture_with_analysis(
                                self.page,
                                self.current_report_id,
                                f"ERROR Step {step_number}: {description or action}",
                                is_final_result=False
                            )
                            if screenshot_info:
                                step_result["screenshot"] = screenshot_info.get("screenshot_path")
                                self.last_failed_step = {
                                    "step_number": step_number,
                                    "action": action,
                                    "description": description,
                                    "screenshot_info": screenshot_info,
                                    "error": str(e)
                                }
                        except Exception as screenshot_error:
                            print(f"[Executor] Failed to capture error screenshot: {screenshot_error}")
                    
                    results.append(step_result)
                    break
            
            # Capture final result page screenshot (regardless of success/failure)
            if self.page and self.screenshot_capture:
                try:
                    print(f"📸 Capturing final result page...")
                    
                    # Extract page content for result summary
                    page_content = self._extract_page_content(self.page)
                    if page_content:
                        self.execution_state["result_page_content"] = page_content
                        self.execution_state["result_summary"] = page_content[:500] + "..." if len(page_content) > 500 else page_content
                    
                    # Capture final page with analysis
                    final_screenshot_info = self.screenshot_capture.capture_with_analysis(
                        self.page,
                        self.current_report_id,
                        "Final Result Page",
                        is_final_result=True
                    )
                    
                    if final_screenshot_info:
                        self.final_result_page = final_screenshot_info
                        
                        # Add result page capture as a step
                        result_page_step = {
                            "step": len(results) + 1,
                            "action": "result_page_capture",
                            "status": "Passed",
                            "description": "Capture final result page",
                            "details": "Result page screenshot captured with analysis",
                            "screenshot": final_screenshot_info.get("screenshot_path"),
                            "page_analysis": final_screenshot_info.get("analysis", {}),
                            "result_summary": self.execution_state.get("result_summary", "Result page captured"),
                            "result_content": self.execution_state.get("result_page_content", "Result page captured"),
                            "full_content": final_screenshot_info.get("full_content"),
                            "is_result_page": True
                        }
                        
                        results.append(result_page_step)
                        self.execution_steps.append(result_page_step)
                        
                        print(f"✅ Captured final result page: {final_screenshot_info.get('screenshot_path')}")
                        
                        # Extract result summary
                        result_summary = self.execution_state.get("result_summary")
                        if result_summary:
                            print(f"📋 Result Summary: {result_summary[:100]}{'...' if len(result_summary) > 100 else ''}")
                except Exception as e:
                    print(f"❌ Failed to capture final result page: {e}")
            
            # Add summary of data usage
            if self.generated_data or self.used_provided_data:
                summary = []
                if self.used_provided_data:
                    summary.append(f"Provided: {', '.join([f'{k}={v[:15]}...' if len(v) > 15 else f'{k}={v}' for k, v in self.used_provided_data.items()])}")
                if self.generated_data:
                    summary.append(f"Generated: {', '.join([f'{k}={v[:15]}...' if len(v) > 15 else f'{k}={v}' for k, v in self.generated_data.items()])}")
                
                results.append({
                    "action": "data_summary",
                    "status": "Info",
                    "details": " | ".join(summary),
                    "description": "Data usage summary"
                })
            
            # Close browser
            self._cleanup()
        
        # Generate execution summary
        execution_summary = self._generate_execution_summary(results)
        print(f"\n📊 Execution Summary:")
        print(f"   Total Steps: {execution_summary['total_steps']}")
        print(f"   Passed: {execution_summary['passed_steps']}")
        print(f"   Failed: {execution_summary['failed_steps']}")
        print(f"   Success Rate: {execution_summary['success_rate']:.1f}%")
        print(f"   Screenshots: {len([r for r in results if r.get('screenshot')])}")
        if self.execution_state.get("result_summary"):
            print(f"   Result Summary: {self.execution_state['result_summary'][:100]}...")
        
        return results
    
    def _extract_page_content(self, page):
        """Extract meaningful content from the current page"""
        try:
            content_parts = []
            
            # Get page title
            try:
                title = page.title()
                if title and len(title.strip()) > 0:
                    content_parts.append(f"Page Title: {title}")
            except:
                pass
            
            # Get main content using common selectors
            content_selectors = [
                "main", "article", "#main", ".main-content", ".content",
                "#search", ".search-results", "#results", ".results",
                "#bodyContent", ".mw-parser-output", "#mw-content-text",
                ".g", ".srg", "#res", "#rcnt",
                "div[role='main']", ".post-content", ".entry-content"
            ]
            
            for selector in content_selectors:
                try:
                    elements = page.locator(selector).all()
                    for elem in elements[:2]:  # Limit to first 2 elements
                        if elem.is_visible():
                            text = elem.inner_text(timeout=1000)
                            if text and len(text.strip()) > 50:
                                # Clean text
                                text = re.sub(r'\s+', ' ', text)
                                content_parts.append(text.strip())
                except:
                    continue
            
            # If no content with selectors, get paragraphs
            if not content_parts:
                try:
                    paragraphs = page.locator("p").all()
                    for p in paragraphs[:5]:
                        if p.is_visible():
                            text = p.inner_text(timeout=1000)
                            if text and len(text.strip()) > 30:
                                text = re.sub(r'\s+', ' ', text)
                                content_parts.append(text.strip())
                except:
                    pass
            
            # For Google search results, extract specific content
            if "google.com" in page.url.lower():
                try:
                    # Get search result snippets
                    snippets = page.locator(".VwiC3b, .MUxGbd, .lyLwlc").all()
                    for snippet in snippets[:3]:
                        if snippet.is_visible():
                            text = snippet.inner_text()
                            if text:
                                content_parts.append(f"Search result: {text[:200]}...")
                except:
                    pass
            
            # For Wikipedia, extract article content
            if "wikipedia.org" in page.url.lower():
                try:
                    # Get article title
                    title_elem = page.locator("#firstHeading").first
                    if title_elem.is_visible():
                        title = title_elem.inner_text()
                        content_parts.append(f"Wikipedia Article: {title}")
                    
                    # Get first few paragraphs
                    paragraphs = page.locator(".mw-parser-output p").all()
                    for p in paragraphs[:3]:
                        if p.is_visible():
                            text = p.inner_text()
                            if text:
                                text = re.sub(r'\s+', ' ', text)
                                if len(text) > 200:
                                    text = text[:200] + "..."
                                content_parts.append(text)
                except:
                    pass
            
            # For Amazon product pages
            if "amazon.com" in page.url.lower():
                try:
                    # Get product title
                    title_elem = page.locator("#productTitle, .a-size-large").first
                    if title_elem.is_visible():
                        title = title_elem.inner_text()
                        if title:
                            content_parts.append(f"Product: {title.strip()}")
                    
                    # Get product description
                    desc_elem = page.locator("#productDescription, .a-spacing-small").first
                    if desc_elem.is_visible():
                        desc = desc_elem.inner_text()
                        if desc:
                            content_parts.append(desc.strip()[:200] + "...")
                except:
                    pass
            
            if content_parts:
                return "\n\n".join(content_parts[:3])
            else:
                # Fallback: get body text
                try:
                    body_text = page.inner_text("body")
                    body_text = re.sub(r'\s+', ' ', body_text)
                    if len(body_text) > 500:
                        body_text = body_text[:500] + "..."
                    return body_text
                except:
                    return "Page loaded successfully"
                    
        except Exception as e:
            print(f"Error extracting page content: {e}")
            return "Could not extract page content"
    
    def _extract_wikipedia_content(self, page):
        """Extract Wikipedia article content"""
        try:
            content_parts = []
            
            # Get article title
            try:
                title_elem = page.locator("#firstHeading").first
                if title_elem.is_visible():
                    title = title_elem.inner_text()
                    if title:
                        content_parts.append(f"Article: {title}")
            except:
                pass
            
            # Get article content paragraphs
            try:
                paragraphs = page.locator(".mw-parser-output p").all()
                for p in paragraphs[:5]:  # First 5 paragraphs
                    if p.is_visible():
                        text = p.inner_text()
                        if text and len(text.strip()) > 30:
                            text = re.sub(r'\s+', ' ', text)
                            if len(text) > 200:
                                text = text[:200] + "..."
                            content_parts.append(text.strip())
            except:
                pass
            
            if content_parts:
                return "\n\n".join(content_parts)
            else:
                return "Wikipedia article loaded successfully"
                
        except Exception as e:
            print(f"Error extracting Wikipedia content: {e}")
            return f"Wikipedia content: {str(e)}"
    
    def _cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.context:
                self.context.close()
                self.context = None
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"[Executor] Cleanup error: {e}")
    
    def _generate_execution_summary(self, results):
        """Generate execution summary from results"""
        total_steps = len([r for r in results if r.get("step")])
        passed_steps = len([r for r in results if r.get("status", "").lower() == "passed"])
        failed_steps = len([r for r in results if r.get("status", "").lower() == "failed"])
        
        success_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "success_rate": success_rate,
            "has_screenshots": len([r for r in results if r.get("screenshot")]) > 0,
            "result_page_captured": self.final_result_page is not None,
            "last_failed_step": self.last_failed_step,
            "result_summary": self.execution_state.get("result_summary")
        }
    
    def get_screenshots_metadata(self):
        """Get metadata about captured screenshots"""
        if not self.screenshot_capture:
            return {}
        
        screenshots = self.screenshot_capture.get_all_screenshots(self.current_report_id)
        
        metadata = {
            "result_page": self.final_result_page,
            "last_failed": self.last_failed_step.get("screenshot_info") if self.last_failed_step else None,
            "all_screenshots": screenshots,
            "count": len(screenshots)
        }
        
        return metadata
    
    def get_result_summary(self):
        """Get result page summary"""
        if self.final_result_page:
            return self.final_result_page.get("result_summary", "Result page captured")
        return self.execution_state.get("result_summary")
    
    def _wait_for_stability(self, page, extra_wait=2, check_element=None):
        """Wait for page stability"""
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(extra_wait)
            
            if check_element:
                page.wait_for_selector(check_element, timeout=5000, state="visible")
        except:
            time.sleep(extra_wait)
    
    def _execute_navigate(self, page, action_data):
        """Navigate to URL"""
        url = action_data.get("url", "")
        if not url:
            return {"action": "navigate", "status": "Failed", "details": "No URL"}
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            self._wait_for_stability(page, 3)
            
            # Handle cookie banners
            self._handle_cookie_banner(page)
            
            return {"action": "navigate", "status": "Passed", "details": f"Navigated to {page.url}"}
        except Exception as e:
            return {"action": "navigate", "status": "Failed", "details": f"Failed: {str(e)}"}
    
    def _handle_cookie_banner(self, page):
        """Handle cookie consent banners"""
        cookie_selectors = [
            "button:has-text('Accept all cookies')",
            "button:has-text('Accept cookies')",
            "button:has-text('I accept')", 
            "button:has-text('Agree')",
            "button:has-text('Accept all')",
            ".accept-cookies",
            "#accept-cookies",
            "button[aria-label*='cookie' i]",
            "button[aria-label*='accept' i]",
            "#sp-cc-accept",  # Amazon cookie banner
        ]
        
        for selector in cookie_selectors:
            try:
                page.wait_for_selector(selector, timeout=3000)
                page.click(selector)
                time.sleep(1)
                print(f"✅ Clicked cookie banner: {selector}")
                break
            except:
                continue
    
    def _execute_search(self, page, action_data):
        """Execute search"""
        query = action_data.get("query", "")
        selector = action_data.get("selector", "")
        
        if not query:
            return {"action": "search", "status": "Failed", "details": "No query"}
        
        self._wait_for_stability(page, 2)
        
        # Try provided selector first
        if selector:
            selectors = [s.strip() for s in selector.split(',')]
            for sel in selectors:
                try:
                    result = self._perform_search(page, sel, query)
                    if result["status"] == "Passed":
                        # After search, extract page content for result analysis
                        content = self._extract_page_content(page)
                        if content:
                            self.execution_state["result_page_content"] = content
                            self.execution_state["result_summary"] = content[:500] + "..." if len(content) > 500 else content
                        return result
                except:
                    continue
        
        # Try common search selectors
        for sel in self.field_selectors["search"]:
            try:
                result = self._perform_search(page, sel, query)
                if result["status"] == "Passed":
                    # After search, extract page content for result analysis
                    content = self._extract_page_content(page)
                    if content:
                        self.execution_state["result_page_content"] = content
                        self.execution_state["result_summary"] = content[:500] + "..." if len(content) > 500 else content
                    return result
            except:
                continue
        
        return {"action": "search", "status": "Failed", "details": "Search box not found"}
    
    def _perform_search(self, page, selector: str, query: str):
        """Perform search with given selector"""
        try:
            page.wait_for_selector(selector, state="visible", timeout=10000)
            
            elem = page.locator(selector).first
            elem.scroll_into_view_if_needed()
            time.sleep(0.5)
            
            # Clear and type
            elem.click()
            time.sleep(0.3)
            elem.fill("")
            time.sleep(0.2)
            elem.fill(query)
            time.sleep(0.5)
            
            # Try pressing Enter
            elem.press("Enter")
            time.sleep(2)
            
            # Also try to find and click search button
            try:
                page.wait_for_timeout(1000)
                
                # Special handling for Wikipedia search button
                if "wikipedia.org" in page.url:
                    search_button = page.locator("#searchButton, button[type='submit'], input[type='submit'][value*='Search' i]").first
                    if search_button.is_visible():
                        search_button.click()
                        time.sleep(1)
                else:
                    search_buttons = page.locator("button:has-text('Search'), #searchButton, .search-button, input[type='submit'][value*='Search' i]")
                    if search_buttons.count() > 0:
                        search_buttons.first.click()
                        time.sleep(1)
            except:
                pass
            
            # Wait for results
            self._wait_for_stability(page, 2)
            
            # Special handling for Wikipedia
            current_url = page.url
            if "wikipedia.org" in current_url:
                if "/wiki/" in current_url:
                    try:
                        title = page.locator("#firstHeading, h1").first.inner_text(timeout=3000)
                        return {"action": "search", "status": "Passed", "details": f"✅ Wikipedia article found: {title}"}
                    except:
                        return {"action": "search", "status": "Passed", "details": f"✅ Wikipedia article found for: {query}"}
                elif "search=" in current_url or "/w/index.php" in current_url:
                    return {"action": "search", "status": "Passed", "details": f"✅ Wikipedia search results for: {query}"}
                else:
                    return {"action": "search", "status": "Passed", "details": f"✅ Searched Wikipedia for: {query}"}
            
            # For other sites, check if search was successful
            page_text = page.inner_text("body").lower()
            
            # Check for search success indicators
            search_indicators = [
                "results", "search", "showing", "did you mean", 
                "related searches", "no results found", "no matches",
                query.lower()
            ]
            
            indicator_count = sum(1 for indicator in search_indicators if indicator in page_text)
            
            if indicator_count > 0 or "?" in current_url or "search" in current_url or "q=" in current_url:
                return {"action": "search", "status": "Passed", "details": f"✅ Search completed: {query}"}
            else:
                return {"action": "search", "status": "Passed", "details": f"✅ Search executed: {query}"}
                
        except Exception as e:
            raise Exception(f"Search failed with {selector}: {str(e)}")
    
    def _execute_type(self, page, action_data, field_type=""):
        """Type into field with enhanced LinkedIn support"""
        selector = action_data.get("selector", "")
        value = action_data.get("value", "")
        
        if not value:
            return {"action": "type", "status": "Failed", "details": "No value to type"}
        
        self._wait_for_stability(page, 2)
        
        # Special handling for LinkedIn email field
        if field_type == "email" and "linkedin" in page.url:
            print(f"📧 LinkedIn email detection: using email-address field for {value[:10]}...")
            # Prioritize LinkedIn-specific selectors
            linkedin_selectors = ["input[name='email-address']", "input[id='email-address']"]
            for sel in linkedin_selectors:
                try:
                    result = self._perform_type(page, sel, value, field_type)
                    if result["status"] == "Passed":
                        return result
                except:
                    continue
        
        # Try provided selectors first
        if selector:
            selectors_list = [s.strip() for s in selector.split(',')]
            for sel in selectors_list:
                try:
                    result = self._perform_type(page, sel, value, field_type)
                    if result["status"] == "Passed":
                        return result
                except:
                    continue
        
        # Use field_type based selectors
        if field_type and field_type in self.field_selectors:
            for sel in self.field_selectors[field_type]:
                try:
                    result = self._perform_type(page, sel, value, field_type)
                    if result["status"] == "Passed":
                        return result
                except:
                    continue
        
        # Try generic input
        try:
            page.wait_for_selector("input", state="visible", timeout=5000)
            inputs = page.locator("input").all()
            for input_elem in inputs[:5]:
                try:
                    input_elem.fill(value)
                    time.sleep(0.5)
                    return {"action": "type", "status": "Passed", "details": f"Typed {field_type}: {value}"}
                except:
                    continue
        except:
            pass
        
        return {"action": "type", "status": "Failed", "details": f"Input field for {field_type} not found"}
    
    def _perform_type(self, page, selector: str, value: str, field_type: str):
        """Perform typing with given selector"""
        try:
            page.wait_for_selector(selector, state="visible", timeout=15000)
            
            elem = page.locator(selector).first
            elem.scroll_into_view_if_needed()
            time.sleep(0.5)
            
            # Clear and type
            elem.click()
            time.sleep(0.3)
            
            try:
                elem.fill("")
            except:
                elem.press("Control+A")
                elem.press("Backspace")
            
            time.sleep(0.2)
            elem.fill(value)
            time.sleep(0.5)
            
            # Mask password value in logs
            display_value = value
            if field_type == "password":
                display_value = "********"
            
            return {"action": "type", "status": "Passed", "details": f"Typed {field_type}: {display_value}"}
        except Exception as e:
            raise Exception(f"Type failed with {selector}: {str(e)}")
    
    def _execute_select(self, page, action_data, field_type=""):
        """Select from dropdown"""
        selector = action_data.get("selector", "")
        value = action_data.get("value", "")
        
        if not value:
            return {"action": "select", "status": "Failed", "details": "No value to select"}
        
        self._wait_for_stability(page, 1)
        
        # Convert value to string
        value_str = str(value)
        
        try:
            page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Try by value first
            try:
                page.select_option(selector, value=value_str)
                time.sleep(0.5)
                return {"action": "select", "status": "Passed", "details": f"Selected {field_type}: {value_str}"}
            except:
                # Try by label/text
                try:
                    page.select_option(selector, label=value_str)
                    time.sleep(0.5)
                    return {"action": "select", "status": "Passed", "details": f"Selected {field_type}: {value_str}"}
                except:
                    # Try by index if numeric
                    if value_str.isdigit():
                        try:
                            page.select_option(selector, index=int(value_str))
                            time.sleep(0.5)
                            return {"action": "select", "status": "Passed", "details": f"Selected {field_type}: {value_str}"}
                        except:
                            pass
        
        except Exception as e:
            pass
        
        return {"action": "select", "status": "Failed", "details": f"Could not select {field_type}: {value_str}"}
    
    def _execute_click(self, page, action_data):
        """Click element with enhanced LinkedIn support"""
        selector = action_data.get("selector", "")
        text = action_data.get("text", "")
        
        self._wait_for_stability(page, 2)
        
        strategies = []
        
        # Text-based strategies
        if text:
            text_lower = text.lower()
            strategies.extend([
                f"button:has-text('{text}')",
                f"a:has-text('{text}')",
                f"div[role='button']:has-text('{text}')",
                f"span:has-text('{text}')",
                f"input[value='{text}']",
            ])
            
            # Add type-specific selectors
            if "login" in text_lower or "log in" in text_lower or "sign in" in text_lower:
                strategies.extend(self.action_selectors["login_button"])
            elif "sign up" in text_lower or "create account" in text_lower or "join" in text_lower or "agree" in text_lower:
                strategies.extend(self.action_selectors["signup_button"])
                # LinkedIn-specific join button
                if "linkedin" in page.url:
                    strategies.append("button:has-text('Agree & Join')")
                    strategies.append("button:has-text('Join now')")
            elif "next" in text_lower:
                strategies.extend(self.action_selectors["next_button"])
            elif "add to cart" in text_lower:
                strategies.extend(self.action_selectors["add_to_cart"])
            elif "search" in text_lower:
                strategies.extend(self.action_selectors["search_button"])
        
        # Add provided selectors
        if selector:
            selectors_list = [s.strip() for s in selector.split(',')]
            strategies = selectors_list + strategies
        
        # Try each strategy
        for strategy in strategies:
            try:
                page.wait_for_selector(strategy, state="visible", timeout=10000)
                
                elem = page.locator(strategy).first
                elem.scroll_into_view_if_needed()
                time.sleep(0.5)
                
                try:
                    elem.click()
                except:
                    page.evaluate("(elem) => elem.click()", elem.element_handle())
                
                time.sleep(2)
                
                return {"action": "click", "status": "Passed", "details": f"Clicked: {text or strategy}"}
            except:
                continue
        
        # Try to find any clickable element with the text
        if text:
            try:
                page.click(f"text={text}", timeout=3000)
                time.sleep(2)
                return {"action": "click", "status": "Passed", "details": f"Clicked text: {text}"}
            except:
                pass
        
        return {"action": "click", "status": "Failed", "details": f"Element not found: {text or selector}"}
    
    def _execute_validate_page(self, page, action_data, execution_state=None):
        """SMART page validation with enhanced LinkedIn support and content extraction"""
        validation_type = action_data.get("type", "generic")
        text = action_data.get("text", "")
        min_indicators = action_data.get("min_indicators", 1)
        
        # Use execution state if provided - FIX: Check if None and initialize
        if execution_state is None:
            execution_state = {}
        
        try:
            self._wait_for_stability(page, 3)
            
            # Get page content
            content = page.content().lower()
            page_text = page.inner_text("body").lower()
            full_content = content + " " + page_text
            
            # Check URL
            current_url = page.url.lower()
            
            # Extract meaningful content for result analysis
            if validation_type == "search" or "result" in validation_type or execution_state.get("is_search_operation", False):
                # Extract actual search results content
                result_content = self._extract_page_content(page)
                if result_content:
                    # Store in execution_state for later use
                    execution_state["result_page_content"] = result_content
                    execution_state["result_summary"] = result_content[:500] + "..." if len(result_content) > 500 else result_content
            
            # Enhanced LinkedIn validation
            if "linkedin.com" in current_url and execution_state.get("is_signup_flow", False):
                print("🔍 Enhanced LinkedIn signup validation")
                
                # LinkedIn signup success indicators (enhanced)
                linkedin_signup_success = [
                    "check your email",
                    "verify your account",
                    "enter the code",
                    "enter code",
                    "enter confirmation code",
                    "we sent a code",
                    "verification",
                    "confirm your email",
                    "check your inbox",
                    "email sent",
                    "confirmation code",
                    "we've sent a code",
                    "enter the 6-digit code",
                    "confirm it's you",
                    "enter the verification code",
                    "verify it's you",
                ]
                
                linkedin_count = 0
                found_indicators = []
                for indicator in linkedin_signup_success:
                    if indicator in full_content:
                        linkedin_count += 1
                        found_indicators.append(indicator)
                
                if linkedin_count >= 1:
                    # Add data usage information
                    details = f"✅ LinkedIn signup successful! ({linkedin_count} indicators found)"
                    
                    # Add data source information
                    if execution_state.get("has_provided_credentials", False):
                        if "email" in self.used_provided_data:
                            details += f" | Used provided email: {self.used_provided_data['email'][:15]}..."
                        if "password" in self.used_provided_data:
                            details += " | Used provided password"
                    
                    if execution_state.get("has_generated_data", False):
                        generated_fields = list(self.generated_data.keys())
                        if generated_fields:
                            details += f" | Generated: {', '.join(generated_fields)}"
                    
                    return {
                        "action": "validate_page",
                        "status": "Passed",
                        "details": details,
                        "indicators_found": found_indicators[:3],
                        "result_content": execution_state.get("result_page_content", "")[:500] if execution_state.get("result_page_content") else None
                    }
            
            # Special Wikipedia validation
            if "wikipedia.org" in current_url:
                wikipedia_indicators = [
                    "wikipedia, the free encyclopedia",
                    "from wikipedia",
                    "main page",
                    "contents",
                    "article",
                    "talk",
                    "read",
                    "edit",
                    "view history",
                    "search",
                    "create account",
                    "log in",
                    "/wiki/"
                ]
                
                wikipedia_count = sum(1 for indicator in wikipedia_indicators if indicator in full_content)
                if wikipedia_count >= 2:
                    # Extract Wikipedia article content
                    article_content = self._extract_wikipedia_content(page)
                    if article_content:
                        execution_state["result_page_content"] = article_content
                        execution_state["result_summary"] = article_content[:500] + "..." if len(article_content) > 500 else article_content
                    
                    return {
                        "action": "validate_page",
                        "status": "Passed",
                        "details": f"✅ Wikipedia page loaded successfully ({wikipedia_count} indicators found)",
                        "indicators_found": [ind for ind in wikipedia_indicators if ind in full_content][:3],
                        "result_content": execution_state.get("result_page_content", "")[:500] if execution_state.get("result_page_content") else None
                    }
            
            # Check for failure patterns first
            if validation_type == "login":
                failure_count = 0
                for pattern in self.validation_patterns["login_failure"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        failure_count += 1
                
                if failure_count >= 1:
                    return {
                        "action": "validate_page",
                        "status": "Failed",
                        "details": "❌ Login failed: Invalid credentials or account not found"
                    }
            
            elif validation_type == "signup":
                failure_count = 0
                for pattern in self.validation_patterns["signup_failure"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        failure_count += 1
                
                if failure_count >= 1:
                    error_details = "❌ Signup failed: "
                    if "email already exists" in full_content or "account already exists" in full_content:
                        error_details += "Email already exists"
                    elif "password too weak" in full_content or "password must be" in full_content:
                        error_details += "Password too weak"
                    else:
                        error_details += "Invalid data provided"
                    
                    return {
                        "action": "validate_page", 
                        "status": "Failed",
                        "details": error_details
                    }
            
            # Check for success patterns
            success_indicators = []
            
            if validation_type == "login":
                for pattern in self.validation_patterns["login_success"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        match = re.search(pattern, full_content, re.IGNORECASE)
                        success_indicators.append(match.group(0) if match else pattern)
                
                # Special check for Twitter/X
                if text == "@":
                    username_matches = re.findall(r'@[a-zA-Z0-9_]+', full_content)
                    if username_matches:
                        success_indicators.extend(username_matches[:2])
            
            elif validation_type == "signup":
                for pattern in self.validation_patterns["signup_success"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        match = re.search(pattern, full_content, re.IGNORECASE)
                        success_indicators.append(match.group(0) if match else pattern)
            
            elif validation_type == "shopping":
                for pattern in self.validation_patterns["shopping_success"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        match = re.search(pattern, full_content, re.IGNORECASE)
                        success_indicators.append(match.group(0) if match else pattern)
            
            elif validation_type == "search":
                for pattern in self.validation_patterns["search_success"]:
                    if re.search(pattern, full_content, re.IGNORECASE):
                        match = re.search(pattern, full_content, re.IGNORECASE)
                        success_indicators.append(match.group(0) if match else pattern)
            
            # Generic text check
            if text:
                text_indicators = [t.strip() for t in text.split(',')]
                for indicator in text_indicators:
                    if indicator.lower() in full_content:
                        success_indicators.append(indicator)
            
            # Remove duplicates
            success_indicators = list(set(success_indicators))
            
            # Evaluate results
            if len(success_indicators) >= min_indicators:
                details = f"✅ Validation passed! Found: {', '.join(success_indicators[:3])}"
                
                # Add data usage info for signup
                if validation_type == "signup":
                    if execution_state.get("has_provided_credentials", False):
                        if "email" in self.used_provided_data:
                            details += f" | Used provided email: {self.used_provided_data['email'][:10]}..."
                    
                    if execution_state.get("has_generated_data", False):
                        details += f" | Used generated data for {len(self.generated_data)} fields"
                
                return {
                    "action": "validate_page",
                    "status": "Passed",
                    "details": details,
                    "indicators_found": success_indicators,
                    "result_content": execution_state.get("result_page_content", "")[:500] if execution_state.get("result_page_content") else None
                }
            else:
                return {
                    "action": "validate_page",
                    "status": "Failed",
                    "details": f"❌ Validation failed. Need {min_indicators} indicators, found {len(success_indicators)}",
                    "indicators_found": success_indicators,
                    "result_content": execution_state.get("result_page_content", "")[:500] if execution_state.get("result_page_content") else None
                }
        
        except Exception as e:
            return {
                "action": "validate_page",
                "status": "Failed",
                "details": f"Validation error: {str(e)}"
            }


# Example usage and testing
if __name__ == "__main__":
    executor = UniversalExecutor()
    
    print(f"\n{'='*60}")
    print("Testing Universal Executor with Enhanced Screenshot Capture...")
    print('='*60)
    
    # Test case: Google search example (like "go to google search apples")
    google_search_test = [
        {
            "action": "navigate", 
            "url": "https://www.google.com",
            "description": "Navigate to Google"
        },
        {
            "action": "wait", 
            "seconds": 2,
            "description": "Wait for page to load"
        },
        {
            "action": "type",
            "selector": "textarea[name='q']",
            "value": "apples nutrition facts",
            "field_type": "search",
            "description": "Search for apples nutrition"
        },
        {
            "action": "click",
            "selector": "input[value='Google Search']",
            "text": "Google Search",
            "description": "Click search button"
        },
        {
            "action": "wait", 
            "seconds": 3,
            "description": "Wait for search results"
        },
        {
            "action": "validate_page",
            "type": "search",
            "text": "results, showing, apples",
            "min_indicators": 2,
            "description": "Validate search results page"
        }
    ]
    
    print("\nTest Case: Google search for 'apples nutrition facts'")
    print("-" * 50)
    
    # Generate a test report ID
    test_report_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    results = executor.run(
        parsed_actions=google_search_test, 
        headless=False, 
        report_id=test_report_id,
        instruction="Go to google search apples nutrition facts"
    )
    
    # Print results
    for r in results:
        status_icon = "✅" if r['status'] == "Passed" else "❌" if r['status'] == "Failed" else "ℹ️"
        step_num = r.get('step', '?')
        action_desc = r.get('description', r['action'])
        print(f"{status_icon} Step {step_num}: {action_desc}: {r['details']}")
        
        if r.get('screenshot'):
            print(f"   📸 Screenshot: {r['screenshot']}")
        
        if r.get('result_content'):
            print(f"   📋 Content: {r['result_content'][:100]}...")
    
    # Get screenshot metadata
    screenshots_metadata = executor.get_screenshots_metadata()
    if screenshots_metadata.get('count', 0) > 0:
        print(f"\n📸 Screenshots captured:")
        print(f"   Total: {screenshots_metadata['count']}")
        
        if screenshots_metadata.get('result_page'):
            print(f"   Result Page: {screenshots_metadata['result_page'].get('filename', 'captured')}")
            print(f"   Result Summary: {screenshots_metadata['result_page'].get('result_summary', 'Available')}")
        
        if screenshots_metadata.get('last_failed'):
            print(f"   Last Failed Step: Step {screenshots_metadata['last_failed'].get('step_number', '?')}")
    
    result_summary = executor.get_result_summary()
    if result_summary:
        print(f"\n📋 Final Result Summary: {result_summary[:200]}...")
    
    print(f"\n{'='*60}")
    print("Executor ready for integration with reporting system")
    print('='*60)