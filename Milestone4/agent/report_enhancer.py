"""
Report Enhancer for NovaQA
Adds enhanced features to existing reports
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch

from agent.result_summarizer import ResultSummarizer


class ReportEnhancer:
    """
    Enhances existing reports with new features
    """
    
    def __init__(self, reports_dir="reports"):
        self.reports_dir = reports_dir
        self.screenshots_dir = os.path.join(reports_dir, "screenshots")
        self.pdf_dir = os.path.join(reports_dir, "pdf")
        self.json_dir = os.path.join(reports_dir, "json_combined")
        
        # Create directories if they don't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        
        self.summarizer = ResultSummarizer()
    
    def generate_enhanced_json_report(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced JSON report with all required information
        
        Args:
            test_data: Original test execution data
        
        Returns:
            Enhanced JSON report
        """
        try:
            # Extract data from test_data
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            generated_code = test_data.get("generated_code", "")
            parsed_actions = test_data.get("parsed", [])
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Calculate summary
            total_steps = len(execution)
            passed_steps = len([s for s in execution if s.get("status", "").lower() == "passed"])
            failed_steps = len([s for s in execution if s.get("status", "").lower() == "failed"])
            success_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0
            
            # Determine overall status
            has_failed_steps = any(s.get("status", "").lower() == "failed" for s in execution)
            has_warning_steps = any(s.get("status", "").lower() == "warning" for s in execution)
            
            if has_failed_steps:
                overall_status = "FAILED"
            elif has_warning_steps:
                overall_status = "WARNING"
            else:
                overall_status = "PASSED"
            
            # Get environment info
            environment_info = self._get_environment_info(metadata)
            
            # Generate action JSON
            action_json = self._generate_action_json(parsed_actions, instruction)
            
            # Generate execution JSON
            execution_json = self._generate_execution_json(execution, metadata, overall_status)
            
            # Generate result page summary if available
            result_summary = None
            if metadata.get("final_screenshot"):
                # Try to extract summary from execution data
                for step in reversed(execution):  # Look from end
                    if step.get("details") and "Navigated to" in step.get("details", ""):
                        url = step.get("details", "").replace("Navigated to ", "").strip()
                        result_summary = self.summarizer.generate_summary_from_content(
                            content=" ".join([s.get("details", "") for s in execution if s.get("details")]),
                            url=url,
                            instruction=instruction
                        )
                        break
            
            # Build enhanced JSON structure
            enhanced_report = {
                "report_metadata": {
                    "report_id": report_id,
                    "generated_at": datetime.now().isoformat(),
                    "format_version": "2.0",
                    "enhanced_features": [
                        "action_json",
                        "execution_json", 
                        "result_summary",
                        "downloadable_formats"
                    ]
                },
                
                "test_overview": {
                    "original_instruction": instruction,
                    "overall_status": overall_status,
                    "execution_summary": {
                        "total_steps": total_steps,
                        "passed_steps": passed_steps,
                        "failed_steps": failed_steps,
                        "warning_steps": len([s for s in execution if s.get("status", "").lower() == "warning"]),
                        "info_steps": len([s for s in execution if s.get("status", "").lower() == "info"]),
                        "success_rate": round(success_rate, 2)
                    },
                    "environment": environment_info
                },
                
                "action_json": action_json,
                "execution_json": execution_json,
                
                "result_page_analysis": result_summary or {
                    "note": "No result page analysis available",
                    "final_url": metadata.get("final_url", "N/A")
                },
                
                "downloadable_assets": {
                    "screenshots": metadata.get("screenshots", []),
                    "final_screenshot": metadata.get("final_screenshot"),
                    "html_report": f"/api/download-report/{report_id}?format=html",
                    "pdf_report": f"/api/download-report/{report_id}?format=pdf",
                    "json_report": f"/api/generate-json-report/{report_id}",
                    "json_pdf_report": f"/api/generate-json-pdf/{report_id}",
                    "analysis_report": f"/api/generate-analysis-report/{report_id}",
                    "single_screenshot": metadata.get("final_screenshot") and f"/api/download-screenshot/{os.path.basename(metadata['final_screenshot'])}"
                },
                
                "data_usage": test_data.get("data_usage", {}),
                "generated_code_preview": generated_code[:500] + "..." if len(generated_code) > 500 else generated_code
            }
            
            # Save JSON file
            filename = f"enhanced_report_{report_id}.json"
            filepath = os.path.join(self.json_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[ReportEnhancer] Enhanced JSON report saved: {filepath}")
            
            return {
                "filepath": filepath,
                "filename": filename,
                "download_url": f"/api/download-enhanced-json/{filename}",
                "report_data": enhanced_report
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to generate enhanced JSON report: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_action_json(self, parsed_actions: List[Dict], instruction: str) -> Dict[str, Any]:
        """Generate Action JSON with step-by-step actions"""
        action_steps = []
        
        for i, action in enumerate(parsed_actions, 1):
            step = {
                "step_number": i,
                "action_type": action.get("action", "unknown"),
                "description": action.get("description", ""),
                "extracted_from_instruction": self._extract_from_instruction(instruction, action),
                "generated_at": datetime.now().isoformat()
            }
            
            # Add action-specific details
            action_type = action.get("action", "")
            
            if action_type == "navigate":
                step.update({
                    "action_details": {
                        "url": action.get("url", ""),
                        "method": "GET",
                        "purpose": "Load web page"
                    }
                })
            
            elif action_type == "search":
                step.update({
                    "action_details": {
                        "query": action.get("query", ""),
                        "selector": action.get("selector", "auto-detected"),
                        "purpose": "Search for content"
                    }
                })
            
            elif action_type == "type":
                step.update({
                    "action_details": {
                        "field_type": action.get("field_type", ""),
                        "value_preview": self._mask_sensitive_data(
                            action.get("field_type", ""), 
                            action.get("value", "")
                        ),
                        "selector": action.get("selector", "auto-detected"),
                        "data_source": "provided" if not action.get("is_random_data", False) else "generated",
                        "purpose": "Fill form field"
                    }
                })
            
            elif action_type == "click":
                step.update({
                    "action_details": {
                        "element_text": action.get("text", ""),
                        "selector": action.get("selector", "auto-detected"),
                        "element_type": "button/link/input",
                        "purpose": "Click interactive element"
                    }
                })
            
            elif action_type == "wait":
                step.update({
                    "action_details": {
                        "duration_seconds": action.get("seconds", 0),
                        "purpose": "Wait for page load/processing"
                    }
                })
            
            elif action_type == "validate_page":
                step.update({
                    "action_details": {
                        "validation_type": action.get("type", "generic"),
                        "expected_content": action.get("text", ""),
                        "minimum_indicators": action.get("min_indicators", 1),
                        "purpose": "Verify page content"
                    }
                })
            
            else:
                step.update({
                    "action_details": {
                        "raw_data": action,
                        "purpose": "Custom action"
                    }
                })
            
            action_steps.append(step)
        
        return {
            "original_instruction": instruction,
            "total_actions": len(action_steps),
            "actions": action_steps,
            "parsing_method": "AI-enhanced natural language processing",
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_execution_json(self, execution: List[Dict], metadata: Dict, overall_status: str) -> Dict[str, Any]:
        """Generate Execution JSON with detailed results"""
        execution_steps = []
        
        for i, step in enumerate(execution, 1):
            step_result = {
                "step_number": i,
                "action_performed": step.get("action", "unknown").replace("_", " ").title(),
                "status": step.get("status", "unknown").upper(),
                "timestamp": datetime.now().isoformat(),
                "details": step.get("details", step.get("description", ""))
            }
            
            # Add execution metadata
            if step.get("duration"):
                step_result["execution_time_ms"] = step.get("duration") * 1000
            elif step.get("execution_time"):
                step_result["execution_time_ms"] = step.get("execution_time") * 1000
            
            # Add error information for failed steps
            if step.get("status", "").lower() == "failed":
                step_result["error"] = {
                    "message": step.get("error_message", step.get("details", "")),
                    "type": "execution_error",
                    "recovery_suggestion": self._get_recovery_suggestion(step.get("details", ""))
                }
            
            # Add screenshot information
            if step.get("screenshot"):
                step_result["screenshot"] = {
                    "path": step.get("screenshot"),
                    "available": os.path.exists(step.get("screenshot")),
                    "download_url": f"/api/download-screenshot/{os.path.basename(step.get('screenshot'))}"
                }
            
            # Add field information for input actions
            if step.get("field_type"):
                step_result["field_processed"] = {
                    "type": step.get("field_type"),
                    "data_source": step.get("data_source", "unknown")
                }
            
            execution_steps.append(step_result)
        
        # Calculate execution metrics
        total_time = metadata.get("duration_seconds", 0)
        
        return {
            "execution_summary": {
                "overall_status": overall_status,
                "browser_used": metadata.get("browser", "Chromium"),
                "execution_mode": "Headless" if metadata.get("headless", True) else "Headed",
                "start_time": metadata.get("start_time", datetime.now().isoformat()),
                "end_time": metadata.get("end_time", datetime.now().isoformat()),
                "total_duration_seconds": total_time,
                "average_step_time": total_time / len(execution) if execution else 0,
                "screenshots_captured": len(metadata.get("screenshots", [])),
                "final_screenshot": metadata.get("final_screenshot")
            },
            "step_by_step_results": execution_steps,
            "performance_metrics": {
                "steps_per_second": len(execution) / total_time if total_time > 0 else 0,
                "success_rate_percentage": (len([s for s in execution if s.get("status", "").lower() == "passed"]) / len(execution) * 100) if execution else 0,
                "failure_rate_percentage": (len([s for s in execution if s.get("status", "").lower() == "failed"]) / len(execution) * 100) if execution else 0
            },
            "quality_indicators": {
                "has_screenshots": len(metadata.get("screenshots", [])) > 0,
                "has_detailed_errors": any(s.get("error") for s in execution_steps),
                "has_performance_data": total_time > 0,
                "execution_completeness": "complete" if execution and execution[-1].get("status") else "partial"
            }
        }
    
    def _extract_from_instruction(self, instruction: str, action: Dict) -> str:
        """Extract which part of instruction led to this action"""
        action_desc = action.get("description", "").lower()
        instruction_lower = instruction.lower()
        
        # Simple keyword matching
        keywords = {
            "navigate": ["go to", "open", "visit", "navigate"],
            "search": ["search", "find", "look for"],
            "type": ["type", "enter", "fill", "input"],
            "click": ["click", "press", "tap", "select"],
            "wait": ["wait", "pause", "sleep"],
            "validate": ["verify", "check", "validate", "confirm"]
        }
        
        for action_type, kw_list in keywords.items():
            if action.get("action") == action_type:
                for keyword in kw_list:
                    if keyword in instruction_lower:
                        return f"From instruction: '{keyword}'"
        
        return "Derived from overall instruction context"
    
    def _mask_sensitive_data(self, field_type: str, value: str) -> str:
        """Mask sensitive data in logs"""
        if not value:
            return ""
        
        sensitive_fields = ["password", "pass", "pwd", "secret", "token", "key"]
        
        if any(sensitive in field_type.lower() for sensitive in sensitive_fields):
            return "********"
        
        # Truncate long values
        if len(value) > 20:
            return value[:17] + "..."
        
        return value
    
    def _get_recovery_suggestion(self, error_details: str) -> str:
        """Get recovery suggestions based on error"""
        error_lower = error_details.lower()
        
        if "not found" in error_lower or "selector" in error_lower:
            return "Check element selector and ensure page is loaded"
        elif "timeout" in error_lower:
            return "Increase timeout or check network connectivity"
        elif "navigation" in error_lower:
            return "Verify URL is correct and accessible"
        elif "network" in error_lower or "connection" in error_lower:
            return "Check internet connection and firewall settings"
        else:
            return "Review test script and execution environment"
    
    def _get_environment_info(self, metadata: Dict) -> Dict[str, str]:
        """Get environment information"""
        import platform
        import sys
        import playwright
        
        return {
            "operating_system": f"{platform.system()} {platform.version()}",
            "python_version": sys.version.split()[0],
            "playwright_version": getattr(playwright, "__version__", "unknown"),
            "browser": metadata.get("browser", "Chromium"),
            "execution_mode": "Headless" if metadata.get("headless", True) else "Headed",
            "screen_resolution": metadata.get("screen_resolution", "1920x1080"),
            "user_agent": metadata.get("user_agent", "Mozilla/5.0 (Playwright)")
        }
    
    def generate_json_pdf_report(self, json_data: Dict, report_id: str = None) -> str:
        """
        Generate PDF report from JSON data
        
        Args:
            json_data: JSON report data
            report_id: Report ID for filename
        
        Returns:
            Path to generated PDF file
        """
        try:
            if not report_id:
                report_id = f"json_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            filename = f"json_report_{report_id}.pdf"
            filepath = os.path.join(self.pdf_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title=f"JSON Report - {report_id}"
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'JsonTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#8B5CF6'),
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'JsonHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#06B6D4'),
                spaceAfter=10
            )
            
            normal_style = ParagraphStyle(
                'JsonNormal',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=6,
                fontName='Courier'
            )
            
            story = []
            
            # Title
            story.append(Paragraph("JSON Test Report", title_style))
            story.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Test Overview
            if "test_overview" in json_data:
                story.append(Paragraph("Test Overview", heading_style))
                
                overview = json_data["test_overview"]
                overview_data = [
                    ["Instruction", overview.get("original_instruction", "N/A")],
                    ["Status", overview.get("overall_status", "UNKNOWN")],
                    ["Total Steps", str(overview.get("execution_summary", {}).get("total_steps", 0))],
                    ["Passed", str(overview.get("execution_summary", {}).get("passed_steps", 0))],
                    ["Failed", str(overview.get("execution_summary", {}).get("failed_steps", 0))],
                    ["Success Rate", f"{overview.get('execution_summary', {}).get('success_rate', 0):.1f}%"]
                ]
                
                overview_table = Table(overview_data, colWidths=[1.5*inch, 4*inch])
                overview_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(overview_table)
                story.append(Spacer(1, 20))
            
            # Action JSON
            if "action_json" in json_data:
                story.append(Paragraph("Generated Actions", heading_style))
                
                action_json = json_data["action_json"]
                story.append(Paragraph(f"Total Actions: {action_json.get('total_actions', 0)}", styles['Normal']))
                
                # Add first few actions
                actions = action_json.get("actions", [])[:5]
                for action in actions:
                    story.append(Paragraph(f"Step {action.get('step_number')}: {action.get('action_type')} - {action.get('description')}", normal_style))
                
                if len(action_json.get("actions", [])) > 5:
                    story.append(Paragraph(f"... and {len(action_json['actions']) - 5} more actions", styles['Italic']))
                
                story.append(Spacer(1, 15))
            
            # Execution JSON
            if "execution_json" in json_data:
                story.append(Paragraph("Execution Results", heading_style))
                
                exec_json = json_data["execution_json"]
                exec_summary = exec_json.get("execution_summary", {})
                
                exec_data = [
                    ["Browser", exec_summary.get("browser_used", "N/A")],
                    ["Mode", exec_summary.get("execution_mode", "N/A")],
                    ["Duration", f"{exec_summary.get('total_duration_seconds', 0):.2f} seconds"],
                    ["Start Time", exec_summary.get("start_time", "N/A")],
                    ["End Time", exec_summary.get("end_time", "N/A")],
                    ["Screenshots", str(len(json_data.get('downloadable_assets', {}).get('screenshots', [])))],
                ]
                
                exec_table = Table(exec_data, colWidths=[1.5*inch, 4*inch])
                exec_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                story.append(exec_table)
                story.append(Spacer(1, 15))
            
            # Result Page Analysis
            if "result_page_analysis" in json_data and json_data["result_page_analysis"].get("summary"):
                story.append(Paragraph("Result Page Analysis", heading_style))
                
                analysis = json_data["result_page_analysis"]
                story.append(Paragraph(f"Site: {analysis.get('site', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"URL: {analysis.get('url', 'N/A')}", styles['Normal']))
                story.append(Paragraph("Summary:", styles['Normal']))
                story.append(Paragraph(analysis.get("summary", "No summary available"), styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Downloadable Assets
            if "downloadable_assets" in json_data:
                story.append(Paragraph("Available Downloads", heading_style))
                
                assets = json_data["downloadable_assets"]
                asset_list = []
                
                if assets.get("html_report"):
                    asset_list.append(["HTML Report", assets["html_report"]])
                if assets.get("pdf_report"):
                    asset_list.append(["PDF Report", assets["pdf_report"]])
                if assets.get("json_report"):
                    asset_list.append(["JSON Report", assets["json_report"]])
                if assets.get("json_pdf_report"):
                    asset_list.append(["JSON PDF Report", assets["json_pdf_report"]])
                if assets.get("analysis_report"):
                    asset_list.append(["Analysis Report", assets["analysis_report"]])
                if assets.get("single_screenshot"):
                    asset_list.append(["Final Screenshot", assets["single_screenshot"]])
                
                if asset_list:
                    asset_table = Table(asset_list, colWidths=[1.5*inch, 4*inch])
                    asset_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ]))
                    story.append(asset_table)
            
            # Build PDF
            doc.build(story)
            
            print(f"[ReportEnhancer] JSON PDF report saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate JSON PDF report: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def embed_screenshot_in_pdf(self, pdf_path: str, screenshot_path: str, position: str = "end") -> str:
        """
        Embed screenshot into existing PDF
        
        Args:
            pdf_path: Path to existing PDF
            screenshot_path: Path to screenshot image
            position: Where to add screenshot ("end" or "beginning")
        
        Returns:
            Path to new PDF with embedded screenshot
        """
        try:
            if not os.path.exists(screenshot_path):
                print(f"[WARNING] Screenshot not found: {screenshot_path}")
                return pdf_path
            
            # Create new PDF with screenshot
            from reportlab.lib.utils import ImageReader
            
            new_pdf_path = pdf_path.replace(".pdf", "_with_screenshot.pdf")
            
            doc = SimpleDocTemplate(
                new_pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Add screenshot
            story.append(Paragraph("Result Page Screenshot", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            try:
                # Add image with caption
                img = Image(screenshot_path, width=5*inch, height=3*inch)
                story.append(img)
                story.append(Paragraph(f"Screenshot captured from final result page", styles['Italic']))
                story.append(Paragraph(f"File: {os.path.basename(screenshot_path)}", styles['Italic']))
                story.append(Spacer(1, 20))
            except Exception as e:
                story.append(Paragraph(f"[Could not embed screenshot: {str(e)}]", styles['Italic']))
            
            # Add note about downloads
            story.append(Paragraph("Available Downloads:", styles['Heading3']))
            story.append(Paragraph("• HTML Report - Complete interactive report", styles['Normal']))
            story.append(Paragraph("• PDF Report - Printable version", styles['Normal']))
            story.append(Paragraph("• JSON Report - Structured data format", styles['Normal']))
            story.append(Paragraph("• Analysis Report - Human-readable analysis", styles['Normal']))
            story.append(Paragraph("• Screenshot Image - Just the final screenshot", styles['Normal']))
            
            doc.build(story)
            
            print(f"[ReportEnhancer] Screenshot embedded in PDF: {new_pdf_path}")
            return new_pdf_path
            
        except Exception as e:
            print(f"[ERROR] Failed to embed screenshot in PDF: {e}")
            return pdf_path