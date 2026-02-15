"""
Result Page Summarizer for NovaQA
Generates human-readable summaries of final result pages
"""

import re
from typing import Dict, List, Optional
import json
from playwright.sync_api import Page


class ResultSummarizer:
    """
    Generates human-readable summaries from result pages
    """
    
    def __init__(self):
        self.site_patterns = {
            "google": {
                "title_selectors": ["#search h3", ".g h3", "h3.LC20lb"],
                "content_selectors": [".VwiC3b", ".MUxGbd", ".lyLwlc"],
                "summary_keywords": ["result", "search", "showing", "about", "information"]
            },
            "wikipedia": {
                "title_selectors": ["#firstHeading", "h1"],
                "content_selectors": ["#mw-content-text p", ".mw-parser-output p"],
                "summary_keywords": ["article", "about", "is a", "was a", "are", "were"]
            },
            "amazon": {
                "title_selectors": ["#productTitle", "h1"],
                "content_selectors": [".product-description", "#feature-bullets", "#productDescription"],
                "summary_keywords": ["product", "price", "features", "description", "buy"]
            },
            "linkedin": {
                "title_selectors": [".profile-topcard-person-entity__name", "h1"],
                "content_selectors": [".profile-topcard-person-entity__description", ".profile-section"],
                "summary_keywords": ["profile", "experience", "education", "skills"]
            },
            "twitter": {
                "title_selectors": ["h1[role='heading']", "[data-testid='UserName']"],
                "content_selectors": ["[data-testid='tweetText']", "[role='article']"],
                "summary_keywords": ["tweet", "post", "following", "followers", "retweet"]
            },
            "youtube": {
                "title_selectors": ["#title h1", ".title"],
                "content_selectors": ["#description", "#meta"],
                "summary_keywords": ["video", "views", "subscribers", "channel", "watch"]
            },
            "default": {
                "title_selectors": ["h1", "h2", ".title", ".heading"],
                "content_selectors": ["p", ".content", ".description", "article"],
                "summary_keywords": ["content", "page", "information", "details"]
            }
        }
    
    def extract_page_summary(self, page: Page, instruction: str = None) -> Dict[str, any]:
        """
        Extract a human-readable summary from the current page
        
        Args:
            page: Playwright page object
            instruction: Original user instruction for context
        
        Returns:
            Dictionary with summary information
        """
        try:
            # Get current URL to identify site
            current_url = page.url.lower()
            site = self._identify_site(current_url)
            
            # Get page content
            page_title = self._get_page_title(page, site)
            page_text = self._get_page_content(page, site)
            
            # Clean and process text
            cleaned_text = self._clean_text(page_text)
            
            # Generate summary based on site and instruction
            summary = self._generate_summary(cleaned_text, instruction, site, page_title)
            
            # Extract key information
            key_info = self._extract_key_information(cleaned_text, site)
            
            return {
                "site": site,
                "url": current_url,
                "page_title": page_title,
                "summary": summary,
                "key_information": key_info,
                "content_length": len(cleaned_text),
                "word_count": len(cleaned_text.split()),
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate summary: {str(e)}",
                "fallback_summary": f"The page at {page.url} was loaded successfully.",
                "timestamp": self._get_timestamp()
            }
    
    def _identify_site(self, url: str) -> str:
        """Identify which website this is based on URL"""
        for site in self.site_patterns.keys():
            if site in url and site != "default":
                return site
        return "default"
    
    def _get_page_title(self, page: Page, site: str) -> str:
        """Extract page title"""
        try:
            # Try to get from meta title first
            title = page.title() or ""
            if title and len(title) > 10:
                return title
            
            # Try site-specific selectors
            for selector in self.site_patterns[site]["title_selectors"]:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        element_title = element.inner_text(timeout=2000)
                        if element_title and len(element_title.strip()) > 5:
                            return element_title.strip()
                except:
                    continue
            
            # Fallback to first h1
            try:
                h1 = page.locator("h1").first
                if h1.is_visible():
                    h1_text = h1.inner_text(timeout=2000)
                    if h1_text:
                        return h1_text.strip()
            except:
                pass
            
            return "Page loaded successfully"
            
        except Exception:
            return "Page loaded successfully"
    
    def _get_page_content(self, page: Page, site: str) -> str:
        """Extract relevant page content"""
        try:
            all_text = []
            
            # Try site-specific content selectors
            for selector in self.site_patterns[site]["content_selectors"]:
                try:
                    elements = page.locator(selector).all()
                    for elem in elements[:10]:  # Limit to first 10 elements
                        if elem.is_visible():
                            text = elem.inner_text(timeout=1000)
                            if text and len(text.strip()) > 20:
                                all_text.append(text.strip())
                except:
                    continue
            
            # If no specific content found, get main content area
            if not all_text:
                try:
                    # Try common content areas
                    content_selectors = [
                        "main", "article", ".content", "#content", ".main-content",
                        "[role='main']", ".post-content", ".entry-content"
                    ]
                    
                    for selector in content_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                text = element.inner_text(timeout=2000)
                                if text and len(text) > 50:
                                    all_text.append(text)
                                    break
                        except:
                            continue
                    
                    # Fallback to body text
                    if not all_text:
                        body = page.locator("body").first
                        text = body.inner_text(timeout=2000)
                        if text and len(text) > 100:
                            # Get first 2000 characters
                            all_text.append(text[:2000])
                except:
                    pass
            
            return " ".join(all_text)
            
        except Exception as e:
            return f"Content extraction failed: {str(e)}"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise
        noise_patterns = [
            r'javascript:.*?;',
            r'<!--.*?-->',
            r'\[.*?\]',
            r'\(.*?\)',
            r'\b\d+\b',
            r'[^\w\s.,!?-]'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, ' ', text)
        
        # Remove short lines and duplicate sentences
        lines = [line.strip() for line in text.split('.') if len(line.strip()) > 20]
        unique_lines = []
        seen = set()
        
        for line in lines:
            if line.lower() not in seen:
                seen.add(line.lower())
                unique_lines.append(line)
        
        return '. '.join(unique_lines[:10])  # Limit to 10 sentences
    
    def _generate_summary(self, text: str, instruction: str, site: str, title: str) -> str:
        """Generate human-readable summary"""
        if not text or len(text) < 50:
            return f"The {site} page '{title}' was loaded successfully."
        
        # Extract first few meaningful sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Filter for relevant sentences based on instruction
        relevant_sentences = []
        if instruction:
            instruction_keywords = instruction.lower().split()
            for sentence in sentences[:5]:
                sentence_lower = sentence.lower()
                # Check if sentence contains instruction keywords
                if any(keyword in sentence_lower for keyword in instruction_keywords if len(keyword) > 3):
                    relevant_sentences.append(sentence)
        
        # If no relevant sentences found, use first few sentences
        if not relevant_sentences:
            relevant_sentences = sentences[:3]
        
        # Generate summary
        summary_parts = []
        
        if title and len(title) > 5:
            summary_parts.append(f"The page '{title}' was accessed.")
        
        if relevant_sentences:
            if len(relevant_sentences) == 1:
                summary_parts.append(f"It contains information about: {relevant_sentences[0]}")
            else:
                summary_text = ' '.join(relevant_sentences[:2])
                summary_parts.append(f"It shows information including: {summary_text}")
        
        # Add site-specific context
        site_context = {
            "google": "search results",
            "wikipedia": "encyclopedia article",
            "amazon": "product page",
            "linkedin": "profile page",
            "twitter": "social media page",
            "youtube": "video page"
        }
        
        site_desc = site_context.get(site, "web page")
        if summary_parts:
            summary = f"The {site_desc} was loaded successfully. {' '.join(summary_parts)}"
        else:
            summary = f"The {site_desc} was loaded successfully with relevant content."
        
        # Truncate if too long
        if len(summary) > 300:
            summary = summary[:297] + "..."
        
        return summary
    
    def _extract_key_information(self, text: str, site: str) -> List[str]:
        """Extract key pieces of information"""
        if not text:
            return []
        
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Extract key sentences (avoid very short or very long)
        key_sentences = []
        for sentence in sentences[:8]:
            words = sentence.split()
            if 5 <= len(words) <= 30:
                # Check for keywords based on site
                keywords = self.site_patterns[site]["summary_keywords"]
                sentence_lower = sentence.lower()
                
                # Score sentence based on keyword matches
                score = sum(1 for keyword in keywords if keyword in sentence_lower)
                
                if score > 0 or site == "default":
                    key_sentences.append(sentence)
        
        return key_sentences[:5]  # Return top 5 key sentences
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_summary_from_content(self, content: str, url: str, instruction: str = None) -> Dict[str, any]:
        """
        Generate summary from content string (for use in reports)
        
        Args:
            content: Page content text
            url: Page URL
            instruction: Original instruction
        
        Returns:
            Summary dictionary
        """
        site = self._identify_site(url.lower())
        
        # Clean content
        cleaned_text = self._clean_text(content)
        
        # Extract title from URL or content
        page_title = url
        if "/" in url:
            page_title = url.split("/")[-1].replace("-", " ").replace("_", " ").title()
        
        # Generate summary
        summary = self._generate_summary(cleaned_text, instruction, site, page_title)
        key_info = self._extract_key_information(cleaned_text, site)
        
        return {
            "site": site,
            "url": url,
            "page_title": page_title,
            "summary": summary,
            "key_information": key_info,
            "content_length": len(cleaned_text),
            "word_count": len(cleaned_text.split())
        }