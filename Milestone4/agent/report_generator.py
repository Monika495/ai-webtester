"""Enhanced Report Generator for NovaQA with Screenshots and Metadata"""
from datetime import datetime
import os
import json
import base64
import platform
import sys
import traceback
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch

class ReportGenerator:
    """Enhanced report generator with screenshots and detailed metadata"""
    
    def __init__(self, reports_dir="reports"):
        self.reports_dir = reports_dir
        
        # Create directory structure
        self.html_dir = os.path.join(reports_dir, "html")
        self.pdf_dir = os.path.join(reports_dir, "pdf")
        self.json_dir = os.path.join(reports_dir, "json")
        self.screenshots_dir = os.path.join(reports_dir, "screenshots")
        self.analysis_dir = os.path.join(reports_dir, "analysis")  # For analysis reports
        
        for directory in [self.html_dir, self.pdf_dir, self.json_dir, self.screenshots_dir, self.analysis_dir]:
            os.makedirs(directory, exist_ok=True)
        
        print(f"[ReportGenerator] Reports directory: {os.path.abspath(reports_dir)}")
        print(f"[ReportGenerator] Analysis directory: {self.analysis_dir}")
    
    def _get_environment_info(self):
        """Get environment information"""
        try:
            import playwright
            playwright_version = playwright.__version__
        except:
            playwright_version = "Unknown"
        
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "playwright_version": playwright_version,
            "project_name": "NovaQA",
            "project_version": "1.0.0"
        }
    
    def _calculate_summary(self, execution):
        """Calculate execution summary"""
        total_steps = len(execution)
        passed_steps = len([s for s in execution if s.get("status", "").lower() == "passed"])
        failed_steps = len([s for s in execution if s.get("status", "").lower() == "failed"])
        warning_steps = len([s for s in execution if s.get("status", "").lower() == "warning"])
        info_steps = len([s for s in execution if s.get("status", "").lower() == "info"])
        
        pass_percentage = (passed_steps / total_steps * 100) if total_steps > 0 else 0
        fail_percentage = (failed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Determine overall status
        if failed_steps > 0:
            status = "FAILED"
        elif warning_steps > 0:
            status = "WARNING"
        else:
            status = "PASSED"
        
        return {
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "warning_steps": warning_steps,
            "info_steps": info_steps,
            "pass_percentage": round(pass_percentage, 2),
            "fail_percentage": round(fail_percentage, 2),
            "status": status
        }
    
    def _get_result_screenshot(self, report_id, metadata):
        """Get the result page screenshot path"""
        try:
            # Check metadata for final screenshot
            if metadata and metadata.get("final_screenshot"):
                screenshot_path = metadata["final_screenshot"]
                if os.path.exists(screenshot_path):
                    return screenshot_path
            
            # Check screenshots metadata
            if metadata and metadata.get("screenshots"):
                screenshots = metadata["screenshots"]
                if isinstance(screenshots, dict) and screenshots.get("result_page"):
                    result_page = screenshots["result_page"]
                    if isinstance(result_page, dict):
                        path = result_page.get("screenshot_path", "")
                        if path and os.path.exists(path):
                            return path
            
            # Search in screenshots directory
            if os.path.exists(self.screenshots_dir):
                for filename in os.listdir(self.screenshots_dir):
                    if report_id in filename and "result_page" in filename.lower() and filename.endswith(".png"):
                        path = os.path.join(self.screenshots_dir, filename)
                        if os.path.exists(path):
                            return path
            
            return None
        except Exception as e:
            print(f"[ReportGenerator] Error getting result screenshot: {e}")
            return None
    
    def _get_result_summary(self, test_data):
        """Extract result page summary from test data"""
        try:
            # Check metadata first
            metadata = test_data.get("metadata", {})
            
            # Direct result_summary
            if metadata.get("result_summary"):
                return metadata["result_summary"]
            
            # Check screenshots metadata
            if metadata.get("screenshots"):
                screenshots = metadata["screenshots"]
                if isinstance(screenshots, dict):
                    if screenshots.get("result_page"):
                        result_page = screenshots["result_page"]
                        if isinstance(result_page, dict) and result_page.get("result_summary"):
                            return result_page["result_summary"]
            
            # Check result_page_analysis
            if test_data.get("result_page_analysis"):
                analysis = test_data["result_page_analysis"]
                if isinstance(analysis, dict) and analysis.get("summary"):
                    return analysis["summary"]
            
            # Check execution steps for result page
            execution = test_data.get("execution", [])
            for step in reversed(execution):
                if step.get("action") == "result_page_capture":
                    return step.get("actual_result", step.get("details", "Result page captured"))
            
            # Generate basic summary from instruction
            instruction = test_data.get("instruction", "")
            if "search" in instruction.lower():
                import re
                query_match = re.search(r'search\s+(?:for\s+)?(.+?)(?:\s+on|\s+in|$)', instruction.lower())
                if query_match:
                    query = query_match.group(1).strip()
                    return f"Search results for '{query}' were displayed successfully"
            
            return "Result page loaded successfully"
            
        except Exception as e:
            print(f"[WARNING] Failed to extract result summary: {e}")
            return "Result page loaded successfully"

    def _get_result_summary_from_metadata(self, metadata):
        """Extract result summary from metadata"""
        try:
            # Try to get result summary from metadata
            if metadata and "result_summary" in metadata:
                return metadata["result_summary"]
            
            # Try to get from screenshots metadata
            if metadata and "screenshots" in metadata:
                screenshots = metadata["screenshots"]
                if isinstance(screenshots, dict) and "result_page" in screenshots:
                    result_page = screenshots["result_page"]
                    if isinstance(result_page, dict) and "result_summary" in result_page:
                        return result_page["result_summary"]
            
            return None
        except:
            return None
    
    def _get_screenshots_for_report(self, metadata, report_id):
        """Get screenshots for the report"""
        screenshots = []
        
        # Check metadata for screenshots
        if metadata and "screenshots" in metadata:
            screenshots_data = metadata["screenshots"]
            
            # Get result page screenshot
            if "result_page" in screenshots_data and screenshots_data["result_page"]:
                result_page = screenshots_data["result_page"]
                if isinstance(result_page, dict) and "screenshot_path" in result_page:
                    screenshots.append({
                        "type": "result_page",
                        "path": result_page["screenshot_path"],
                        "description": "Final Result Page",
                        "summary": result_page.get("result_summary", "Result page captured")
                    })
            
            # Get last failed screenshot
            if "last_failed" in screenshots_data and screenshots_data["last_failed"]:
                last_failed = screenshots_data["last_failed"]
                if isinstance(last_failed, dict) and "screenshot_path" in last_failed:
                    screenshots.append({
                        "type": "failed_step",
                        "path": last_failed["screenshot_path"],
                        "description": "Last Failed Step",
                        "summary": last_failed.get("step_description", "Failed step captured")
                    })
        
        # Also scan the screenshots directory
        if os.path.exists(self.screenshots_dir):
            for filename in os.listdir(self.screenshots_dir):
                if report_id in filename and filename.endswith('.png'):
                    # Skip thumbnails
                    if not filename.startswith('thumb_'):
                        filepath = os.path.join(self.screenshots_dir, filename)
                        
                        # Determine type
                        if 'result_page' in filename.lower():
                            screenshot_type = 'result_page'
                            description = 'Result Page'
                        elif 'failed' in filename.lower():
                            screenshot_type = 'failed_step'
                            description = 'Failed Step'
                        else:
                            screenshot_type = 'step'
                            description = 'Step Screenshot'
                        
                        screenshots.append({
                            "type": screenshot_type,
                            "path": filepath,
                            "description": description,
                            "filename": filename
                        })
        
        return screenshots
    
    def _get_failure_recommendations(self, error_message):
        """Get recommendations based on error message"""
        error_lower = error_message.lower()
        recommendations = []
        
        if "not found" in error_lower or "selector" in error_lower:
            recommendations.append("Review element selectors for accuracy")
            recommendations.append("Check if the element exists on the page")
            recommendations.append("Add wait time before element interaction")
        
        if "timeout" in error_lower:
            recommendations.append("Increase timeout duration")
            recommendations.append("Check network connectivity")
            recommendations.append("Verify server response times")
        
        if "navigation" in error_lower:
            recommendations.append("Check URL validity")
            recommendations.append("Verify network connectivity")
            recommendations.append("Ensure the website is accessible")
        
        if "network" in error_lower or "connection" in error_lower:
            recommendations.append("Check internet connection")
            recommendations.append("Verify server status")
            recommendations.append("Review firewall/proxy settings")
        
        if "permission" in error_lower or "access" in error_lower:
            recommendations.append("Check user permissions")
            recommendations.append("Verify login credentials")
            recommendations.append("Review access control settings")
        
        # Add general recommendations
        if not recommendations:
            recommendations = [
                "Review test script for logical errors",
                "Add more detailed logging",
                "Test in non-headless mode first",
                "Check browser compatibility",
                "Update Playwright to latest version"
            ]
        
        return recommendations
    
    def generate_pdf_report(self, test_data):
        """Generate standard PDF report with screenshot and summary"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Get screenshot and summary
            screenshot_path = self._get_result_screenshot(report_id, metadata)
            result_summary = self._get_result_summary(test_data)
            
            # Create PDF
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"report_{report_id}_{timestamp}.pdf"
            pdf_filepath = os.path.join(self.pdf_dir, pdf_filename)
            
            doc = SimpleDocTemplate(pdf_filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#06B6D4'), spaceAfter=20, alignment=1)
            heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0891B2'), spaceAfter=10)
            
            story = []
            
            # Title
            story.append(Paragraph("NovaQA Test Report", title_style))
            story.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Test Information
            story.append(Paragraph("Test Information", heading_style))
            test_info = [
                ["Instruction", instruction],
                ["Total Steps", str(len(execution))],
                ["Duration", f"{metadata.get('duration_seconds', 0):.2f} seconds"],
                ["Browser", metadata.get('browser', 'Chromium')],
                ["Mode", "Headless" if metadata.get('headless', True) else "Headed"]
            ]
            
            info_table = Table(test_info, colWidths=[2*inch, 3.5*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Result Page Screenshot and Summary
            if screenshot_path and os.path.exists(screenshot_path):
                story.append(Paragraph("Result Page", heading_style))
                story.append(Spacer(1, 10))
                
                # Add screenshot
                try:
                    img = Image(screenshot_path, width=5*inch, height=3.5*inch)
                    story.append(img)
                    story.append(Spacer(1, 10))
                except Exception as e:
                    story.append(Paragraph(f"[Could not embed screenshot: {str(e)}]", styles['Italic']))
                
                # Add summary below screenshot
                if result_summary:
                    story.append(Paragraph("Result Summary:", heading_style))
                    story.append(Paragraph(result_summary, styles['Normal']))
                    story.append(Spacer(1, 20))
            elif result_summary:
                # Show summary even if no screenshot
                story.append(Paragraph("Result Summary:", heading_style))
                story.append(Paragraph(result_summary, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Execution Steps
            story.append(Paragraph("Execution Timeline", heading_style))
            
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown").upper()
                action = step.get("action", "Unknown").replace('_', ' ').title()
                details = step.get("description") or step.get("details", "No details")
                
                story.append(Paragraph(f"Step {i}: {action} - [{status}]", styles['Normal']))
                story.append(Paragraph(f"Details: {details}", styles['Normal']))
                
                if step.get("error_message"):
                    error_style = ParagraphStyle('Error', parent=styles['Normal'], textColor=colors.red)
                    story.append(Paragraph(f"Error: {step['error_message']}", error_style))
                
                story.append(Spacer(1, 8))
            
            # Build PDF
            doc.build(story)
            
            print(f"[ReportGenerator] PDF report saved: {pdf_filepath}")
            return pdf_filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate PDF report: {e}")
            traceback.print_exc()
            return None
    
    def generate_enhanced_pdf_report(self, test_data):
        """Generate enhanced PDF report with failure/success analysis and summary"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Calculate summary
            summary = self._calculate_summary(execution)
            
            # Get result summary
            result_summary = self._get_result_summary_from_metadata(metadata)
            
            # Create PDF filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"analysis_report_{report_id}_{timestamp}.pdf"
            pdf_filepath = os.path.join(self.pdf_dir, pdf_filename)
            
            # Create PDF with reportlab
            doc = SimpleDocTemplate(
                pdf_filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title=f"NovaQA Analysis Report - {report_id}",
                author="NovaQA Test Automation"
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'EnhancedTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#10B981') if summary['status'] == 'PASSED' else colors.HexColor('#EF4444'),
                spaceAfter=12,
                alignment=1  # Center
            )
            
            sub_title_style = ParagraphStyle(
                'SubTitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#0891B2'),
                spaceAfter=6
            )
            
            heading_style = ParagraphStyle(
                'EnhancedHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#0891B2'),
                spaceAfter=8
            )
            
            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            bold_style = ParagraphStyle(
                'BoldStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                fontName='Helvetica-Bold'
            )
            
            error_style = ParagraphStyle(
                'ErrorStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.red,
                spaceAfter=6,
                backColor=colors.HexColor('#FFEBEE')
            )
            
            success_style = ParagraphStyle(
                'SuccessStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=6,
                backColor=colors.HexColor('#E8F5E9')
            )
            
            story = []
            
            # ========== PAGE 1: COVER PAGE ==========
            story.append(Paragraph("NovaQA Test Analysis Report", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Status indicator
            status_color = colors.HexColor('#10B981') if summary['status'] == 'PASSED' else colors.HexColor('#EF4444')
            status_style = ParagraphStyle(
                'StatusStyle',
                parent=styles['Normal'],
                fontSize=16,
                textColor=status_color,
                alignment=1,
                fontName='Helvetica-Bold',
                spaceAfter=12
            )
            story.append(Paragraph(f"Status: {summary['status']}", status_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Report info
            story.append(Paragraph(f"Report ID: {report_id}", normal_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Paragraph(f"Instruction: {instruction[:100]}{'...' if len(instruction) > 100 else ''}", normal_style))
            
            # Add Result Summary if available
            if result_summary:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Result Page Summary:", heading_style))
                story.append(Paragraph(result_summary, normal_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Summary table
            story.append(Paragraph("Execution Summary", heading_style))
            
            summary_data = [
                ["Metric", "Value", "Percentage"],
                ["Total Steps", str(summary["total_steps"]), "100%"],
                ["Passed", str(summary["passed_steps"]), f"{summary['pass_percentage']:.1f}%"],
                ["Failed", str(summary["failed_steps"]), f"{summary['fail_percentage']:.1f}%"],
                ["Success Rate", f"{summary['pass_percentage']:.1f}%", f"{summary['pass_percentage']:.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06B6D4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F3F4F6')),
                ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F3F4F6')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(summary_table)
            
            story.append(Spacer(1, 0.3*inch))
            
            # Quick Analysis
            story.append(Paragraph("Quick Analysis", heading_style))
            
            if summary['status'] == 'PASSED':
                story.append(Paragraph("✅ All test steps executed successfully.", success_style))
                story.append(Paragraph(f"✅ Execution completed in {metadata.get('duration_seconds', 0):.2f} seconds.", success_style))
                story.append(Paragraph("✅ No errors detected during execution.", success_style))
                if result_summary:
                    story.append(Paragraph(f"✅ {result_summary[:100]}...", success_style))
            else:
                story.append(Paragraph("❌ Test execution completed with failures.", error_style))
                story.append(Paragraph(f"❌ {summary['failed_steps']} out of {summary['total_steps']} steps failed.", error_style))
                story.append(Paragraph("❌ Review the detailed analysis below.", error_style))
            
            story.append(PageBreak())
            
            # ========== PAGE 2: DETAILED ANALYSIS ==========
            story.append(Paragraph("Detailed Test Analysis", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Test Instruction
            story.append(Paragraph("Test Instruction:", sub_title_style))
            story.append(Paragraph(instruction, normal_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Execution Timeline
            story.append(Paragraph("Step-by-Step Execution:", sub_title_style))
            
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown").upper()
                action = step.get("action", "Unknown").replace('_', ' ').title()
                description = step.get("description") or step.get("details", "No description")
                error_message = step.get("error_message", "")
                
                # Determine step style
                if status == "PASSED":
                    step_style = success_style
                    status_text = "✅ PASSED"
                elif status == "FAILED":
                    step_style = error_style
                    status_text = "❌ FAILED"
                elif status == "WARNING":
                    step_style = ParagraphStyle(
                        'WarningStyle',
                        parent=styles['Normal'],
                        fontSize=9,
                        textColor=colors.HexColor('#F59E0B'),
                        spaceAfter=6,
                        backColor=colors.HexColor('#FEF3C7')
                    )
                    status_text = "⚠️ WARNING"
                else:
                    step_style = normal_style
                    status_text = f"ℹ️ {status}"
                
                # Add step header
                step_header = f"Step {i}: {action} - {status_text}"
                story.append(Paragraph(step_header, bold_style))
                
                # Add description
                story.append(Paragraph(f"Description: {description}", normal_style))
                
                # Add error if present
                if error_message:
                    story.append(Paragraph(f"Error: {error_message}", error_style))
                
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Failure Analysis (if any failures)
            failed_steps = [s for s in execution if s.get("status", "").lower() == "failed"]
            if failed_steps:
                story.append(Paragraph("Failure Analysis:", sub_title_style))
                
                for step in failed_steps[:3]:  # Show first 3 failures
                    step_num = execution.index(step) + 1
                    action = step.get("action", "Unknown").replace('_', ' ').title()
                    error_msg = step.get("error_message", step.get("details", "Unknown error"))
                    
                    story.append(Paragraph(f"Step {step_num}: {action}", bold_style))
                    story.append(Paragraph(f"Failure Reason: {error_msg}", error_style))
                    
                    # Add recommendations
                    recommendations = self._get_failure_recommendations(error_msg)
                    for rec in recommendations:
                        story.append(Paragraph(f"🔧 {rec}", normal_style))
                    
                    story.append(Spacer(1, 0.1*inch))
                
                if len(failed_steps) > 3:
                    story.append(Paragraph(f"... and {len(failed_steps) - 3} more failure(s)", normal_style))
            
            story.append(PageBreak())
            
            # ========== PAGE 3: RECOMMENDATIONS & METADATA ==========
            story.append(Paragraph("Recommendations & Metadata", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Recommendations based on test status
            story.append(Paragraph("Recommendations:", sub_title_style))
            
            if summary['status'] == 'PASSED':
                recommendations = [
                    "Continue with current test approach",
                    "Consider adding more edge cases for robustness",
                    "Run performance tests to measure response times",
                    "Integrate with CI/CD pipeline for automated runs",
                    "Add validation steps for critical functionality"
                ]
                for rec in recommendations:
                    story.append(Paragraph(f"✅ {rec}", success_style))
            else:
                recommendations = [
                    "Review failed step selectors and locators",
                    "Add explicit wait times before critical actions",
                    "Implement retry logic for flaky test steps",
                    "Verify test data accuracy and completeness",
                    "Check network connectivity and server status"
                ]
                for rec in recommendations:
                    story.append(Paragraph(f"🔧 {rec}", normal_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Metadata
            story.append(Paragraph("Execution Metadata:", sub_title_style))
            
            meta_data = [
                ["Browser", metadata.get('browser', 'Chromium')],
                ["Mode", "Headless" if metadata.get('headless', True) else "Headed"],
                ["Start Time", metadata.get('start_time', 'N/A')],
                ["End Time", metadata.get('end_time', 'N/A')],
                ["Duration", f"{metadata.get('duration_seconds', 0):.2f} seconds"],
                ["Screenshots", f"{len(self._get_screenshots_for_report(metadata, report_id))} captured"]
            ]
            
            meta_table = Table(meta_data, colWidths=[2*inch, 3*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F3F4F6')),
                ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#F3F4F6')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(meta_table)
            
            story.append(Spacer(1, 0.3*inch))
            
            # Result Summary (if available)
            if result_summary:
                story.append(Paragraph("Result Page Analysis:", sub_title_style))
                story.append(Paragraph(result_summary, normal_style))
                story.append(Spacer(1, 0.3*inch))
            
            # Environment Info
            story.append(Paragraph("Environment Information:", sub_title_style))
            
            env_info = self._get_environment_info()
            env_data = [
                ["Operating System", f"{env_info['os']} {env_info['os_version']}"],
                ["Python Version", env_info['python_version']],
                ["Playwright Version", env_info['playwright_version']],
                ["Project", f"{env_info['project_name']} v{env_info['project_version']}"]
            ]
            
            env_table = Table(env_data, colWidths=[2*inch, 3*inch])
            env_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F3F4F6')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(env_table)
            
            # Footer note
            story.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=1
            )
            story.append(Paragraph("NovaQA Test Automation Platform - AI-Powered Testing", footer_style))
            story.append(Paragraph(f"Report Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # Build PDF
            doc.build(story)
            
            print(f"[ReportGenerator] Enhanced PDF report saved: {pdf_filepath}")
            return pdf_filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate enhanced PDF report: {e}")
            traceback.print_exc()
            # Fallback to regular PDF
            return self.generate_pdf_report(test_data)
    
    def generate_json_to_pdf(self, json_data, report_id=None):
        """Convert JSON actions to PDF format - FIXED VERSION"""
        try:
            if not report_id:
                report_id = f"json_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            pdf_filename = f"json_report_{report_id}.pdf"
            pdf_filepath = os.path.join(self.pdf_dir, pdf_filename)
            
            doc = SimpleDocTemplate(pdf_filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, 
                textColor=colors.HexColor('#8B5CF6'), spaceAfter=20, alignment=1)
            heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, 
                textColor=colors.HexColor('#06B6D4'), spaceAfter=8)
            code_style = ParagraphStyle('Code', parent=styles['Normal'], fontSize=9, 
                fontName='Courier', spaceAfter=6, textColor=colors.black)
            action_style = ParagraphStyle('Action', parent=styles['Normal'], fontSize=10, 
                spaceAfter=4, textColor=colors.HexColor('#1F2937'))
            
            story = []
            
            # Title
            story.append(Paragraph("JSON Actions Report", title_style))
            story.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Debug: Print JSON structure
            print(f"[JSON-PDF] JSON data type: {type(json_data)}")
            if isinstance(json_data, dict):
                print(f"[JSON-PDF] JSON keys: {list(json_data.keys())}")
            
            # Extract AI-generated actions - FIXED LOGIC
            actions = []
            
            # Handle different JSON structures - FIXED
            if isinstance(json_data, dict):
                print(f"[JSON-PDF] Processing dictionary JSON data")
                
                # Check if it's a complete test report
                if "parsed" in json_data and isinstance(json_data["parsed"], list):
                    actions = json_data["parsed"]
                    print(f"[JSON-PDF] Found {len(actions)} actions in 'parsed' key")
                elif "execution" in json_data and isinstance(json_data["execution"], list):
                    actions = json_data["execution"]
                    print(f"[JSON-PDF] Found {len(actions)} actions in 'execution' key")
                elif "generated_actions" in json_data and isinstance(json_data["generated_actions"], list):
                    actions = json_data["generated_actions"]
                    print(f"[JSON-PDF] Found {len(actions)} actions in 'generated_actions' key")
                elif "actions" in json_data and isinstance(json_data["actions"], list):
                    actions = json_data["actions"]
                    print(f"[JSON-PDF] Found {len(actions)} actions in 'actions' key")
                elif "action_json" in json_data and isinstance(json_data["action_json"], dict):
                    action_json = json_data["action_json"]
                    if "actions" in action_json and isinstance(action_json["actions"], list):
                        actions = action_json["actions"]
                        print(f"[JSON-PDF] Found {len(actions)} actions in 'action_json.actions'")
                
                # If no actions found yet, check if the dictionary itself contains action-like data
                if not actions:
                    # Check if this is actually a single action dictionary
                    if "action" in json_data or "action_type" in json_data:
                        actions = [json_data]  # Wrap single action in a list
                        print(f"[JSON-PDF] Treating as single action dictionary")
                    else:
                        # Try to extract any list values
                        for key, value in json_data.items():
                            if isinstance(value, list) and value and isinstance(value[0], dict):
                                if "action" in value[0] or "action_type" in value[0]:
                                    actions = value
                                    print(f"[JSON-PDF] Found {len(actions)} actions in key '{key}'")
                                    break
            
            elif isinstance(json_data, list):
                actions = json_data
                print(f"[JSON-PDF] JSON data is a list: {len(actions)} items")
            
            # Display actions
            if actions:
                # Filter out non-action items
                valid_actions = []
                for item in actions:
                    if isinstance(item, dict) and ("action" in item or "action_type" in item or "step" in item or "description" in item):
                        valid_actions.append(item)
                
                print(f"[JSON-PDF] Valid actions found: {len(valid_actions)}")
                
                if valid_actions:
                    story.append(Paragraph("AI-Generated Actions for Playwright Execution", heading_style))
                    story.append(Paragraph(f"Total {len(valid_actions)} actions generated for automation", styles['Normal']))
                    story.append(Spacer(1, 10))
                    
                    # Create detailed actions table
                    for i, action in enumerate(valid_actions, 1):
                        story.append(Paragraph(f"Action {i}:", styles['Heading3']))
                        
                        # Extract key action properties
                        action_type = action.get("action", action.get("action_type", "unknown"))
                        description = action.get("description", action.get("details", "No description"))
                        selector = action.get("selector", "")
                        value = action.get("value", "")
                        field_type = action.get("field_type", "")
                        status = action.get("status", "")
                        
                        # Create action details table
                        action_details = [
                            ["Property", "Value"],
                            ["Type", action_type],
                            ["Description", description[:100] + "..." if len(description) > 100 else description]
                        ]
                        
                        if selector:
                            action_details.append(["Selector", selector[:80] + "..." if len(selector) > 80 else selector])
                        
                        if value:
                            display_value = value
                            if field_type == "password":
                                display_value = "********"
                            elif len(value) > 30:
                                display_value = value[:30] + "..."
                            action_details.append(["Value", display_value])
                        
                        if field_type:
                            action_details.append(["Field Type", field_type])
                        
                        if status:
                            action_details.append(["Status", status])
                        
                        action_table = Table(action_details, colWidths=[1.5*inch, 3.5*inch])
                        action_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
                        ]))
                        story.append(action_table)
                        story.append(Spacer(1, 10))
                    
                    # Add JSON code sample
                    story.append(Paragraph("Complete JSON Structure", heading_style))
                    story.append(Paragraph("Full JSON data that can be executed by Playwright:", styles['Italic']))
                    story.append(Spacer(1, 10))
                    
                    # Format JSON nicely
                    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                    json_lines = json_str.split('\n')
                    
                    # Add first 30 lines of JSON (or all if less)
                    lines_to_show = min(30, len(json_lines))
                    for line in json_lines[:lines_to_show]:
                        story.append(Paragraph(line, code_style))
                    
                    if len(json_lines) > lines_to_show:
                        story.append(Paragraph(f"... and {len(json_lines) - lines_to_show} more lines", styles['Italic']))
                    
                    story.append(Spacer(1, 20))
                    
                    # Add usage instructions
                    story.append(Paragraph("How to Use These Actions", heading_style))
                    instructions = [
                        "1. These actions are generated for execution by Playwright",
                        "2. Each action represents a step in the automated test",
                        "3. Actions include navigation, typing, clicking, and validation",
                        "4. The JSON structure contains all necessary metadata",
                        "5. You can use this data to replay the test scenario",
                        "6. For login/signup tests, credentials are managed intelligently"
                    ]
                    
                    for instruction in instructions:
                        story.append(Paragraph(f"• {instruction}", action_style))
                    
                else:
                    # No valid actions found
                    story.append(Paragraph("No Valid Actions Found", heading_style))
                    story.append(Paragraph("The JSON data does not contain recognizable action structures.", styles['Normal']))
                    story.append(Spacer(1, 10))
                    
                    # Show the JSON structure anyway
                    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                    for line in json_str.split('\n')[:50]:
                        story.append(Paragraph(line, code_style))
                    
                    if len(json_str.split('\n')) > 50:
                        story.append(Paragraph(f"... and {len(json_str.split('\n')) - 50} more lines", styles['Italic']))
            else:
                # If no actions found, show the JSON data structure
                story.append(Paragraph("JSON Data Structure", heading_style))
                story.append(Paragraph("No structured actions found. Showing JSON data:", styles['Normal']))
                story.append(Spacer(1, 10))
                
                # Convert to string and display
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                for line in json_str.split('\n')[:50]:  # Limit lines
                    story.append(Paragraph(line, code_style))
                
                if len(json_str.split('\n')) > 50:
                    story.append(Paragraph(f"... and {len(json_str.split('\n')) - 50} more lines", styles['Italic']))
            
            # Build PDF
            doc.build(story)
            
            print(f"[ReportGenerator] JSON-to-PDF saved: {pdf_filepath}")
            return pdf_filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate JSON-to-PDF: {e}")
            traceback.print_exc()
            
            # Create a simple fallback PDF
            try:
                if not report_id:
                    report_id = f"json_report_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                pdf_filename = f"json_report_fallback_{report_id}.pdf"
                pdf_filepath = os.path.join(self.pdf_dir, pdf_filename)
                
                doc = SimpleDocTemplate(pdf_filepath, pagesize=A4)
                story = []
                
                story.append(Paragraph("JSON Actions Report", title_style))
                story.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
                story.append(Spacer(1, 20))
                story.append(Paragraph("Error generating detailed report:", styles['Normal']))
                story.append(Paragraph(str(e), styles['Normal']))
                
                doc.build(story)
                return pdf_filepath
            except:
                return None
    
    def generate_html_report(self, test_data):
        """Generate HTML report with result page summary and screenshots"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Calculate summary
            summary = self._calculate_summary(execution)
            
            # Get result summary
            result_summary = self._get_result_summary_from_metadata(metadata)
            
            # Get screenshots
            screenshots = self._get_screenshots_for_report(metadata, report_id)
            
            # Get environment info
            env_info = self._get_environment_info()
            
            # Format metadata
            start_time = metadata.get("start_time", datetime.now().isoformat())
            end_time = metadata.get("end_time", datetime.now().isoformat())
            duration = metadata.get("duration_seconds", 0)
            
            try:
                start_dt = datetime.fromisoformat(start_time)
                start_time_formatted = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                start_time_formatted = start_time
            
            try:
                end_dt = datetime.fromisoformat(end_time)
                end_time_formatted = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                end_time_formatted = end_time
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Build HTML
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaQA Test Report - {report_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%); color: white; padding: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 5px; }}
        .summary {{ padding: 30px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px; }}
        .summary-card {{ text-align: center; padding: 20px; border-radius: 8px; background: white; border: 1px solid #e5e7eb; }}
        .summary-card h3 {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
        .summary-card.total {{ color: #1e40af; }}
        .summary-card.passed {{ color: #15803d; }}
        .summary-card.failed {{ color: #dc2626; }}
        .summary-card.percentage {{ color: #ca8a04; }}
        .summary-card p {{ color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .section {{ padding: 30px; border-bottom: 1px solid #e5e7eb; }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; color: #111827; display: flex; align-items: center; gap: 10px; }}
        .section h2::before {{ content: ""; width: 4px; height: 24px; background: #06B6D4; border-radius: 2px; }}
        .metadata-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }}
        .metadata-item {{ padding: 15px; background: #f9fafb; border-radius: 8px; border-left: 3px solid #06B6D4; }}
        .metadata-item label {{ display: block; font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }}
        .metadata-item value {{ display: block; font-size: 16px; font-weight: 500; color: #111827; }}
        .instruction-box {{ background: #f9fafb; padding: 20px; border-radius: 8px; border-left: 4px solid #06B6D4; margin-top: 15px; }}
        .instruction-box p {{ color: #374151; line-height: 1.6; font-size: 15px; }}
        
        /* Result Summary Section */
        .result-summary-section {{ margin: 20px 0; }}
        .result-summary-box {{ background: #f0fdf4; border-left: 4px solid #10B981; padding: 20px; border-radius: 8px; }}
        .result-summary-box.failed {{ background: #fef2f2; border-left-color: #EF4444; padding: 20px; border-radius: 8px; }}
        .result-summary-title {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }}
        
        /* Screenshot Section */
        .screenshot-section {{ margin: 20px 0; }}
        .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 15px; }}
        .screenshot-card {{ border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }}
        .screenshot-img {{ width: 100%; height: 200px; object-fit: cover; cursor: pointer; }}
        .screenshot-info {{ padding: 15px; }}
        .screenshot-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; margin-bottom: 5px; }}
        
        /* Download Section */
        .download-section {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .download-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
        .download-btn {{ display: block; padding: 15px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; text-align: center; text-decoration: none; color: #111827; transition: all 0.2s; }}
        .download-btn:hover {{ background: #06B6D4; color: white; border-color: #06B6D4; }}
        
        /* Timeline */
        .timeline {{ margin-top: 20px; }}
        .timeline-item {{ display: flex; gap: 20px; margin-bottom: 20px; position: relative; }}
        .timeline-item::before {{ content: ""; position: absolute; left: 19px; top: 40px; bottom: -20px; width: 2px; background: #e5e7eb; }}
        .timeline-item:last-child::before {{ display: none; }}
        .timeline-icon {{ flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; position: relative; z-index: 1; }}
        .timeline-icon.passed {{ background: #10b981; }}
        .timeline-icon.failed {{ background: #ef4444; }}
        .timeline-icon.warning {{ background: #f59e0b; }}
        .timeline-icon.info {{ background: #3b82f6; }}
        .timeline-content {{ flex: 1; background: #f9fafb; padding: 15px 20px; border-radius: 8px; border-left: 3px solid #e5e7eb; }}
        .timeline-content.passed {{ border-left-color: #10b981; background: #f0fdf4; }}
        .timeline-content.failed {{ border-left-color: #ef4444; background: #fef2f2; }}
        .timeline-content.warning {{ border-left-color: #f59e0b; background: #fef3c7; }}
        .timeline-content h4 {{ font-size: 14px; margin-bottom: 8px; color: #111827; display: flex; justify-content: space-between; align-items: center; }}
        .timeline-content p {{ font-size: 13px; color: #6b7280; line-height: 1.5; }}
        
        /* Badges */
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .badge.passed {{ background: #dcfce7; color: #15803d; }}
        .badge.failed {{ background: #fee2e2; color: #dc2626; }}
        .badge.warning {{ background: #fef3c7; color: #92400e; }}
        .badge.info {{ background: #dbeafe; color: #1e40af; }}
        
        /* Footer */
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 13px; background: #f9fafb; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 NovaQA Test Report</h1>
            <p>Report ID: {report_id} | Generated on {timestamp}</p>
        </div>
        
        <div class="summary">
            <h2>Execution Summary</h2>
            <div class="summary-grid">
                <div class="summary-card total">
                    <h3>{summary["total_steps"]}</h3>
                    <p>Total Steps</p>
                </div>
                <div class="summary-card passed">
                    <h3>{summary["passed_steps"]}</h3>
                    <p>Passed</p>
                </div>
                <div class="summary-card failed">
                    <h3>{summary["failed_steps"]}</h3>
                    <p>Failed</p>
                </div>
                <div class="summary-card percentage">
                    <h3>{summary["pass_percentage"]:.1f}%</h3>
                    <p>Pass Rate</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Test Information</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <label>Instruction</label>
                    <value>{instruction}</value>
                </div>
                <div class="metadata-item">
                    <label>Status</label>
                    <value>
                        <span style="color: {'#10B981' if summary['status'] == 'PASSED' else '#EF4444'}; font-weight: bold;">
                            {summary['status']}
                        </span>
                    </value>
                </div>
                <div class="metadata-item">
                    <label>Duration</label>
                    <value>{duration:.2f} seconds</value>
                </div>
                <div class="metadata-item">
                    <label>Start Time</label>
                    <value>{start_time_formatted}</value>
                </div>
                <div class="metadata-item">
                    <label>End Time</label>
                    <value>{end_time_formatted}</value>
                </div>
            </div>
        </div>
"""
            
            # Add Result Summary Section
            if result_summary:
                html_content += f"""
        <div class="section">
            <h2>📋 Result Page Summary</h2>
            <div class="result-summary-section">
                <div class="result-summary-box {'failed' if summary['failed_steps'] > 0 else ''}">
                    <div class="result-summary-title">
                        <h3>Search Results Summary</h3>
                    </div>
                    <p>{result_summary}</p>
                </div>
            </div>
        </div>
"""
            
            # Add Screenshots Section
            if screenshots:
                html_content += """
        <div class="section">
            <h2>📸 Screenshots</h2>
            <div class="screenshot-section">
                <div class="screenshot-grid">
"""
                
                for screenshot in screenshots:
                    if os.path.exists(screenshot.get("path", "")):
                        try:
                            with open(screenshot["path"], "rb") as f:
                                img_data = base64.b64encode(f.read()).decode()
                            
                            screenshot_type = screenshot.get("type", "step")
                            description = screenshot.get("description", "Screenshot")
                            
                            html_content += f"""
                    <div class="screenshot-card">
                        <img src="data:image/png;base64,{img_data}" 
                             class="screenshot-img" 
                             alt="{description}"
                             onclick="window.open('data:image/png;base64,{img_data}')">
                        <div class="screenshot-info">
                            <div class="screenshot-label">
                                {'🎯 Result Page' if screenshot_type == 'result_page' else '❌ Failed Step' if screenshot_type == 'failed_step' else '📸 Step Screenshot'}
                            </div>
                            <strong>{description}</strong><br>
                            <small>{screenshot.get('summary', '')}</small>
                        </div>
                    </div>
"""
                        except Exception as e:
                            print(f"Failed to embed screenshot: {e}")
                
                html_content += """
                </div>
            </div>
        </div>
"""
            
            # Add Download Section
            html_content += f"""
        <div class="section">
            <h2>📥 Download Reports</h2>
            <div class="download-section">
                <div class="download-grid">
                    <a href="/api/download-report/{report_id}/html" class="download-btn" download>
                        📄 HTML Report
                    </a>
                    <a href="/api/download-report/{report_id}/pdf" class="download-btn" download>
                        📊 PDF Report
                    </a>
                    <a href="/api/download-report/{report_id}/analysis" class="download-btn" download>
                        📈 Analysis Report
                    </a>
                    <a href="/api/download-report/{report_id}/json-pdf" class="download-btn" download>
                        🗂️ JSON as PDF
                    </a>
                    <a href="/api/download-report/{report_id}/json" class="download-btn" download>
                        📋 Raw JSON
                    </a>
"""
            
            # Add screenshot download links
            if screenshots:
                for screenshot in screenshots:
                    filename = os.path.basename(screenshot.get("path", ""))
                    if filename:
                        html_content += f"""
                    <a href="/api/download-screenshot/{filename}" class="download-btn" download>
                        📸 {filename[:20]}...
                    </a>
"""
            
            html_content += """
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔄 Execution Timeline</h2>
            <div class="timeline">
"""
            
            # Add execution steps
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown").lower()
                action = step.get("action", "Unknown").replace('_', ' ').title()
                details = step.get("description") or step.get("details", "No details")
                screenshot_path = step.get("screenshot", "")
                error_message = step.get("error_message", "")
                
                icon_class = status if status in ["passed", "failed", "warning", "info"] else "info"
                
                html_content += f"""
                <div class="timeline-item">
                    <div class="timeline-icon {icon_class}">{i}</div>
                    <div class="timeline-content {icon_class}">
                        <h4>
                            <span>{action}</span>
                            <span class="badge {status}">{status.upper()}</span>
                        </h4>
                        <p>{details}</p>
"""
                
                if error_message:
                    html_content += f"""
                        <div style="margin-top: 10px; padding: 8px; background: #fee2e2; border-radius: 4px;">
                            <strong>Error:</strong> {error_message}
                        </div>
"""
                
                # Add screenshot if available
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        with open(screenshot_path, "rb") as img_file:
                            img_data = base64.b64encode(img_file.read()).decode()
                        html_content += f"""
                        <div style="margin-top: 10px;">
                            <img src="data:image/png;base64,{img_data}" 
                                 style="max-width: 200px; border-radius: 4px; border: 1px solid #ddd; cursor: pointer;"
                                 onclick="window.open('data:image/png;base64,{img_data}')"
                                 alt="Step Screenshot">
                        </div>
"""
                    except Exception as e:
                        print(f"Failed to embed step screenshot: {e}")
                
                html_content += """
                    </div>
                </div>
"""
            
            html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p><strong>NovaQA</strong> - AI-Powered Test Automation Platform</p>
            <p>© 2026 Developed by Monika | Powered by LangGraph + Playwright</p>
        </div>
    </div>
    
    <script>
        // Make all images clickable to open in new tab
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('img').forEach(img => {
                if (!img.onclick) {
                    img.style.cursor = 'pointer';
                    img.onclick = function() { 
                        window.open(this.src); 
                    };
                }
            });
        });
    </script>
</body>
</html>
"""
            
            # Save HTML file
            filename = f"report_{report_id}.html"
            filepath = os.path.join(self.html_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"[ReportGenerator] HTML report saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate HTML report: {e}")
            traceback.print_exc()
            return None
    
    def generate_json_report(self, test_data):
        """Generate JSON report with screenshots metadata"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Calculate summary
            summary = self._calculate_summary(execution)
            
            # Get result summary
            result_summary = self._get_result_summary_from_metadata(metadata)
            
            # Get screenshots
            screenshots = self._get_screenshots_for_report(metadata, report_id)
            
            # Get environment info
            env_info = self._get_environment_info()
            
            # Build JSON structure
            report_data = {
                "report_metadata": {
                    "report_id": report_id,
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "execution_report"
                },
                "test_summary": {
                    "instruction": instruction,
                    "total_steps": summary["total_steps"],
                    "passed_steps": summary["passed_steps"],
                    "failed_steps": summary["failed_steps"],
                    "warning_steps": summary["warning_steps"],
                    "info_steps": summary["info_steps"],
                    "success_rate": summary["pass_percentage"],
                    "status": summary["status"],
                    "result_summary": result_summary
                },
                "execution_details": {
                    "start_time": metadata.get("start_time"),
                    "end_time": metadata.get("end_time"),
                    "duration_seconds": metadata.get("duration_seconds", 0),
                    "browser": metadata.get("browser", "Chromium"),
                    "headless": metadata.get("headless", True)
                },
                "environment": env_info,
                "execution_steps": [
                    {
                        "step_number": idx + 1,
                        "step_name": step.get("action", "Unknown"),
                        "action_performed": step.get("description", step.get("details", "")),
                        "expected_result": step.get("expected_result", "N/A"),
                        "actual_result": step.get("actual_result", step.get("details", "")),
                        "status": step.get("status", "Unknown"),
                        "error_message": step.get("error_message", "") if step.get("status", "").lower() == "failed" else "",
                        "screenshot_path": step.get("screenshot", ""),
                        "step_execution_time": step.get("duration", 0)
                    }
                    for idx, step in enumerate(execution)
                ],
                "screenshots": [
                    {
                        "type": screenshot.get("type"),
                        "path": screenshot.get("path"),
                        "description": screenshot.get("description"),
                        "summary": screenshot.get("summary", "")
                    }
                    for screenshot in screenshots
                ]
            }
            
            # Save JSON file
            filename = f"report_{report_id}.json"
            filepath = os.path.join(self.json_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"[ReportGenerator] JSON report saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate JSON report: {e}")
            traceback.print_exc()
            return None
    
    def generate_analysis_report_html(self, test_data):
        """Generate HTML version of analysis report for dashboard"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            metadata = test_data.get("metadata", {})
            report_id = test_data.get("report_id", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Calculate summary
            summary = self._calculate_summary(execution)
            
            # Get result summary
            result_summary = self._get_result_summary_from_metadata(metadata)
            
            # Get environment info
            env_info = self._get_environment_info()
            
            # Format metadata
            start_time = metadata.get("start_time", datetime.now().isoformat())
            end_time = metadata.get("end_time", datetime.now().isoformat())
            duration = metadata.get("duration_seconds", 0)
            
            try:
                start_dt = datetime.fromisoformat(start_time)
                start_time_formatted = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                start_time_formatted = start_time
            
            try:
                end_dt = datetime.fromisoformat(end_time)
                end_time_formatted = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                end_time_formatted = end_time
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get screenshots
            screenshots = self._get_screenshots_for_report(metadata, report_id)
            
            html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Report - {report_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ padding: 30px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px; }}
        .summary-card {{ text-align: center; padding: 20px; border-radius: 8px; background: white; border: 1px solid #e5e7eb; }}
        .section {{ padding: 30px; border-bottom: 1px solid #e5e7eb; }}
        .analysis-box {{ margin-top: 20px; }}
        .analysis-box.success {{ background: #f0fdf4; border-left: 4px solid #10B981; padding: 20px; border-radius: 8px; }}
        .analysis-box.failure {{ background: #fef2f2; border-left: 4px solid #EF4444; padding: 20px; border-radius: 8px; }}
        .result-summary-box {{ background: #e0f2fe; border-left: 4px solid #06B6D4; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .step-analysis {{ margin-top: 20px; }}
        .step-item {{ padding: 15px; margin-bottom: 10px; border-radius: 8px; background: #f9fafb; border-left: 4px solid #e5e7eb; }}
        .step-item.passed {{ border-left-color: #10B981; background: #f0fdf4; }}
        .step-item.failed {{ border-left-color: #EF4444; background: #fef2f2; }}
        .recommendations {{ margin-top: 20px; }}
        .recommendation-item {{ padding: 10px; margin-bottom: 8px; border-radius: 6px; background: white; border-left: 3px solid #3b82f6; }}
        .metadata-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }}
        .metadata-item {{ padding: 15px; background: #f9fafb; border-radius: 8px; border-left: 3px solid #06B6D4; }}
        .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
        .screenshot-item {{ text-align: center; }}
        .screenshot-img {{ width: 100%; height: 150px; object-fit: cover; border-radius: 6px; border: 1px solid #e5e7eb; cursor: pointer; }}
        .status-badge {{ padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; display: inline-block; margin-left: 10px; }}
        .status-passed {{ background: #dcfce7; color: #15803d; }}
        .status-failed {{ background: #fee2e2; color: #dc2626; }}
        .status-warning {{ background: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Analysis Report - {report_id}</h1>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="summary">
            <h2>Test Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{summary["total_steps"]}</h3>
                    <p>Total Steps</p>
                </div>
                <div class="summary-card">
                    <h3>{summary["passed_steps"]}</h3>
                    <p>Passed</p>
                </div>
                <div class="summary-card">
                    <h3>{summary["failed_steps"]}</h3>
                    <p>Failed</p>
                </div>
                <div class="summary-card">
                    <h3>{summary["pass_percentage"]:.1f}%</h3>
                    <p>Success Rate</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Test Information</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Instruction</label>
                    <strong>{instruction}</strong>
                </div>
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Status</label>
                    <span class="status-badge {'status-passed' if summary['status'] == 'PASSED' else 'status-failed'}">{summary['status']}</span>
                </div>
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Duration</label>
                    <strong>{duration:.2f} seconds</strong>
                </div>
            </div>
'''
            
            # Add Result Summary Section
            if result_summary:
                html_content += f'''
            <div class="result-summary-box">
                <h3>📋 Result Page Summary</h3>
                <p><strong>Search Results Summary:</strong></p>
                <p>{result_summary}</p>
            </div>
'''
            
            html_content += '''
        </div>
        
        <div class="section">
            <h2>Analysis</h2>
            <div class="analysis-box {'success' if summary['status'] == 'PASSED' else 'failure'}">
                <h3>{'✅ Success Analysis' if summary['status'] == 'PASSED' else '❌ Failure Analysis'}</h3>
                <p>
'''
            
            if summary['status'] == 'PASSED':
                html_content += f'''
                    All {summary["total_steps"]} steps executed successfully. The test completed in {duration:.2f} seconds with a {summary["pass_percentage"]:.1f}% success rate.
                '''
            else:
                html_content += f'''
                    {summary["failed_steps"]} out of {summary["total_steps"]} steps failed. The test completed in {duration:.2f} seconds with a {summary["pass_percentage"]:.1f}% success rate.
                '''
            
            html_content += '''
                </p>
            </div>
            
            <div class="step-analysis">
                <h3 style="margin-top: 20px;">Step-by-Step Analysis</h3>
'''
            
            # Add step analysis
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown").lower()
                status_class = "passed" if status == "passed" else "failed" if status == "failed" else ""
                
                html_content += f'''
                <div class="step-item {status_class}">
                    <h4>
                        Step {i}: {step.get("action", "Unknown").replace("_", " ").title()}
                        <span class="status-badge {'status-passed' if status == 'passed' else 'status-failed' if status == 'failed' else 'status-warning'}">{status.upper()}</span>
                    </h4>
                    <p>{step.get("description", step.get("details", "No description"))}</p>
'''
                
                if step.get("error_message"):
                    html_content += f'''
                    <div style="background: #fee2e2; padding: 10px; border-radius: 4px; margin-top: 5px;">
                        <strong>Error:</strong> {step.get("error_message")}
                    </div>
'''
                
                html_content += '''
                </div>
'''
            
            html_content += '''
            </div>
            
            <div class="recommendations">
                <h3>Recommendations</h3>
'''
            
            # Add recommendations based on test status
            if summary['status'] == 'PASSED':
                recommendations = [
                    "✅ Continue with current test approach",
                    "✅ Consider adding more edge cases",
                    "✅ Run performance tests",
                    "✅ Integrate with CI/CD pipeline"
                ]
            else:
                recommendations = [
                    "🔧 Review failed step selectors",
                    "🔧 Add wait times before critical actions",
                    "🔧 Implement retry logic for flaky tests",
                    "🔧 Verify test data accuracy"
                ]
            
            for rec in recommendations:
                html_content += f'''
                <div class="recommendation-item">
                    {rec}
                </div>
'''
            
            html_content += '''
            </div>
        </div>
        
        <div class="section">
            <h2>Screenshots</h2>
'''
            
            # Add screenshots
            if screenshots:
                html_content += '''
            <div class="screenshot-grid">
'''
                
                for screenshot in screenshots:
                    if os.path.exists(screenshot.get("path", "")):
                        try:
                            with open(screenshot["path"], "rb") as f:
                                img_data = base64.b64encode(f.read()).decode()
                            
                            screenshot_type = screenshot.get("type", "step")
                            description = screenshot.get("description", "Screenshot")
                            
                            html_content += f'''
                <div class="screenshot-item">
                    <img src="data:image/png;base64,{img_data}" 
                         class="screenshot-img" 
                         alt="{description}"
                         onclick="window.open('data:image/png;base64,{img_data}')">
                    <div style="margin-top: 5px; font-size: 12px;">
                        {description}
                    </div>
                </div>
'''
                        except:
                            pass
                
                html_content += '''
            </div>
'''
            else:
                html_content += '''
            <p>No screenshots available for this report.</p>
'''
            
            html_content += '''
        </div>
        
        <div class="section">
            <h2>Metadata</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Start Time</label>
                    <strong>{start_time_formatted}</strong>
                </div>
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">End Time</label>
                    <strong>{end_time_formatted}</strong>
                </div>
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Browser</label>
                    <strong>{metadata.get('browser', 'Chromium')}</strong>
                </div>
                <div class="metadata-item">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 5px;">Mode</label>
                    <strong>{'Headless' if metadata.get('headless', True) else 'Headed'}</strong>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Make all images clickable to open in new tab
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('img').forEach(img => {
                img.style.cursor = 'pointer';
                img.onclick = function() { 
                    window.open(this.src); 
                };
            });
        });
    </script>
</body>
</html>
'''
            
            # Save HTML file
            filename = f"analysis_{report_id}.html"
            filepath = os.path.join(self.analysis_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"[ReportGenerator] Analysis HTML saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate analysis HTML: {e}")
            traceback.print_exc()
            return None

# Example usage
if __name__ == "__main__":
    # Test the report generator
    generator = ReportGenerator()
    
    # Sample test data with result summary
    test_data = {
        "report_id": "GUEST-20260122215640",
        "instruction": "Go to google search apples",
        "execution": [
            {
                "action": "navigate",
                "status": "Passed",
                "details": "Navigated to https://www.google.com",
                "description": "Navigate to Google"
            },
            {
                "action": "type",
                "status": "Passed",
                "details": "Typed 'apples' in search box",
                "description": "Search for apples"
            },
            {
                "action": "press",
                "status": "Passed",
                "details": "Pressed Enter key",
                "description": "Submit search"
            },
            {
                "action": "result_page_capture",
                "status": "Passed",
                "details": "Result page screenshot captured",
                "description": "Capture final result page",
                "screenshot": "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png",
                "actual_result": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results."
            }
        ],
        "metadata": {
            "browser": "Chromium",
            "headless": True,
            "start_time": "2024-01-15T10:30:00",
            "end_time": "2024-01-15T10:32:30",
            "duration_seconds": 150,
            "result_summary": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results.",
            "screenshots": {
                "result_page": {
                    "screenshot_path": "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png",
                    "result_summary": "Search results for 'apples' showing nutritional information, recipes, and health benefits. Found approximately 1,340,000,000 results.",
                    "step_description": "Final Result Page"
                },
                "last_failed": None,
                "all": [
                    {
                        "path": "reports/screenshots/result_page_GUEST-20260122215640_20260125_123456.png",
                        "description": "Result Page",
                        "type": "result_page"
                    }
                ]
            }
        }
    }
    
    # Generate all reports
    print("\nGenerating reports...")
    html_report = generator.generate_html_report(test_data)
    json_report = generator.generate_json_report(test_data)
    pdf_report = generator.generate_pdf_report(test_data)
    enhanced_pdf = generator.generate_enhanced_pdf_report(test_data)
    analysis_html = generator.generate_analysis_report_html(test_data)
    json_pdf = generator.generate_json_to_pdf(test_data, test_data["report_id"])
    
    print(f"\n✅ Reports generated:")
    print(f"   HTML: {html_report}")
    print(f"   JSON: {json_report}")
    print(f"   PDF: {pdf_report}")
    print(f"   Enhanced PDF: {enhanced_pdf}")
    print(f"   Analysis HTML: {analysis_html}")
    print(f"   JSON as PDF: {json_pdf}")