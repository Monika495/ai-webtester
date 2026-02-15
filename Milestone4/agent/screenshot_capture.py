"""
Screenshot Capture Module for NovaQA
Captures screenshots with analysis and content extraction for result pages
Uses Gemini AI for intelligent content summarization
"""

import os
import time
from datetime import datetime
import re
from PIL import Image
import io
import base64
import traceback
import json

# Try to import Gemini
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[ScreenshotCapture] Gemini not available, using basic extraction")


class ScreenshotCapture:
    """
    Handles screenshot capture with page analysis and content extraction
    Uses Gemini AI for intelligent summarization when available
    """
    
    def __init__(self, reports_dir="reports", api_key=None):
        self.reports_dir = reports_dir
        self.screenshots_dir = os.path.join(reports_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Initialize Gemini if available
        self.gemini_client = None
        self.gemini_available = False
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if self.api_key and GEMINI_AVAILABLE:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
                # Test connection
                response = self.gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents="Say OK"
                )
                if response.text and "OK" in response.text.upper():
                    self.gemini_available = True
                    print("[ScreenshotCapture] ✅ Gemini AI initialized for intelligent summarization")
            except Exception as e:
                print(f"[ScreenshotCapture] ⚠️ Gemini init failed: {e}")
                self.gemini_available = False
        else:
            print("[ScreenshotCapture] Using basic content extraction (Gemini not available)")
        
        print(f"[ScreenshotCapture] Directory: {self.screenshots_dir}")
    
    def _summarize_with_gemini(self, content, title, url):
        """Use Gemini to generate an intelligent summary of the content"""
        if not self.gemini_available or not content:
            return None
        
        try:
            # Truncate content if too long (Gemini has limits)
            if len(content) > 5000:
                content = content[:5000] + "..."
            
            prompt = f"""You are a content summarizer for a test automation report. 
            
I have extracted the following content from a webpage:
URL: {url}
Title: {title}

Content:
{content}

Please provide a concise, informative summary of what this page contains. 
Focus on the main topic and key information. Keep it to 3-5 sentences maximum.
The summary should be human-readable and capture the essence of the page.

Summary:"""

            response = self.gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            if response and response.text:
                summary = response.text.strip()
                print(f"[ScreenshotCapture] ✨ Gemini generated summary: {summary[:100]}...")
                return summary
            else:
                return None
                
        except Exception as e:
            print(f"[ScreenshotCapture] ⚠️ Gemini summarization failed: {e}")
            return None
    
    def capture(self, page, filename_prefix="screenshot"):
        """Capture a screenshot and return the filepath"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            page.screenshot(path=filepath, full_page=True)
            
            # Create thumbnail
            self._create_thumbnail(filepath)
            
            print(f"[ScreenshotCapture] Captured: {filename}")
            return filepath
            
        except Exception as e:
            print(f"[ScreenshotCapture] Failed to capture: {e}")
            return None
    
    def capture_with_analysis(self, page, report_id, description="", is_final_result=False):
        """
        Capture screenshot with page analysis and content extraction
        
        Args:
            page: Playwright page object
            report_id: Report ID for naming
            description: Description of the screenshot
            is_final_result: Whether this is the final result page
            
        Returns:
            Dictionary with screenshot info and analysis
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if is_final_result:
                screenshot_type = "result_page"
            else:
                screenshot_type = "screenshot"
            
            # Clean description for filename
            clean_desc = re.sub(r'[^\w\s-]', '', description)
            clean_desc = clean_desc.replace(' ', '_')[:30]
            
            filename = f"{screenshot_type}_{report_id}_{clean_desc}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            page.screenshot(path=filepath, full_page=True)
            
            # Create thumbnail
            thumb_filename = f"thumb_{filename}"
            thumb_path = os.path.join(self.screenshots_dir, thumb_filename)
            self._create_thumbnail(filepath, thumb_path)
            
            # Get page analysis with content extraction
            analysis = self._analyze_page(page, description, is_final_result)
            
            # Extract detailed content
            page_content = self._extract_detailed_content(page)
            
            # Generate intelligent summary using Gemini for final result
            result_summary = None
            if is_final_result and page_content:
                # Try Gemini first
                if self.gemini_available:
                    title = page.title() if page.title() else "Result page"
                    gemini_summary = self._summarize_with_gemini(page_content, title, page.url)
                    if gemini_summary:
                        result_summary = gemini_summary
                    else:
                        # Fallback to basic summary
                        result_summary = self._create_basic_summary(page_content)
                else:
                    # Use basic summary
                    result_summary = self._create_basic_summary(page_content)
                
                # Store full content separately
                analysis["full_content"] = page_content
            else:
                result_summary = analysis.get("summary", "Step captured")
            
            screenshot_info = {
                "filename": filename,
                "thumb_filename": thumb_filename,
                "screenshot_path": filepath,
                "thumb_path": thumb_path,
                "timestamp": timestamp,
                "description": description,
                "analysis": analysis,
                "result_summary": result_summary,
                "full_content": page_content if is_final_result else None,
                "is_final_result": is_final_result
            }
            
            print(f"📸 Screenshot captured: {filename}")
            if is_final_result and result_summary:
                print(f"📋 Result Summary: {result_summary[:150]}...")
            
            return screenshot_info
            
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            traceback.print_exc()
            return None
    
    def _create_basic_summary(self, content):
        """Create a basic summary when Gemini is not available"""
        if not content:
            return "Page loaded successfully"
        
        # Take first 2-3 sentences
        sentences = re.split(r'[.!?]+', content)
        summary_sentences = []
        char_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                summary_sentences.append(sentence)
                char_count += len(sentence)
                if char_count > 300 or len(summary_sentences) >= 3:
                    break
        
        if summary_sentences:
            return '. '.join(summary_sentences) + '.'
        else:
            return content[:300] + "..." if len(content) > 300 else content
    
    def _extract_detailed_content(self, page):
        """
        Extract detailed content from page for result summary
        Enhanced version with better content extraction for various sites
        """
        try:
            content_parts = []
            current_url = page.url.lower()
            
            # Get page title
            try:
                title = page.title()
                if title and len(title.strip()) > 0:
                    content_parts.append(f"Page Title: {title}")
            except:
                pass
            
            # Get meta description if available
            try:
                meta_desc = page.locator("meta[name='description']").first
                if meta_desc:
                    content = meta_desc.get_attribute("content")
                    if content:
                        content_parts.append(f"Description: {content[:200]}...")
            except:
                pass
            
            # Site-specific content extraction
            if "wikipedia.org" in current_url:
                # Wikipedia article - extract full article content
                try:
                    # Get article title
                    title_elem = page.locator("#firstHeading").first
                    if title_elem.is_visible():
                        title = title_elem.inner_text()
                        if title:
                            content_parts.append(f"Wikipedia Article: {title}")
                    
                    # Get article content paragraphs - get more paragraphs for better summary
                    paragraphs = page.locator(".mw-parser-output p").all()
                    article_paragraphs = []
                    for p in paragraphs[:10]:  # Get first 10 paragraphs
                        if p.is_visible():
                            text = p.inner_text()
                            if text and len(text.strip()) > 30 and not text.startswith("Jump to navigation"):
                                # Clean text
                                text = re.sub(r'\s+', ' ', text)
                                article_paragraphs.append(text.strip())
                    
                    if article_paragraphs:
                        content_parts.extend(article_paragraphs[:5])  # Add first 5 paragraphs
                    
                    # Get section headings for context
                    headings = page.locator(".mw-parser-output h2, .mw-parser-output h3").all()
                    section_names = []
                    for h in headings[:5]:
                        if h.is_visible():
                            text = h.inner_text()
                            if text and "See also" not in text and "References" not in text:
                                section_names.append(text.strip())
                    
                    if section_names:
                        content_parts.append(f"Sections include: {', '.join(section_names[:5])}")
                        
                except Exception as e:
                    print(f"Error extracting Wikipedia content: {e}")
            
            elif "google.com" in current_url:
                # Google search results
                try:
                    # Get search query
                    search_box = page.locator("textarea[name='q'], input[name='q']").first
                    if search_box:
                        query = search_box.get_attribute("value")
                        if query:
                            content_parts.append(f"Search Query: {query}")
                    
                    # Get result stats
                    stats = page.locator("#result-stats").first
                    if stats:
                        stats_text = stats.inner_text()
                        if stats_text:
                            content_parts.append(f"Search Statistics: {stats_text}")
                    
                    # Get search result snippets
                    snippets = page.locator(".VwiC3b, .MUxGbd, .lyLwlc, .g .VwiC3b").all()
                    for i, snippet in enumerate(snippets[:5]):
                        if snippet.is_visible():
                            text = snippet.inner_text()
                            if text and len(text.strip()) > 20:
                                content_parts.append(f"Result {i+1}: {text[:200]}...")
                except Exception as e:
                    print(f"Error extracting Google content: {e}")
            
            elif "amazon.com" in current_url or "amazon.in" in current_url:
                # Amazon product or search page
                try:
                    # Check if it's a product page
                    product_title = page.locator("#productTitle, .a-size-large").first
                    if product_title.is_visible():
                        title = product_title.inner_text()
                        if title:
                            content_parts.append(f"Product: {title[:200]}...")
                        
                        # Get price
                        price = page.locator(".a-price-whole, .a-price .a-offscreen").first
                        if price.is_visible():
                            price_text = price.inner_text()
                            if price_text:
                                content_parts.append(f"Price: {price_text}")
                        
                        # Get rating
                        rating = page.locator(".a-icon-alt, #acrPopover .a-size-base").first
                        if rating.is_visible():
                            rating_text = rating.inner_text()
                            if rating_text:
                                content_parts.append(f"Rating: {rating_text}")
                        
                        # Get product description
                        desc = page.locator("#productDescription, #feature-bullets").first
                        if desc.is_visible():
                            desc_text = desc.inner_text()
                            if desc_text:
                                content_parts.append(f"Description: {desc_text[:200]}...")
                    else:
                        # Search results page
                        search_box = page.locator("#twotabsearchtextbox").first
                        if search_box:
                            query = search_box.get_attribute("value")
                            if query:
                                content_parts.append(f"Search: {query}")
                        
                        # Get result count
                        result_count = page.locator(".a-section.a-spacing-small.a-spacing-top-small span").first
                        if result_count.is_visible():
                            count_text = result_count.inner_text()
                            if count_text:
                                content_parts.append(f"Results: {count_text}")
                        
                        # Get first few product titles
                        products = page.locator(".s-result-item h2 a span, .a-size-medium.a-color-base.a-text-normal").all()
                        for i, product in enumerate(products[:5]):
                            if product.is_visible():
                                text = product.inner_text()
                                if text:
                                    content_parts.append(f"Product {i+1}: {text[:150]}...")
                except Exception as e:
                    print(f"Error extracting Amazon content: {e}")
            
            # Generic content extraction for any site
            if len(content_parts) < 3:  # If we don't have enough content
                try:
                    # Get main content area
                    main_selectors = ["main", "article", "#main", ".main-content", ".content", "#content"]
                    for selector in main_selectors:
                        elem = page.locator(selector).first
                        if elem.is_visible():
                            text = elem.inner_text()
                            if text and len(text.strip()) > 50:
                                text = re.sub(r'\s+', ' ', text)
                                if len(text) > 500:
                                    text = text[:500] + "..."
                                content_parts.append(text)
                                break
                    
                    # Get paragraphs if still no content
                    if len(content_parts) < 2:
                        paragraphs = page.locator("p").all()
                        para_texts = []
                        for p in paragraphs[:8]:
                            if p.is_visible():
                                text = p.inner_text()
                                if text and len(text.strip()) > 20:
                                    text = re.sub(r'\s+', ' ', text)
                                    para_texts.append(text)
                        
                        if para_texts:
                            content_parts.append(" ".join(para_texts[:5]))
                except Exception as e:
                    print(f"Error in generic content extraction: {e}")
            
            # If we have content, return it
            if content_parts:
                return "\n\n".join(content_parts)
            else:
                # Last resort: get body text
                try:
                    body_text = page.inner_text("body")
                    body_text = re.sub(r'\s+', ' ', body_text)
                    if len(body_text) > 1000:
                        body_text = body_text[:1000] + "..."
                    return body_text
                except:
                    return "Page loaded successfully"
                    
        except Exception as e:
            print(f"Error in _extract_detailed_content: {e}")
            traceback.print_exc()
            return "Could not extract page content"
    
    def _create_thumbnail(self, image_path, thumb_path=None, size=(320, 240)):
        """Create a thumbnail of the screenshot"""
        try:
            if thumb_path is None:
                filename = os.path.basename(image_path)
                thumb_path = os.path.join(self.screenshots_dir, f"thumb_{filename}")
            
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumb_path, "PNG")
            
            return thumb_path
        except Exception as e:
            print(f"[ScreenshotCapture] Failed to create thumbnail: {e}")
            return None
    
    def _analyze_page(self, page, description="", is_final_result=False):
        """Analyze page content and return summary"""
        try:
            url = page.url
            title = page.title() or "No title"
            
            # Get page text for analysis
            page_text = page.inner_text("body")[:1000] if page.inner_text("body") else ""
            
            # Clean text
            page_text = re.sub(r'\s+', ' ', page_text)
            
            # Basic analysis
            analysis = {
                "url": url,
                "title": title,
                "description": description,
                "text_preview": page_text[:300] + "..." if len(page_text) > 300 else page_text,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add site-specific analysis
            if "wikipedia.org" in url.lower():
                analysis["site"] = "wikipedia"
                analysis["summary"] = f"Wikipedia article: {title}"
            elif "google.com" in url.lower():
                analysis["site"] = "google"
                analysis["summary"] = f"Google page: {title}"
            elif "amazon.com" in url.lower() or "amazon.in" in url.lower():
                analysis["site"] = "amazon"
                analysis["summary"] = f"Amazon page: {title}"
            elif "youtube.com" in url.lower():
                analysis["site"] = "youtube"
                analysis["summary"] = f"YouTube: {title}"
            elif "linkedin.com" in url.lower():
                analysis["site"] = "linkedin"
                analysis["summary"] = f"LinkedIn: {title}"
            elif "twitter.com" in url.lower() or "x.com" in url.lower():
                analysis["site"] = "twitter"
                analysis["summary"] = f"Twitter/X: {title}"
            else:
                analysis["site"] = "generic"
                analysis["summary"] = f"Page: {title}"
            
            return analysis
            
        except Exception as e:
            return {
                "url": page.url if page else "unknown",
                "title": "Unknown",
                "description": description,
                "summary": "Page loaded successfully",
                "error": str(e)
            }
    
    def get_all_screenshots(self, report_id):
        """Get all screenshots for a specific report"""
        screenshots = []
        
        if os.path.exists(self.screenshots_dir):
            for filename in os.listdir(self.screenshots_dir):
                if report_id in filename and filename.endswith('.png'):
                    if not filename.startswith('thumb_'):
                        screenshots.append({
                            "filename": filename,
                            "path": os.path.join(self.screenshots_dir, filename),
                            "thumbnail": f"thumb_{filename}" if os.path.exists(os.path.join(self.screenshots_dir, f"thumb_{filename}")) else filename
                        })
        
        return screenshots
    
    def get_screenshot_as_base64(self, filename):
        """Get screenshot as base64 string"""
        filepath = os.path.join(self.screenshots_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"[ScreenshotCapture] Failed to encode screenshot: {e}")
            return None
    
    def delete_screenshot(self, filename):
        """Delete a screenshot file"""
        filepath = os.path.join(self.screenshots_dir, filename)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                
                # Also delete thumbnail if exists
                thumb_path = os.path.join(self.screenshots_dir, f"thumb_{filename}")
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                
                return True
            except Exception as e:
                print(f"[ScreenshotCapture] Failed to delete {filename}: {e}")
                return False
        
        return False


# Example usage
if __name__ == "__main__":
    # Test the screenshot capture module
    sc = ScreenshotCapture()
    print(f"\n{'='*60}")
    print("ScreenshotCapture module initialized")
    print(f"Screenshots directory: {sc.screenshots_dir}")
    print(f"Gemini AI: {'✅ Available' if sc.gemini_available else '❌ Not Available'}")
    print('='*60)