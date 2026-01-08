"""
Report generation module for NovaQA
"""
from datetime import datetime
import os

class ReportGenerator:
    """Generate downloadable test reports"""
    
    def __init__(self, reports_dir="reports"):
        self.reports_dir = reports_dir
        # Create directory if it doesn't exist
        os.makedirs(reports_dir, exist_ok=True)
        print(f"[ReportGenerator] Reports directory: {self.reports_dir}")
        print(f"[ReportGenerator] Absolute path: {os.path.abspath(reports_dir)}")
    
    def generate_html_report(self, test_data):
        """Generate HTML report"""
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            generated_code = test_data.get("generated_code", "")
            
            # Calculate statistics
            total_steps = len(execution)
            passed_steps = len([s for s in execution if s.get("status") == "Passed"])
            failed_steps = total_steps - passed_steps
            success_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Build HTML
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaQA Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 20px;
            color: #E2E8F0;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.9);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #06B6D4;
        }}
        
        .header h1 {{
            color: #06B6D4;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(15, 23, 42, 0.6);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(6, 182, 212, 0.3);
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: #06B6D4;
            margin-bottom: 5px;
        }}
        
        .section {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(6, 182, 212, 0.2);
        }}
        
        .step-item {{
            background: rgba(30, 41, 59, 0.6);
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .step-item.passed {{
            border-left: 4px solid #10B981;
        }}
        
        .step-item.failed {{
            border-left: 4px solid #EF4444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 NovaQA Test Report</h1>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_steps}</div>
                <div>Total Steps</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #10B981;">{passed_steps}</div>
                <div>Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #EF4444;">{failed_steps}</div>
                <div>Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{success_rate:.0f}%</div>
                <div>Success Rate</div>
            </div>
        </div>
        
        <div class="section">
            <h2 style="color: #06B6D4;">Test Instruction</h2>
            <p style="margin-top: 1rem; color: #CBD5E1;">{instruction}</p>
        </div>
        
        <div class="section">
            <h2 style="color: #06B6D4;">Execution Steps</h2>
"""
            
            # Add execution steps
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown")
                action = step.get("action", "Unknown")
                details = step.get("details", "No details")
                
                html_content += f"""            <div class="step-item {status.lower()}">
                <span style="background: rgba(16, 185, 129, 0.2); color: #10B981; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">{status}</span>
                <div style="flex: 1;">
                    <div style="color: #E2E8F0; font-weight: 600;">Step {i}: {action.replace('_', ' ').title()}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem;">{details}</div>
                </div>
            </div>
"""
            
            html_content += f"""        </div>
        
        <div class="section">
            <h2 style="color: #06B6D4;">Generated Test Code</h2>
            <pre style="background: #1E293B; padding: 20px; border-radius: 8px; overflow-x: auto; color: #E2E8F0;">{generated_code if generated_code else 'No code generated'}</pre>
        </div>
        
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(6, 182, 212, 0.2); color: #94A3B8;">
            <p><strong>NovaQA</strong> - AI-Powered Test Automation Platform</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Save HTML file
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.reports_dir, filename)
            
            print(f"[ReportGenerator] Writing HTML to: {filepath}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"[ReportGenerator] HTML report saved successfully")
            print(f"[ReportGenerator] File exists: {os.path.exists(filepath)}")
            print(f"[ReportGenerator] File size: {os.path.getsize(filepath)} bytes")
            
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate HTML report: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_pdf_report(self, test_data):
        """Generate PDF report using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except ImportError:
            print("[WARNING] reportlab not installed, generating HTML instead")
            # If reportlab not installed, return HTML instead
            return self.generate_html_report(test_data)
        
        try:
            instruction = test_data.get("instruction", "N/A")
            execution = test_data.get("execution", [])
            
            # Calculate statistics
            total_steps = len(execution)
            passed_steps = len([s for s in execution if s.get("status") == "Passed"])
            failed_steps = total_steps - passed_steps
            success_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            print(f"[ReportGenerator] Writing PDF to: {filepath}")
            
            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#06B6D4'),
                spaceAfter=30,
                alignment=1
            )
            
            # Title
            story.append(Paragraph("NovaQA Test Report", title_style))
            story.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Statistics table
            stats_data = [
                ['Total Steps', 'Passed', 'Failed', 'Success Rate'],
                [str(total_steps), str(passed_steps), str(failed_steps), f"{success_rate:.0f}%"]
            ]
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06B6D4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Test instruction
            story.append(Paragraph("<b>Test Instruction:</b>", styles['Heading2']))
            story.append(Paragraph(instruction, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Execution steps
            story.append(Paragraph("<b>Execution Steps:</b>", styles['Heading2']))
            
            for i, step in enumerate(execution, 1):
                status = step.get("status", "Unknown")
                action = step.get("action", "Unknown")
                details = step.get("details", "No details")
                
                step_text = f"<b>Step {i}:</b> {action.replace('_', ' ').title()}<br/>"
                step_text += f"<b>Status:</b> {status}<br/>"
                step_text += f"<b>Details:</b> {details}"
                
                story.append(Paragraph(step_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            # Build PDF
            doc.build(story)
            
            print(f"[ReportGenerator] PDF report saved successfully")
            print(f"[ReportGenerator] File exists: {os.path.exists(filepath)}")
            print(f"[ReportGenerator] File size: {os.path.getsize(filepath)} bytes")
            
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to generate PDF report: {e}")
            import traceback
            traceback.print_exc()
            raise