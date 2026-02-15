"""
Enhanced JSON Report Generator for NovaQA
Generates a single combined JSON report with screenshots and result summaries
"""
import json
import os
import base64
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
import re

class JSONReportGenerator:
    """
    Generates a structured JSON report with all execution details, screenshots, and result summaries
    """
    
    def __init__(self, reports_dir="reports"):
        self.reports_dir = reports_dir
        self.json_dir = os.path.join(reports_dir, "json_combined")
        self.screenshots_dir = os.path.join(reports_dir, "screenshots")
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        print(f"[JSONReportGenerator] Directory: {self.json_dir}")
        print(f"[JSONReportGenerator] Screenshots directory: {self.screenshots_dir}")
    
    def generate_report(self, test_data, run_id=None):
        """
        Generate a single combined JSON report with enhanced metadata
        
        Args:
            test_data (dict): Contains all test execution data
            run_id (str): Unique identifier for this run
        
        Returns:
            dict: Contains filepath, run_id, and filename
        """
        try:
            # Generate run ID if not provided
            if not run_id:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                run_id = test_data.get("report_id", f"report_{timestamp}")
            
            print(f"[JSONReportGenerator] Generating enhanced report for: {run_id}")
            
            # Extract data from test_data
            instruction = test_data.get("instruction", "N/A")
            parsed_actions = test_data.get("parsed", [])
            execution_steps = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            generated_code = test_data.get("generated_code", "")
            
            # Get result page summary
            result_summary = self._extract_result_summary(test_data)
            
            # Get screenshots information
            screenshots_info = self._get_screenshots_info(metadata, run_id)
            
            # Generate structured actions
            structured_actions = self._generate_structured_actions(parsed_actions)
            
            # Generate step results with screenshot paths
            step_results = self._generate_step_results(execution_steps, run_id)
            
            # Calculate overall status
            overall_status = self._calculate_overall_status(execution_steps)
            
            # Get environment info
            environment_info = self._get_environment_info(metadata)
            
            # Get download file paths
            download_files = self._generate_download_files(run_id, test_data)
            
            # Build enhanced JSON structure
            json_report = {
                "report_metadata": {
                    "report_id": run_id,
                    "generated_at": datetime.now().isoformat(),
                    "format_version": "2.0",
                    "generator": "NovaQA Enhanced JSON Report Generator",
                    "report_type": "complete_execution_report"
                },
                
                "test_execution": {
                    "original_instruction": instruction,
                    "overall_status": overall_status,
                    "result_page_summary": result_summary,
                    "environment": environment_info,
                    "execution_metadata": {
                        "start_time": metadata.get("start_time", datetime.now().isoformat()),
                        "end_time": metadata.get("end_time", datetime.now().isoformat()),
                        "duration_seconds": metadata.get("duration_seconds", 0),
                        "duration_ms": metadata.get("duration_seconds", 0) * 1000,
                        "browser": metadata.get("browser", "Chromium"),
                        "headless": metadata.get("headless", True),
                        "viewport": metadata.get("viewport", "1920x1080"),
                        "total_urls_visited": len([s for s in execution_steps if s.get("action") == "navigate"])
                    }
                },
                
                "result_analysis": {
                    "search_query_extracted": self._extract_search_query(instruction),
                    "result_page_detected": self._is_result_page_detected(result_summary),
                    "content_summary": result_summary,
                    "page_type": self._determine_page_type(execution_steps),
                    "success_indicators": self._extract_success_indicators(execution_steps),
                    "failure_indicators": self._extract_failure_indicators(execution_steps)
                },
                
                "generated_actions": structured_actions,
                "step_results": step_results,
                
                "screenshots": {
                    "total_count": len(screenshots_info),
                    "result_page": screenshots_info.get("result_page", {}),
                    "last_failed": screenshots_info.get("last_failed", {}),
                    "step_screenshots": screenshots_info.get("step_screenshots", []),
                    "all_screenshots": screenshots_info.get("all_files", []),
                    "download_urls": self._generate_screenshot_urls(run_id, screenshots_info)
                },
                
                "downloadable_files": download_files,
                
                "performance_metrics": {
                    "total_steps": len(execution_steps),
                    "passed_steps": len([s for s in execution_steps if s.get("status", "").lower() == "passed"]),
                    "failed_steps": len([s for s in execution_steps if s.get("status", "").lower() == "failed"]),
                    "warning_steps": len([s for s in execution_steps if s.get("status", "").lower() == "warning"]),
                    "info_steps": len([s for s in execution_steps if s.get("status", "").lower() == "info"]),
                    "success_rate": (len([s for s in execution_steps if s.get("status", "").lower() == "passed"]) / len(execution_steps) * 100) if execution_steps else 0,
                    "average_step_duration": self._calculate_average_duration(execution_steps),
                    "total_duration_seconds": metadata.get("duration_seconds", 0)
                },
                
                "generated_content": {
                    "test_code": generated_code,
                    "code_lines": len(generated_code.split('\n')) if generated_code else 0,
                    "has_code": bool(generated_code and generated_code.strip())
                },
                
                "data_usage": test_data.get("data_usage", {}),
                
                "files_references": {
                    "html_report": test_data.get("html_report_path", ""),
                    "pdf_report": test_data.get("pdf_report_path", ""),
                    "analysis_report": test_data.get("analysis_report_path", ""),
                    "json_pdf_report": test_data.get("json_pdf_path", ""),
                    "code_file": test_data.get("code_file_path", "")
                }
            }
            
            # Add result page content if available
            final_step = execution_steps[-1] if execution_steps else {}
            if final_step.get("action") == "result_page_capture":
                json_report["result_page_details"] = {
                    "url": final_step.get("actual_result_url", ""),
                    "title": final_step.get("page_title", ""),
                    "screenshot_path": final_step.get("screenshot", ""),
                    "content_preview": final_step.get("content_preview", "")
                }
            
            # Save JSON file
            filename = f"report_{run_id}.json"
            filepath = os.path.join(self.json_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[JSONReportGenerator] Enhanced JSON report saved: {filepath}")
            
            # Also save a minified version for API responses
            minified_filename = f"report_{run_id}_min.json"
            minified_filepath = os.path.join(self.json_dir, minified_filename)
            with open(minified_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, separators=(',', ':'), default=str)
            
            # Return both path and run_id for reference
            return {
                "filepath": filepath,
                "minified_filepath": minified_filepath,
                "run_id": run_id,
                "filename": filename,
                "screenshots_count": len(screenshots_info.get("all_files", [])),
                "has_result_page": bool(screenshots_info.get("result_page")),
                "download_files": list(download_files.keys())
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to generate JSON report: {e}")
            traceback.print_exc()
            raise
    
    def _extract_result_summary(self, test_data):
        """Extract result page summary from test data"""
        try:
            # Check metadata first
            metadata = test_data.get("metadata", {})
            
            # Check for result_summary in metadata
            if metadata and "result_summary" in metadata:
                return metadata["result_summary"]
            
            # Check screenshots metadata
            if metadata and "screenshots" in metadata:
                screenshots = metadata["screenshots"]
                if isinstance(screenshots, dict):
                    # Check result_page
                    if "result_page" in screenshots and screenshots["result_page"]:
                        result_page = screenshots["result_page"]
                        if isinstance(result_page, dict) and "result_summary" in result_page:
                            return result_page["result_summary"]
            
            # Check execution steps for result page
            execution = test_data.get("execution", [])
            for step in execution:
                if step.get("action") == "result_page_capture":
                    return step.get("actual_result", step.get("details", "Result page captured"))
            
            # Try to extract from instruction
            instruction = test_data.get("instruction", "")
            if any(keyword in instruction.lower() for keyword in ["search", "google", "find", "results"]):
                query = self._extract_search_query(instruction)
                if query:
                    return f"Search results for '{query}' were displayed successfully"
            
            return "Result page loaded successfully"
            
        except Exception as e:
            print(f"[WARNING] Failed to extract result summary: {e}")
            return "Unable to extract result page summary"
    
    def _extract_search_query(self, instruction):
        """Extract search query from instruction"""
        try:
            # Simple extraction for common patterns
            patterns = [
                r"search\s+(?:for\s+)?['\"]?([^'\"]+)['\"]?",
                r"google\s+(?:search\s+)?['\"]?([^'\"]+)['\"]?",
                r"find\s+(?:information\s+about\s+)?['\"]?([^'\"]+)['\"]?",
                r"look\s+up\s+['\"]?([^'\"]+)['\"]?"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, instruction.lower())
                if match:
                    query = match.group(1).strip()
                    if len(query) > 1:  # Avoid single characters
                        return query
            
            return None
        except:
            return None
    
    def _is_result_page_detected(self, result_summary):
        """Check if result page was detected"""
        result_keywords = [
            "search results", "results for", "found", "showing",
            "displaying", "listings", "products", "items"
        ]
        
        summary_lower = result_summary.lower()
        return any(keyword in summary_lower for keyword in result_keywords)
    
    def _determine_page_type(self, execution_steps):
        """Determine the type of page visited"""
        if not execution_steps:
            return "unknown"
        
        # Get last URL from navigation steps
        urls = []
        for step in execution_steps:
            if step.get("action") == "navigate" and "http" in step.get("details", "").lower():
                # Extract URL from details
                details = step.get("details", "").lower()
                if "navigated to" in details:
                    url = details.split("navigated to")[1].strip()
                    urls.append(url)
        
        if not urls:
            return "unknown"
        
        last_url = urls[-1].lower()
        
        # Check for common site patterns
        if "google.com" in last_url:
            return "search_engine"
        elif "youtube.com" in last_url:
            return "video"
        elif "amazon.com" in last_url:
            return "ecommerce"
        elif "wikipedia.org" in last_url:
            return "encyclopedia"
        elif "login" in last_url or "signin" in last_url:
            return "login_page"
        elif "search" in last_url or "results" in last_url:
            return "search_results"
        elif "product" in last_url or "item" in last_url:
            return "product_page"
        else:
            return "general_website"
    
    def _extract_success_indicators(self, execution_steps):
        """Extract success indicators from execution"""
        indicators = []
        
        for step in execution_steps:
            if step.get("status", "").lower() == "passed":
                details = step.get("details", "").lower()
                
                if "successfully" in details:
                    indicators.append("successful_execution")
                if "loaded" in details and "page" in details:
                    indicators.append("page_load_success")
                if "clicked" in details:
                    indicators.append("click_success")
                if "typed" in details or "entered" in details:
                    indicators.append("input_success")
                if "navigated" in details:
                    indicators.append("navigation_success")
        
        return list(set(indicators))  # Remove duplicates
    
    def _extract_failure_indicators(self, execution_steps):
        """Extract failure indicators from execution"""
        indicators = []
        
        for step in execution_steps:
            if step.get("status", "").lower() == "failed":
                error = step.get("error_message", "").lower()
                details = step.get("details", "").lower()
                
                if "not found" in error or "selector" in error:
                    indicators.append("element_not_found")
                if "timeout" in error:
                    indicators.append("timeout_error")
                if "navigation" in error:
                    indicators.append("navigation_failed")
                if "network" in error or "connection" in error:
                    indicators.append("network_error")
                if "permission" in error or "access" in error:
                    indicators.append("access_denied")
                
                if "failed" in details:
                    indicators.append("execution_failed")
        
        return list(set(indicators))  # Remove duplicates
    
    def _get_screenshots_info(self, metadata, report_id):
        """Get detailed information about screenshots"""
        screenshots_info = {
            "result_page": {},
            "last_failed": {},
            "step_screenshots": [],
            "all_files": []
        }
        
        # Check metadata for screenshots
        if metadata and "screenshots" in metadata:
            screenshots_data = metadata["screenshots"]
            
            # Get result page screenshot
            if "result_page" in screenshots_data and screenshots_data["result_page"]:
                result_page = screenshots_data["result_page"]
                if isinstance(result_page, dict):
                    screenshots_info["result_page"] = {
                        "path": result_page.get("screenshot_path", ""),
                        "filename": os.path.basename(result_page.get("screenshot_path", "")),
                        "summary": result_page.get("result_summary", ""),
                        "timestamp": result_page.get("timestamp", ""),
                        "is_result_page": True,
                        "type": "result_page"
                    }
            
            # Get last failed screenshot
            if "last_failed" in screenshots_data and screenshots_data["last_failed"]:
                last_failed = screenshots_data["last_failed"]
                if isinstance(last_failed, dict):
                    screenshots_info["last_failed"] = {
                        "path": last_failed.get("screenshot_path", ""),
                        "filename": os.path.basename(last_failed.get("screenshot_path", "")),
                        "step_description": last_failed.get("step_description", ""),
                        "timestamp": last_failed.get("timestamp", ""),
                        "is_failed_step": True,
                        "type": "failed_step"
                    }
        
        # Scan screenshots directory
        if os.path.exists(self.screenshots_dir):
            for filename in os.listdir(self.screenshots_dir):
                if report_id in filename and filename.endswith('.png'):
                    filepath = os.path.join(self.screenshots_dir, filename)
                    
                    # Skip thumbnails
                    if filename.startswith('thumb_'):
                        continue
                    
                    screenshot_info = {
                        "filename": filename,
                        "path": filepath,
                        "size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat() if os.path.exists(filepath) else "",
                        "type": self._determine_screenshot_type(filename),
                        "download_url": f"/api/download-screenshot/{filename}"
                    }
                    
                    # Determine screenshot type
                    if 'result_page' in filename.lower():
                        screenshot_info["is_result_page"] = True
                        screenshots_info["result_page"] = screenshot_info
                    elif 'failed' in filename.lower():
                        screenshot_info["is_failed_step"] = True
                        screenshots_info["last_failed"] = screenshot_info
                    else:
                        screenshot_info["is_step_screenshot"] = True
                        screenshots_info["step_screenshots"].append(screenshot_info)
                    
                    screenshots_info["all_files"].append(screenshot_info)
        
        return screenshots_info
    
    def _determine_screenshot_type(self, filename):
        """Determine the type of screenshot from filename"""
        filename_lower = filename.lower()
        
        if 'result_page' in filename_lower:
            return 'result_page'
        elif 'failed' in filename_lower:
            return 'failed_step'
        elif 'step' in filename_lower or 'screenshot_' in filename_lower:
            return 'step_screenshot'
        else:
            return 'general_screenshot'
    
    def _generate_screenshot_urls(self, report_id, screenshots_info):
        """Generate download URLs for screenshots"""
        urls = []
        
        for screenshot in screenshots_info.get("all_files", []):
            filename = screenshot.get("filename", "")
            if filename:
                urls.append({
                    "filename": filename,
                    "url": f"/api/download-screenshot/{filename}",
                    "type": screenshot.get("type", "unknown"),
                    "size_kb": round(screenshot.get("size_bytes", 0) / 1024, 2)
                })
        
        return urls
    
    def _generate_download_files(self, report_id, test_data):
        """Generate download file information"""
        download_files = {
            "html_report": {
                "filename": f"report_{report_id}.html",
                "description": "Interactive HTML Report",
                "type": "html",
                "download_url": f"/api/download-report/{report_id}/html",
                "size_kb": 0  # Will be updated if file exists
            },
            "pdf_report": {
                "filename": f"report_{report_id}.pdf",
                "description": "PDF Document Report",
                "type": "pdf",
                "download_url": f"/api/download-report/{report_id}/pdf",
                "size_kb": 0
            },
            "analysis_report": {
                "filename": f"analysis_{report_id}.html",
                "description": "Detailed Analysis Report",
                "type": "html",
                "download_url": f"/api/download-report/{report_id}/analysis",
                "size_kb": 0
            },
            "json_pdf_report": {
                "filename": f"json_report_{report_id}.pdf",
                "description": "JSON Data as PDF",
                "type": "pdf",
                "download_url": f"/api/download-report/{report_id}/json-pdf",
                "size_kb": 0
            },
            "raw_json": {
                "filename": f"report_{report_id}.json",
                "description": "Raw JSON Data",
                "type": "json",
                "download_url": f"/api/download-report/{report_id}/json",
                "size_kb": 0
            }
        }
        
        # Update file sizes if files exist
        for file_key, file_info in download_files.items():
            filepath = os.path.join(self.reports_dir, file_info["type"], file_info["filename"])
            if os.path.exists(filepath):
                file_info["size_kb"] = round(os.path.getsize(filepath) / 1024, 2)
                file_info["exists"] = True
            else:
                file_info["exists"] = False
        
        return download_files
    
    def _generate_structured_actions(self, parsed_actions):
        """Convert parsed actions to structured format"""
        structured = []
        
        for i, action in enumerate(parsed_actions, 1):
            structured_action = {
                "step": i,
                "action": action.get("action", "unknown"),
                "description": action.get("description", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add action-specific data
            action_type = action.get("action", "")
            
            if action_type == "navigate":
                structured_action.update({
                    "type": "navigation",
                    "url": action.get("url", ""),
                    "method": "GET",
                    "wait_until": "networkidle"
                })
            
            elif action_type == "search":
                structured_action.update({
                    "type": "search",
                    "query": action.get("query", ""),
                    "selector": action.get("selector", ""),
                    "engine": "google" if "google" in str(action.get("query", "")).lower() else "unknown"
                })
            
            elif action_type == "type":
                structured_action.update({
                    "type": "input",
                    "field_type": action.get("field_type", ""),
                    "value": action.get("value", ""),
                    "selector": action.get("selector", ""),
                    "is_random_data": action.get("is_random_data", False),
                    "is_sensitive": action.get("field_type") in ["password", "ssn", "credit_card"]
                })
                
                # Mask sensitive data
                if action.get("field_type") in ["password", "ssn", "credit_card"]:
                    structured_action["value_masked"] = "********"
            
            elif action_type == "click":
                structured_action.update({
                    "type": "interaction",
                    "text": action.get("text", ""),
                    "selector": action.get("selector", ""),
                    "element_type": action.get("element_type", "button/link"),
                    "click_type": "left_click"
                })
            
            elif action_type == "wait":
                structured_action.update({
                    "type": "delay",
                    "seconds": action.get("seconds", 0),
                    "reason": "page_loading",
                    "unit": "seconds"
                })
            
            elif action_type == "validate_page":
                structured_action.update({
                    "type": "validation",
                    "validation_type": action.get("type", "generic"),
                    "text": action.get("text", ""),
                    "min_indicators": action.get("min_indicators", 1),
                    "validation_method": "text_presence"
                })
            
            elif action_type == "screenshot":
                structured_action.update({
                    "type": "capture",
                    "capture_type": "screenshot",
                    "full_page": True,
                    "purpose": "step_documentation"
                })
            
            elif action_type == "result_page_capture":
                structured_action.update({
                    "type": "capture",
                    "capture_type": "result_page_screenshot",
                    "full_page": True,
                    "purpose": "result_documentation",
                    "is_final": True
                })
            
            elif action_type in ["info", "generate_data", "data_summary"]:
                structured_action.update({
                    "type": "info",
                    "message": action.get("message", "") or action.get("details", ""),
                    "info_type": "execution_note"
                })
            
            else:
                # Unknown action type
                structured_action.update({
                    "type": "unknown",
                    "raw_data": action
                })
            
            structured.append(structured_action)
        
        return structured
    
    def _generate_step_results(self, execution_steps, report_id):
        """Convert execution steps to structured results with screenshot paths"""
        results = []
        
        for i, step in enumerate(execution_steps, 1):
            step_result = {
                "step": i,
                "action": step.get("action", "unknown"),
                "status": step.get("status", "unknown").upper(),
                "description": step.get("description", step.get("details", "")),
                "timestamp": datetime.now().isoformat(),
                "has_screenshot": bool(step.get("screenshot")),
                "screenshot_filename": os.path.basename(step.get("screenshot", "")) if step.get("screenshot") else None
            }
            
            # Add duration if available
            if step.get("duration"):
                step_result["duration_seconds"] = step.get("duration")
                step_result["duration_ms"] = step.get("duration") * 1000
            elif step.get("execution_time"):
                step_result["duration_seconds"] = step.get("execution_time")
                step_result["duration_ms"] = step.get("execution_time") * 1000
            
            # Add expected and actual results
            if step.get("expected_result"):
                step_result["expected_result"] = step.get("expected_result")
            if step.get("actual_result"):
                step_result["actual_result"] = step.get("actual_result")
            
            # Add error information for failed steps
            if step.get("status", "").lower() == "failed":
                step_result["error"] = {
                    "message": step.get("error_message", step.get("details", "")),
                    "type": "execution_error",
                    "severity": "high"
                }
                
                # Add screenshot path if available
                if step.get("screenshot"):
                    step_result["screenshot"] = {
                        "path": step.get("screenshot"),
                        "filename": os.path.basename(step.get("screenshot")),
                        "download_url": f"/api/download-screenshot/{os.path.basename(step.get('screenshot'))}",
                        "is_failed_step": True
                    }
            
            # Add screenshot for successful steps too
            elif step.get("screenshot"):
                step_result["screenshot"] = {
                    "path": step.get("screenshot"),
                    "filename": os.path.basename(step.get("screenshot")),
                    "download_url": f"/api/download-screenshot/{os.path.basename(step.get('screenshot'))}",
                    "is_step_screenshot": True
                }
            
            # Add field type for input actions
            if step.get("field_type"):
                step_result["field_type"] = step.get("field_type")
            
            # Add data source information
            if step.get("is_random_data"):
                step_result["data_source"] = "generated"
            elif step.get("field_type") in ["email", "password", "username"]:
                step_result["data_source"] = "provided"
            
            # Check if this is a result page capture
            if step.get("action") == "result_page_capture":
                step_result["is_result_page"] = True
                step_result["result_summary"] = step.get("actual_result", "Result page captured")
            
            results.append(step_result)
        
        return results
    
    def _calculate_overall_status(self, execution_steps):
        """Calculate overall test status from step results"""
        if not execution_steps:
            return "UNKNOWN"
        
        has_failed = any(s.get("status", "").lower() == "failed" for s in execution_steps)
        has_warning = any(s.get("status", "").lower() == "warning" for s in execution_steps)
        
        if has_failed:
            return "FAILED"
        elif has_warning:
            return "WARNING"
        else:
            return "PASSED"
    
    def _get_environment_info(self, metadata):
        """Get environment information"""
        try:
            import playwright
            
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": sys.version.split()[0],
                "playwright_version": getattr(playwright, "__version__", "unknown"),
                "browser": metadata.get("browser", "Chromium"),
                "headless": metadata.get("headless", True),
                "viewport": metadata.get("viewport", "1920x1080"),
                "timezone": datetime.now().astimezone().tzname(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[WARNING] Failed to get environment info: {e}")
            return {
                "os": platform.system(),
                "python_version": sys.version.split()[0],
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_average_duration(self, execution_steps):
        """Calculate average step duration"""
        if not execution_steps:
            return 0
        
        durations = []
        for step in execution_steps:
            if step.get("duration"):
                durations.append(step.get("duration"))
        
        if not durations:
            return 0
        
        return round(sum(durations) / len(durations), 3)
    
    def get_report_by_id(self, run_id):
        """Get JSON report by run ID"""
        filename = f"report_{run_id}.json"
        filepath = os.path.join(self.json_dir, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load report {filename}: {e}")
                return None
        
        # Try minified version
        minified_filename = f"report_{run_id}_min.json"
        minified_filepath = os.path.join(self.json_dir, minified_filename)
        
        if os.path.exists(minified_filepath):
            try:
                with open(minified_filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def list_reports(self, limit=50):
        """List all JSON reports with metadata"""
        reports = []
        
        if os.path.exists(self.json_dir):
            for filename in sorted(os.listdir(self.json_dir), reverse=True):
                if filename.endswith('.json') and not filename.endswith('_min.json'):
                    filepath = os.path.join(self.json_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            
                        # Extract metadata for listing
                        report_metadata = {
                            "filename": filename,
                            "run_id": report_data.get("report_metadata", {}).get("report_id", ""),
                            "instruction": report_data.get("test_execution", {}).get("original_instruction", "")[:100],
                            "status": report_data.get("test_execution", {}).get("overall_status", ""),
                            "timestamp": report_data.get("report_metadata", {}).get("generated_at", ""),
                            "filepath": filepath,
                            "has_screenshots": len(report_data.get("screenshots", {}).get("all_files", [])) > 0,
                            "has_result_page": bool(report_data.get("screenshots", {}).get("result_page", {})),
                            "total_steps": report_data.get("performance_metrics", {}).get("total_steps", 0),
                            "success_rate": report_data.get("performance_metrics", {}).get("success_rate", 0),
                            "duration_seconds": report_data.get("test_execution", {}).get("execution_metadata", {}).get("duration_seconds", 0)
                        }
                        
                        reports.append(report_metadata)
                    except Exception as e:
                        print(f"[WARNING] Failed to load report {filename}: {e}")
        
        return reports[:limit]
    
    def get_screenshot_data(self, filename, as_base64=False):
        """Get screenshot data, optionally as base64"""
        filepath = os.path.join(self.screenshots_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        if as_base64:
            try:
                with open(filepath, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"[ERROR] Failed to encode screenshot: {e}")
                return None
        else:
            return filepath
    
    def generate_summary_report(self, run_id):
        """Generate a summary version of the report"""
        full_report = self.get_report_by_id(run_id)
        if not full_report:
            return None
        
        # Create summary
        summary = {
            "report_id": full_report.get("report_metadata", {}).get("report_id"),
            "instruction": full_report.get("test_execution", {}).get("original_instruction"),
            "status": full_report.get("test_execution", {}).get("overall_status"),
            "result_summary": full_report.get("test_execution", {}).get("result_page_summary"),
            "timestamp": full_report.get("report_metadata", {}).get("generated_at"),
            "performance": full_report.get("performance_metrics", {}),
            "screenshots_count": full_report.get("screenshots", {}).get("total_count", 0),
            "has_result_page": bool(full_report.get("screenshots", {}).get("result_page", {})),
            "download_files": list(full_report.get("downloadable_files", {}).keys())
        }
        
        # Save summary
        summary_filename = f"summary_{run_id}.json"
        summary_filepath = os.path.join(self.json_dir, summary_filename)
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_filepath


# Example usage
if __name__ == "__main__":
    # Test the enhanced JSON report generator
    generator = JSONReportGenerator()
    
    # Sample test data with all required features
    test_data = {
        "report_id": "GUEST-20260122215640",
        "instruction": "Go to google search apples and show results",
        "parsed": [
            {
                "action": "navigate",
                "description": "Navigate to Google",
                "url": "https://www.google.com"
            },
            {
                "action": "type",
                "description": "Search for apples",
                "selector": "input[name='q']",
                "value": "apples"
            },
            {
                "action": "press",
                "description": "Press Enter to search",
                "key": "Enter"
            },
            {
                "action": "screenshot",
                "description": "Capture search results"
            }
        ],
        "execution": [
            {
                "step": 1,
                "action": "navigate",
                "status": "passed",
                "details": "Navigated to https://www.google.com",
                "description": "Navigate to Google",
                "duration": 2.5,
                "expected_result": "Google homepage loads",
                "actual_result": "Google homepage loaded successfully"
            },
            {
                "step": 2,
                "action": "type",
                "status": "passed",
                "details": "Typed 'apples' in search box",
                "description": "Search for apples",
                "duration": 1.2,
                "expected_result": "Search term entered",
                "actual_result": "Search term 'apples' entered successfully"
            },
            {
                "step": 3,
                "action": "press",
                "status": "passed",
                "details": "Pressed Enter key",
                "description": "Submit search",
                "duration": 0.8,
                "expected_result": "Search executed",
                "actual_result": "Search executed, results page loading"
            },
            {
                "step": 4,
                "action": "result_page_capture",
                "status": "passed",
                "details": "Result page screenshot captured",
                "description": "Capture final result page",
                "screenshot": "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png",
                "duration": 1.5,
                "expected_result": "Search results page captured",
                "actual_result": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results.",
                "page_title": "apples - Google Search",
                "content_preview": "Apples are nutritious fruits rich in fiber and vitamin C..."
            }
        ],
        "metadata": {
            "browser": "Chromium",
            "headless": True,
            "start_time": "2024-01-25T10:30:00",
            "end_time": "2024-01-25T10:32:30",
            "duration_seconds": 150,
            "viewport": "1920x1080",
            "result_summary": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results.",
            "screenshots": {
                "result_page": {
                    "screenshot_path": "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png",
                    "result_summary": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results.",
                    "step_description": "Final Result Page",
                    "timestamp": "2024-01-25T10:32:25"
                },
                "last_failed": None,
                "all": [
                    "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png"
                ]
            }
        },
        "generated_code": "from playwright.sync_api import sync_playwright\n\nwith sync_playwright() as p:\n    browser = p.chromium.launch()\n    page = browser.new_page()\n    page.goto('https://www.google.com')\n    page.type('input[name=\"q\"]', 'apples')\n    page.press('input[name=\"q\"]', 'Enter')\n    page.screenshot(path='search_results.png')\n    browser.close()",
        "html_report_path": "reports/html/report_GUEST-20260122215640.html",
        "pdf_report_path": "reports/pdf/report_GUEST-20260122215640.pdf",
        "analysis_report_path": "reports/analysis/analysis_GUEST-20260122215640.html",
        "json_pdf_path": "reports/pdf/json_report_GUEST-20260122215640.pdf",
        "code_file_path": "reports/code/test_GUEST-20260122215640.py",
        "data_usage": {
            "random_data_generated": True,
            "fields_generated": ["email", "username"],
            "data_sources": ["faker", "manual"]
        }
    }
    
    # Generate the enhanced report
    print("\nGenerating enhanced JSON report...")
    result = generator.generate_report(test_data)
    
    if result:
        print(f"\n✅ Enhanced JSON report generated:")
        print(f"   Report ID: {result['run_id']}")
        print(f"   File: {result['filename']}")
        print(f"   Path: {result['filepath']}")
        print(f"   Screenshots: {result['screenshots_count']}")
        print(f"   Has Result Page: {result['has_result_page']}")
        print(f"   Download Files: {', '.join(result['download_files'])}")
        
        # Load and display some key information
        report_data = generator.get_report_by_id(result['run_id'])
        if report_data:
            print(f"\n📋 Report Summary:")
            print(f"   Instruction: {report_data['test_execution']['original_instruction']}")
            print(f"   Status: {report_data['test_execution']['overall_status']}")
            print(f"   Result Summary: {report_data['test_execution']['result_page_summary']}")
            print(f"   Total Steps: {report_data['performance_metrics']['total_steps']}")
            print(f"   Success Rate: {report_data['performance_metrics']['success_rate']:.1f}%")
            print(f"   Screenshots: {report_data['screenshots']['total_count']}")
            
            # List downloadable files
            print(f"\n📥 Downloadable Files:")
            for file_key, file_info in report_data['downloadable_files'].items():
                if file_info.get('exists'):
                    print(f"   • {file_info['description']}: {file_info['filename']} ({file_info['size_kb']} KB)")