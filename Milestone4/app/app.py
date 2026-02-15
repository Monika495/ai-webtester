from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sys
import os
import json
from datetime import datetime
import traceback
import time
import hashlib

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import components
from agent.universal_parser import UniversalParser
from agent.universal_executor import UniversalExecutor
from agent.codegen_agent import CodeGenerator
from agent.report_generator import ReportGenerator
from agent.database import Database
from agent.json_report_generator import JSONReportGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'novaqa-secret-key-2026-monika'
app.config['SESSION_COOKIE_SECURE'] = False  # For development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Create reports directory
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize components
codegen = CodeGenerator()
report_gen = ReportGenerator(reports_dir=REPORTS_DIR)
db = Database(db_path=os.path.join(PROJECT_ROOT, 'novaqa.db'))
json_report_gen = JSONReportGenerator(reports_dir=REPORTS_DIR)

print("=" * 60)
print("🚀 NovaQA - Enhanced Test Automation with Advanced Reporting")
print("=" * 60)
if GEMINI_API_KEY:
    print("🤖 AI MODE: ENABLED")
else:
    print("⚠️  AI MODE: DISABLED (Using Smart Regex)")
print("📊 Enhanced Reporting: ENABLED")
print("📸 Failure Screenshots: ENABLED")
print("📋 JSON Reports: ENABLED")
print("🎲 Smart Data Management: ENABLED")
print("🔧 Enhanced: Twitter/X, Amazon, LinkedIn, Wikipedia, Reddit, GitHub")
print("=" * 60)

# ==================== GUEST REPORT FILE STORAGE ====================

def get_guest_session_id():
    """Get or create unique guest session ID"""
    if 'guest_session_id' not in session:
        user_agent = request.headers.get('User-Agent', '') if request else ''
        timestamp = str(time.time())
        session_hash = hashlib.md5(f"{user_agent}_{timestamp}".encode()).hexdigest()[:16]
        session['guest_session_id'] = f"guest_{session_hash}"
        session.modified = True
        print(f"[SESSION] Created guest session ID: {session['guest_session_id']}")
    return session['guest_session_id']

def save_guest_report_to_file(guest_report):
    """Save guest report to JSON file (bypasses 4KB session limit)"""
    session_id = get_guest_session_id()
    guest_reports_dir = os.path.join(PROJECT_ROOT, 'guest_reports')
    os.makedirs(guest_reports_dir, exist_ok=True)
    
    # File path for this session
    session_file = os.path.join(guest_reports_dir, f"{session_id}.json")
    
    # Load existing reports
    existing_reports = []
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                existing_reports = json.load(f)
            print(f"[FILE] Loaded {len(existing_reports)} existing reports from {session_file}")
        except Exception as e:
            print(f"[FILE] Error loading existing reports: {e}")
            existing_reports = []
    
    # Add new report at beginning (newest first)
    existing_reports.insert(0, guest_report)
    
    # Keep only last 50 reports
    if len(existing_reports) > 50:
        existing_reports = existing_reports[:50]
        print(f"[FILE] Trimmed to 50 reports (oldest removed)")
    
    # Save to file
    try:
        with open(session_file, 'w') as f:
            json.dump(existing_reports, f, indent=2)
        
        print(f"✅ Guest report saved to FILE: {session_file}")
        print(f"📁 Total reports in file: {len(existing_reports)}")
        return len(existing_reports)
    except Exception as e:
        print(f"❌ Error saving to file: {e}")
        return 0

def load_guest_reports_from_file():
    """Load guest reports from file"""
    if 'guest_session_id' not in session:
        print("[FILE] No guest session ID found")
        return []
    
    session_id = session['guest_session_id']
    guest_reports_dir = os.path.join(PROJECT_ROOT, 'guest_reports')
    session_file = os.path.join(guest_reports_dir, f"{session_id}.json")
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                reports = json.load(f)
            print(f"✅ Loaded {len(reports)} guest reports from file: {session_file}")
            return reports
        except Exception as e:
            print(f"❌ Error loading guest reports from {session_file}: {e}")
            return []
    else:
        print(f"[FILE] No report file found: {session_file}")
        return []

# ==================== SESSION MANAGEMENT ====================

@app.before_request
def init_session():
    """Initialize session for guests"""
    if 'initialized' not in session:
        session['initialized'] = True
        session['guest_reports_count'] = 0
        session['test_stats'] = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0
        }
        print(f"[SESSION] New session initialized")

# ==================== AUTH ROUTES ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.verify_user(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            print(f"[AUTH] User logged in: {username} (ID: {user['id']})")
            return redirect(url_for('dashboard'))
        else:
            print(f"[AUTH] Failed login attempt: {username}")
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Signup page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        
        user_id = db.create_user(username, password, email)
        if user_id:
            session.clear()
            session['user_id'] = user_id
            session['username'] = username
            print(f"[AUTH] New user created: {username} (ID: {user_id})")
            return redirect(url_for('dashboard'))
        else:
            print(f"[AUTH] Failed signup: Username {username} already exists")
            return render_template("signup.html", error="Username already exists")
    
    return render_template("signup.html")

@app.route("/logout")
def logout():
    """Logout"""
    print(f"[AUTH] User logged out: {session.get('username')}")
    session.clear()
    return redirect(url_for('home'))

# ==================== MAIN ROUTES ====================

@app.route("/")
def home():
    """Landing page"""
    return render_template("home.html")

@app.route("/about")
def about():
    """About page"""
    return render_template("about.html")

@app.route("/how-it-works")
def how_it_works():
    """How it works page"""
    return render_template("how_it_works.html")

@app.route("/demo")
def demo():
    """Demo page"""
    return render_template("demo.html")

@app.route("/dashboard")
def dashboard():
    """Main dashboard"""
    username = session.get('username', 'Guest')
    user_id = session.get('user_id')
    
    # Get stats from session
    stats = session.get('test_stats', {
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'success_rate': 0
    })
    
    print(f"[DASHBOARD] User: {username}, ID: {user_id}, Stats: {stats}")
    
    return render_template(
        "dashboard.html", 
        username=username, 
        logged_in=user_id is not None,
        stats=stats
    )

@app.route("/reports")
def reports():
    """Reports page - FIXED to show ALL reports"""
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    
    print(f"\n{'='*60}")
    print(f"[REPORTS] Loading reports for user: {username} (ID: {user_id})")
    
    if user_id:
        # For logged-in users, get reports from database
        reports_list = db.get_reports(user_id=user_id)
        print(f"[REPORTS] Loaded {len(reports_list)} reports from database for user {user_id}")
    else:
        # For guests, get reports from FILE instead of session
        reports_list = load_guest_reports_from_file()
        print(f"[REPORTS] Loaded {len(reports_list)} reports from file for guest")
    
    # Ensure all reports have required fields
    enhanced_reports = []
    passed_count = 0
    failed_count = 0
    
    for report in reports_list:
        report_copy = report.copy() if isinstance(report, dict) else {}
        
        # Ensure required fields
        if 'report_id' not in report_copy:
            report_copy['report_id'] = f"UNKNOWN_{int(time.time())}"
        
        if 'instruction' not in report_copy:
            report_copy['instruction'] = "No instruction provided"
        
        if 'status' not in report_copy:
            report_copy['status'] = 'UNKNOWN'
        
        if 'total_steps' not in report_copy:
            report_copy['total_steps'] = 0
        
        if 'passed_steps' not in report_copy:
            report_copy['passed_steps'] = 0
        
        if 'failed_steps' not in report_copy:
            report_copy['failed_steps'] = 0
        
        if 'success_rate' not in report_copy:
            if report_copy['total_steps'] > 0:
                report_copy['success_rate'] = round(
                    (report_copy['passed_steps'] / report_copy['total_steps']) * 100, 
                    2
                )
            else:
                report_copy['success_rate'] = 0
        
        if 'created_at' not in report_copy:
            report_copy['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Count passed/failed
        if report_copy.get('status') == 'PASSED':
            passed_count += 1
        elif report_copy.get('status') == 'FAILED':
            failed_count += 1
        
        enhanced_reports.append(report_copy)
    
    # Sort by creation date (newest first)
    try:
        enhanced_reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except:
        pass
    
    print(f"[REPORTS] Displaying {len(enhanced_reports)} enhanced reports")
    print(f"[REPORTS] Passed: {passed_count}, Failed: {failed_count}")
    print(f"{'='*60}\n")
    
    return render_template(
        "reports.html", 
        reports=enhanced_reports, 
        logged_in=user_id is not None,
        passed_count=passed_count,
        failed_count=failed_count
    )

# ==================== REPORT DOWNLOAD ROUTES ====================

@app.route("/api/download-report/<report_id>/<format>", methods=["GET"])
def api_download_report_format(report_id, format):
    """Download report in specific format - GET VERSION"""
    try:
        print(f"[DOWNLOAD] Request to download report {report_id} in {format} format")
        
        user_id = session.get('user_id')
        
        # Get report data based on user type
        if user_id:
            # For logged-in users, get from database
            report_data = db.get_report_detail(report_id)
            print(f"[DOWNLOAD] Got report from DB for user {user_id}")
        else:
            # For guests, get from file
            reports_list = load_guest_reports_from_file()
            report_data = next((r for r in reports_list if isinstance(r, dict) and r.get('report_id') == report_id), None)
            print(f"[DOWNLOAD] Got report from file for guest")
        
        if not report_data:
            print(f"[DOWNLOAD] Report {report_id} not found")
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        print(f"[DOWNLOAD] Report found, generating {format}...")
        
        # Initialize report generator
        report_gen = ReportGenerator(reports_dir=REPORTS_DIR)
        
        if format == "html":
            filepath = report_gen.generate_html_report(report_data)
            if filepath and os.path.exists(filepath):
                print(f"[DOWNLOAD] HTML file ready: {filepath}")
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"novaqa_report_{report_id}.html",
                    mimetype='text/html'
                )
            else:
                print(f"[DOWNLOAD] HTML file not generated")
        
        elif format == "pdf":
            filepath = report_gen.generate_pdf_report(report_data)
            if filepath and os.path.exists(filepath):
                print(f"[DOWNLOAD] PDF file ready: {filepath}")
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"novaqa_report_{report_id}.pdf",
                    mimetype='application/pdf'
                )
            else:
                print(f"[DOWNLOAD] PDF file not generated")
        
        elif format == "analysis":
            filepath = report_gen.generate_enhanced_pdf_report(report_data)
            if filepath and os.path.exists(filepath):
                print(f"[DOWNLOAD] Analysis PDF ready: {filepath}")
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"novaqa_analysis_report_{report_id}.pdf",
                    mimetype='application/pdf'
                )
            else:
                print(f"[DOWNLOAD] Analysis PDF not generated")
        
        elif format == "json":
            filepath = report_gen.generate_json_report(report_data)
            if filepath and os.path.exists(filepath):
                print(f"[DOWNLOAD] JSON file ready: {filepath}")
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"novaqa_report_{report_id}.json",
                    mimetype='application/json'
                )
            else:
                print(f"[DOWNLOAD] JSON file not generated")
        
        elif format == "json-pdf":
            filepath = report_gen.generate_json_to_pdf(report_data, report_id)
            if filepath and os.path.exists(filepath):
                print(f"[DOWNLOAD] JSON PDF ready: {filepath}")
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"novaqa_json_report_{report_id}.pdf",
                    mimetype='application/pdf'
                )
            else:
                print(f"[DOWNLOAD] JSON PDF not generated")
        
        else:
            print(f"[DOWNLOAD] Invalid format requested: {format}")
            return jsonify({"success": False, "error": f"Invalid format: {format}"}), 400
        
        print(f"[DOWNLOAD] Failed to generate file for format: {format}")
        return jsonify({"success": False, "error": "Failed to generate report file"}), 500
        
    except Exception as e:
        print(f"❌ Error downloading report {report_id} in {format}: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to download report: {str(e)}"
        }), 500

@app.route("/api/download-screenshot/<filename>", methods=["GET"])
def api_download_screenshot(filename):
    """Download screenshot file"""
    try:
        screenshot_dir = os.path.join(REPORTS_DIR, "screenshots")
        filepath = os.path.join(screenshot_dir, filename)
        
        if os.path.exists(filepath):
            print(f"[SCREENSHOT] Downloading: {filename}")
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='image/png'
            )
        else:
            print(f"[SCREENSHOT] File not found: {filename}")
            return jsonify({"success": False, "error": "Screenshot not found"}), 404
            
    except Exception as e:
        print(f"❌ Error downloading screenshot {filename}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/download-all-screenshots/<report_id>", methods=["GET"])
def api_download_all_screenshots(report_id):
    """Download all screenshots as ZIP"""
    try:
        import zipfile
        import io
        
        screenshot_dir = os.path.join(REPORTS_DIR, "screenshots")
        
        # Find all screenshots for this report
        screenshot_files = []
        for filename in os.listdir(screenshot_dir):
            if report_id in filename and filename.endswith('.png') and not filename.startswith('thumb_'):
                screenshot_files.append(filename)
        
        if not screenshot_files:
            return jsonify({"success": False, "error": "No screenshots found"}), 404
        
        print(f"[SCREENSHOT ZIP] Creating ZIP with {len(screenshot_files)} screenshots for report {report_id}")
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename in screenshot_files:
                filepath = os.path.join(screenshot_dir, filename)
                if os.path.exists(filepath):
                    zip_file.write(filepath, filename)
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"screenshots_{report_id}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        print(f"❌ Error creating screenshot ZIP for {report_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
      
@app.route("/api/reports/<report_id>/screenshots", methods=["GET"])
def api_get_report_screenshots(report_id):
    """Get screenshots for a specific report"""
    try:
        user_id = session.get('user_id')
        
        # Get report data to check metadata
        if user_id:
            report_data = db.get_report_detail(report_id)
        else:
            reports_list = load_guest_reports_from_file()
            report_data = next((r for r in reports_list if r.get('report_id') == report_id), None)
        
        if not report_data:
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        screenshot_dir = os.path.join(REPORTS_DIR, "screenshots")
        
        # Find screenshots
        screenshots = []
        for filename in os.listdir(screenshot_dir):
            if report_id in filename and filename.endswith('.png'):
                if filename.startswith('thumb_'):
                    continue
                
                filepath = os.path.join(screenshot_dir, filename)
                
                # Get thumbnail if exists
                thumb_filename = f"thumb_{filename}"
                thumb_path = os.path.join(screenshot_dir, thumb_filename)
                
                screenshot_info = {
                    "filename": filename,
                    "url": f"/api/download-screenshot/{filename}",
                    "is_result_page": "result_page" in filename.lower(),
                    "is_failed_step": "failed" in filename.lower(),
                    "thumbnail": thumb_filename if os.path.exists(thumb_path) else filename
                }
                
                screenshots.append(screenshot_info)
        
        return jsonify({
            "success": True,
            "screenshots": screenshots,
            "count": len(screenshots)
        })
        
    except Exception as e:
        print(f"❌ Error getting screenshots for {report_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reports/<report_id>/files", methods=["GET"])
def api_get_report_files(report_id):
    """Get all files available for a report"""
    try:
        report_gen = ReportGenerator(reports_dir=REPORTS_DIR)
        
        files = []
        
        # Check HTML report
        html_path = os.path.join(report_gen.html_dir, f"report_{report_id}.html")
        if os.path.exists(html_path):
            files.append({
                "name": f"report_{report_id}.html",
                "type": "html",
                "url": f"/api/download-report/{report_id}/html",
                "description": "HTML Report"
            })
        
        # Check PDF report
        pdf_path = os.path.join(report_gen.pdf_dir, f"report_{report_id}.pdf")
        if os.path.exists(pdf_path):
            files.append({
                "name": f"report_{report_id}.pdf",
                "type": "pdf",
                "url": f"/api/download-report/{report_id}/pdf",
                "description": "PDF Report"
            })
        
        # Check analysis report
        analysis_path = os.path.join(report_gen.pdf_dir, f"analysis_report_{report_id}.pdf")
        if os.path.exists(analysis_path):
            files.append({
                "name": f"analysis_report_{report_id}.pdf",
                "type": "pdf",
                "url": f"/api/download-report/{report_id}/analysis",
                "description": "Analysis Report"
            })
        
        # Check JSON report
        json_path = os.path.join(report_gen.json_dir, f"report_{report_id}.json")
        if os.path.exists(json_path):
            files.append({
                "name": f"report_{report_id}.json",
                "type": "json",
                "url": f"/api/download-report/{report_id}/json",
                "description": "JSON Report"
            })
        
        # Check JSON PDF report
        json_pdf_path = os.path.join(report_gen.pdf_dir, f"json_report_{report_id}.pdf")
        if os.path.exists(json_pdf_path):
            files.append({
                "name": f"json_report_{report_id}.pdf",
                "type": "pdf",
                "url": f"/api/download-report/{report_id}/json-pdf",
                "description": "JSON as PDF"
            })
        
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        })
        
    except Exception as e:
        print(f"❌ Error getting files for {report_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sync-dashboard-reports", methods=["POST"])
def api_sync_dashboard_reports():
    """Sync reports to ensure dashboard shows correct count"""
    try:
        user_id = session.get('user_id')
        
        if user_id:
            reports_list = db.get_reports(user_id=user_id)
        else:
            reports_list = load_guest_reports_from_file()
        
        # Update session stats if needed
        if reports_list:
            passed_count = len([r for r in reports_list if isinstance(r, dict) and r.get('status') == 'PASSED'])
            failed_count = len([r for r in reports_list if isinstance(r, dict) and r.get('status') == 'FAILED'])
            
            stats = session.get('test_stats', {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0
            })
            
            stats['total_tests'] = len(reports_list)
            stats['passed_tests'] = passed_count
            stats['failed_tests'] = failed_count
            
            if stats['total_tests'] > 0:
                stats['success_rate'] = round((stats['passed_tests'] / stats['total_tests']) * 100, 2)
            
            session['test_stats'] = stats
            session.modified = True
        
        return jsonify({
            "success": True,
            "count": len(reports_list)
        })
        
    except Exception as e:
        print(f"❌ Error syncing dashboard reports: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reports/<report_id>")
def report_detail(report_id):
    """Individual report"""
    user_id = session.get('user_id')
    
    print(f"[REPORT_DETAIL] Requesting report: {report_id} for user ID: {user_id}")
    
    if user_id:
        report = db.get_report_detail(report_id)
        if report:
            print(f"[REPORT_DETAIL] Found database report")
            return render_template("report_detail.html", report=report)
        else:
            print(f"[REPORT_DETAIL] Database report not found")
            return "Report not found", 404
    else:
        # Load from FILE
        reports_list = load_guest_reports_from_file()
        report = next((r for r in reports_list if isinstance(r, dict) and r.get('report_id') == report_id), None)
        
        if report:
            print(f"[REPORT_DETAIL] Found guest report in file")
            return render_template("report_detail.html", report=report)
        else:
            print(f"[REPORT_DETAIL] Guest report not found in file")
            return "Report not found", 404

# ==================== API ENDPOINTS ====================

@app.route("/api/run-test", methods=["POST"])
def api_run_test():
    """Run test API with Enhanced Reporting - FIXED session storage and result page analysis"""
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
            instruction = data.get("instruction", "").strip()
            headless = data.get("headless", True)
            use_random_data = data.get("use_random_data", False)
        else:
            instruction = request.form.get("instruction", "").strip()
            headless = request.form.get("headless", "true").lower() == "true"
            use_random_data = request.form.get("use_random_data", "false").lower() == "true"
        
        if not instruction:
            return jsonify({
                "success": False,
                "error": "Please provide a test instruction"
            }), 400
        
        print(f"\n{'='*70}")
        print(f"🧪 TEST EXECUTION STARTED")
        print(f"{'='*70}")
        print(f"📝 Instruction: {instruction}")
        print(f"🔧 Headless: {headless}")
        print(f"🎲 Random Data: {'ENABLED' if use_random_data else 'DISABLED'}")
        
        # DEBUG: Check session data BEFORE test execution
        print(f"\n[DEBUG] 1. User ID in session: {session.get('user_id')}")
        print(f"[DEBUG] 2. User name in session: {session.get('username')}")
        print(f"[DEBUG] 3. Is user logged in: {bool(session.get('user_id'))}")
        print(f"{'='*70}")
        
        # Step 1: Parse with Smart Data Management
        start_time = time.time()
        parser = UniversalParser(api_key=GEMINI_API_KEY, use_random_data=use_random_data)
        parsed = parser.parse(instruction)
        parse_time = time.time() - start_time
        
        print(f"✅ Parsed into {len(parsed)} actions (took {parse_time:.2f}s)")
        
        # Check for parsing errors
        if len(parsed) > 0 and parsed[0].get("action") == "error":
            error_msg = parsed[0].get("error", "Unknown error")
            missing = parsed[0].get("missing_fields", [])
            suggestion = parsed[0].get("suggestion", "Enable 'Use Random Data' to auto-fill missing fields")
            details = parsed[0].get("details", "")
            
            response_data = {
                "success": False,
                "error": error_msg,
                "missing_fields": missing,
                "suggestion": suggestion
            }
            
            if details:
                response_data["details"] = details
            
            # Enhanced handling for LinkedIn account creation without credentials
            instruction_lower = instruction.lower()
            if "linkedin" in instruction_lower and not use_random_data:
                is_signup_or_create = any(kw in instruction_lower for kw in ["create", "signup", "join", "register"])
                
                if is_signup_or_create:
                    import re
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_match = re.search(email_pattern, instruction_lower)
                    has_email = bool(email_match)
                    
                    has_password = any(kw in instruction_lower for kw in ["password", "pass", "pwd"])
                    
                    if not (has_email and has_password):
                        response_data["is_linkedin_creation_error"] = True
                        response_data["retry_suggestion"] = "Enable Random Data and try again"
                        response_data["details"] = "LinkedIn account creation requires email and password, or enable Random Data"
            
            return jsonify(response_data), 400
        
        # Step 2: Execute with Enhanced Executor
        execution_start_time = time.time()
        # Pass GEMINI_API_KEY to UniversalExecutor for screenshot capture summarization
        executor = UniversalExecutor(api_key=GEMINI_API_KEY)
        
        # Execute the parsed actions
        execution = executor.run(parsed, headless=headless, report_id=None, instruction=instruction)
        execution_time = time.time() - execution_start_time
        
        # Extract screenshots from execution steps
        screenshots = []
        result_page_analysis = None
        final_screenshot_data = None
        final_screenshot_filename = None
        result_summary = None
        
        for step in execution:
            if step.get("screenshot") and os.path.exists(step.get("screenshot")):
                screenshots.append(step.get("screenshot"))
            
            # Check for result page analysis
            if step.get("action") == "result_page_capture":
                result_page_analysis = step.get("page_analysis", {})
                screenshot_path = step.get("screenshot", "")
                final_screenshot_data = {
                    "path": screenshot_path,
                    "filename": os.path.basename(screenshot_path) if screenshot_path else None,
                    "summary": step.get("result_summary", "Result page captured"),
                    "analysis": step.get("page_analysis", {}),
                    "is_final": True
                }
                final_screenshot_filename = os.path.basename(screenshot_path) if screenshot_path else None
                result_summary = step.get("result_summary", "Result page captured")
            
            # FIXED: Check for validation steps that might have content - removed .__dict__ access
            if step.get("action") == "validate_page" and step.get("result_content"):
                # Content is directly in the step result
                if not result_page_analysis:
                    result_page_analysis = {
                        "content": step.get("result_content"),
                        "summary": step.get("result_content")[:200] + "..." if step.get("result_content") and len(step.get("result_content")) > 200 else step.get("result_content")
                    }
                    result_summary = step.get("result_content")
            
            # Also check executor's execution_state (but only if it exists)
            if hasattr(executor, 'execution_state') and executor.execution_state and not result_page_analysis:
                if executor.execution_state.get("result_page_content"):
                    result_page_analysis = {
                        "content": executor.execution_state.get("result_page_content"),
                        "summary": executor.execution_state.get("result_summary")
                    }
                    result_summary = executor.execution_state.get("result_summary")
        
        # Capture final screenshot if not already captured
        has_failed_steps = any(s.get("status", "").lower() == "failed" for s in execution)
        final_screenshot = None
        try:
            if hasattr(executor, 'page') and executor.page:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_dir = os.path.join("reports", "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                
                # Generate a report_id if we don't have one yet
                current_report_id = None
                # Try to get from the loop above or generate a new one
                if 'report_id' in locals() and report_id:
                    current_report_id = report_id
                else:
                    current_report_id = f"GUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                screenshot_filename = f"result_page_{current_report_id}_{timestamp}.png"
                screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
                
                executor.page.screenshot(path=screenshot_path, full_page=True)
                final_screenshot = screenshot_path
                final_screenshot_filename = screenshot_filename
                print(f"[Executor] Captured final screenshot: {screenshot_path}")
                screenshots.append(final_screenshot)
                
                # If we don't have result page analysis, create it from final screenshot
                if not result_page_analysis:
                    # Try to get page content
                    try:
                        page_content = executor.page.inner_text("body")
                        # Clean content
                        import re
                        page_content = re.sub(r'\s+', ' ', page_content)
                        if len(page_content) > 500:
                            page_content = page_content[:500] + "..."
                        
                        result_page_analysis = {
                            "content": page_content,
                            "summary": f"Page loaded successfully: {executor.page.title() if executor.page.title() else 'Result page'}"
                        }
                        result_summary = page_content
                    except:
                        result_page_analysis = {"summary": "Result page captured"}
                        result_summary = "Result page captured"
                
                # Update final_screenshot_data if it doesn't exist yet
                if not final_screenshot_data:
                    final_screenshot_data = {
                        "path": screenshot_path,
                        "filename": screenshot_filename,
                        "summary": result_summary,
                        "analysis": result_page_analysis if isinstance(result_page_analysis, dict) else {"summary": result_page_analysis},
                        "is_final": True
                    }
        except Exception as e:
            print(f"[Executor] Failed to capture final screenshot: {e}")
        
        # Create metadata dictionary
        metadata = {
            "browser": "Chromium",
            "headless": headless,
            "start_time": datetime.fromtimestamp(execution_start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": execution_time,
            "screenshots": screenshots,
            "final_screenshot": final_screenshot,
            "final_screenshot_filename": final_screenshot_filename,
            "result_summary": result_summary
        }
        
        print(f"✅ Executed {len(execution)} actions (took {execution_time:.2f}s)")
        print(f"📸 Screenshots captured: {len(screenshots)}")
        if result_summary:
            print(f"📋 Result Summary: {result_summary[:100]}...")
        if final_screenshot_filename:
            print(f"📸 Final screenshot filename: {final_screenshot_filename}")
        
        # Step 3: Generate code
        generated_code = codegen.generate(parsed)
        
        # Extract data usage information from execution
        data_usage = {
            "provided": [],
            "generated": [],
            "mode": "provided_only"
        }
        
        # Also check parsed actions for data source info
        for action in parsed:
            if action.get("action") == "type":
                field_type = action.get("field_type", "")
                value = action.get("value", "")
                is_random = action.get("is_random_data", False)
                
                if field_type and value:
                    display_value = value[:20] + "..." if len(value) > 20 else value
                    if field_type == "password":
                        display_value = "********"
                    
                    if is_random:
                        data_usage["generated"].append({
                            "field": field_type,
                            "value": display_value
                        })
                    else:
                        data_usage["provided"].append({
                            "field": field_type,
                            "value": display_value
                        })
        
        # Determine data usage mode
        if use_random_data and data_usage["generated"]:
            if data_usage["provided"] and data_usage["generated"]:
                data_usage["mode"] = "mixed"
                print("🔧 Data Mode: MIXED (provided + generated)")
            elif data_usage["generated"]:
                data_usage["mode"] = "random_only"
                print("🎲 Data Mode: RANDOM ONLY (all fields generated)")
        elif data_usage["provided"]:
            data_usage["mode"] = "provided_only"
            print("✅ Data Mode: PROVIDED ONLY (all fields from instruction)")
        else:
            data_usage["mode"] = "none"
            print("🔍 Data Mode: NONE (no credentials needed)")
        
        # Calculate results
        total = len(execution)
        passed = len([s for s in execution if s.get("status", "").lower() == "passed"])
        failed = len([s for s in execution if s.get("status", "").lower() == "failed"])
        warning = len([s for s in execution if s.get("status", "").lower() == "warning"])
        info = len([s for s in execution if s.get("status", "").lower() == "info"])
        
        print(f"📊 Step Statuses: Passed={passed}, Failed={failed}, Warning={warning}, Info={info}")
        
        # Determine overall status based on actual failures
        has_failed_steps = any(s.get("status", "").lower() == "failed" for s in execution)
        has_warning_steps = any(s.get("status", "").lower() == "warning" for s in execution)
        
        if has_failed_steps:
            status = "FAILED"
        elif has_warning_steps:
            status = "WARNING"
        else:
            status = "PASSED"
        
        rate = (passed / total * 100) if total > 0 else 0
        
        # Prepare result with metadata
        result = {
            "instruction": instruction,
            "parsed": parsed,
            "execution": execution,
            "metadata": metadata,
            "generated_code": generated_code,
            "total_steps": total,
            "passed_steps": passed,
            "failed_steps": failed,
            "warning_steps": warning,
            "info_steps": info,
            "success_rate": round(rate, 2),
            "status": status,
            "used_random_data": use_random_data,
            "was_random_data_used": len(data_usage["generated"]) > 0,
            "data_usage": data_usage,
            "execution_time": round(execution_time, 2),
            "parse_time": round(parse_time, 2),
            "result_page_analysis": result_page_analysis,
            "final_screenshot_data": final_screenshot_data
        }
        
        # Save report
        user_id = session.get('user_id')
        
        if user_id:
            # For logged-in users, save to database
            print(f"\n[DEBUG] 4. Database save called with user_id: {user_id}")
            print(f"[DEBUG] 5. Report instruction: {instruction[:50]}...")
            print(f"[DEBUG] 6. Report will be saved for: {'User ' + str(user_id)}")
            
            report_id = db.save_report(result, user_id=user_id)
            print(f"✅ Saved to database: {report_id}")
        else:
            # For guests, save to FILE (not session)
            report_id = f"GUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            guest_report = {
                "report_id": report_id,
                "instruction": instruction,
                "total_steps": total,
                "passed_steps": passed,
                "failed_steps": failed,
                "warning_steps": warning,
                "info_steps": info,
                "success_rate": round(rate, 2),
                "status": status,
                "execution": execution,
                "metadata": metadata,
                "generated_code": generated_code,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "used_random_data": use_random_data,
                "was_random_data_used": len(data_usage["generated"]) > 0,
                "data_usage": data_usage,
                "result_page_analysis": result_page_analysis,
                "final_screenshot_data": final_screenshot_data
            }
            
            # Save to FILE instead of session (bypasses 4KB limit)
            total_reports = save_guest_report_to_file(guest_report)
            
            # Store only COUNT in session (small data)
            session['guest_reports_count'] = total_reports
            session.modified = True
            
            print(f"✅ Guest report stored in FILE: {report_id}")
            print(f"📊 Session only stores count: {total_reports}")
        
        # Step 4: Generate JSON report automatically
        json_report_data = None
        try:
            json_report_result = json_report_gen.generate_report(result, run_id=report_id)
            json_report_data = {
                "filepath": json_report_result["filepath"],
                "filename": json_report_result["filename"],
                "download_url": f"/api/download-json-report/{json_report_result['filename']}"
            }
            print(f"📊 Auto-generated JSON report: {json_report_result['filename']}")
        except Exception as json_error:
            print(f"⚠️ Failed to auto-generate JSON report: {json_error}")
            json_report_data = None
        
        # Step 5: Generate analysis report automatically
        analysis_report_data = None
        try:
            # Generate analysis HTML report
            analysis_html_path = report_gen.generate_analysis_report_html(result)
            
            # Generate enhanced PDF report
            enhanced_pdf_path = report_gen.generate_enhanced_pdf_report(result)
            
            if enhanced_pdf_path:
                enhanced_pdf_filename = os.path.basename(enhanced_pdf_path)
                analysis_report_data = {
                    "html_path": analysis_html_path,
                    "pdf_path": enhanced_pdf_path,
                    "pdf_filename": enhanced_pdf_filename,
                    "download_url": f"/api/download-analysis-pdf/{enhanced_pdf_filename}"
                }
                print(f"📄 Auto-generated analysis report: {enhanced_pdf_filename}")
        except Exception as pdf_error:
            print(f"⚠️ Failed to auto-generate analysis report: {pdf_error}")
            analysis_report_data = None
        
        # Update session stats
        stats = session.get('test_stats', {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0
        })
        
        stats['total_tests'] += 1
        if status == "PASSED":
            stats['passed_tests'] += 1
        else:
            stats['failed_tests'] += 1
        
        if stats['total_tests'] > 0:
            stats['success_rate'] = round((stats['passed_tests'] / stats['total_tests']) * 100, 2)
        
        session['test_stats'] = stats
        session.modified = True
        
        print(f"{'='*70}")
        print(f"📊 Result: {status} ({passed}/{total} passed, {failed} failed)")
        print(f"📈 Session Stats: {stats['total_tests']} tests, {stats['success_rate']}% success rate")
        print(f"💾 Data Usage: {data_usage['mode']}")
        print(f"📸 Screenshots: {len(screenshots)} captured")
        print(f"📸 Final Screenshot: {final_screenshot_filename or 'None'}")
        print(f"📋 Result Summary: {result_summary[:100] if result_summary else 'None'}...")
        print(f"📁 Generated Files:")
        if json_report_data:
            print(f"   • JSON Report: {json_report_data['filename']}")
        if analysis_report_data:
            print(f"   • Analysis Report: {analysis_report_data['pdf_filename']}")
        print(f"⏱️  Total time: {parse_time + execution_time:.2f}s")
        print(f"{'='*70}\n")
        
        return jsonify({
            "success": True,
            "report_id": report_id,
            "instruction": instruction,
            "parsed": parsed,
            "execution": execution,
            "metadata": metadata,
            "generated_code": generated_code,
            "used_random_data": use_random_data,
            "was_random_data_used": len(data_usage["generated"]) > 0,
            "data_usage": data_usage,
            "stats": stats,
            "execution_metadata": {
                "parse_time": round(parse_time, 2),
                "execution_time": round(execution_time, 2),
                "total_time": round(parse_time + execution_time, 2)
            },
            "status": status,
            "step_summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warning": warning,
                "info": info
            },
            "generated_files": {
                "json_report": json_report_data,
                "analysis_report": analysis_report_data
            },
            "download_urls": {
                "json": f"/api/generate-json-report/{report_id}" if json_report_data else None,
                "analysis": f"/api/generate-analysis-report/{report_id}" if analysis_report_data else None,
                "regular_pdf": f"/api/download-report/{report_id}",
                "html": f"/api/download-report/{report_id}"
            }
        })
    
    except Exception as e:
        print(f"❌ Error in api_run_test: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Server Error: {str(e)}",
            "traceback": traceback.format_exc() if app.debug else None
        }), 500

@app.route("/api/analyze-instruction", methods=["POST"])
def api_analyze_instruction():
    """Analyze instruction without executing - for UI preview"""
    try:
        data = request.get_json()
        instruction = data.get("instruction", "").strip()
        use_random_data = data.get("use_random_data", False)
        
        if not instruction:
            return jsonify({
                "success": False,
                "error": "Please provide an instruction"
            }), 400
        
        print(f"🔍 Analyzing instruction: {instruction}")
        
        # Quick analysis without full parsing
        instruction_lower = instruction.lower()
        
        # Check what kind of instruction this is
        analysis = {
            "type": "unknown",
            "requires_credentials": False,
            "has_credentials": False,
            "has_email": False,
            "has_password": False,
            "site": "unknown",
            "suggestions": []
        }
        
        # Detect site
        sites = ["linkedin", "twitter", "x.com", "facebook", "amazon", "google", "wikipedia", "reddit", "github"]
        for site in sites:
            if site in instruction_lower:
                analysis["site"] = site
                break
        
        # Check for credentials
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, instruction_lower)
        if email_match:
            analysis["has_email"] = True
            analysis["has_credentials"] = True
        
        pass_patterns = [r'password\s+(\S+)', r'pass\s+(\S+)']
        for pattern in pass_patterns:
            if re.search(pattern, instruction_lower):
                analysis["has_password"] = True
                analysis["has_credentials"] = True
                break
        
        # Determine instruction type
        is_login = any(kw in instruction_lower for kw in ["login", "signin", "sign in", "log in"])
        is_signup = any(kw in instruction_lower for kw in ["signup", "register", "sign up", "join", "create account", "create"])
        
        if is_signup:
            analysis["type"] = "signup"
            analysis["requires_credentials"] = True
            
            # LinkedIn specific analysis
            if analysis["site"] == "linkedin" and not analysis["has_credentials"]:
                analysis["requires_random_data"] = True
                analysis["suggestions"].append("This LinkedIn account creation requires Random Data or provided credentials")
                if not use_random_data:
                    analysis["suggestions"].append("Enable 'Use Random Data' checkbox")
        
        elif is_login:
            analysis["type"] = "login"
            analysis["requires_credentials"] = True
        
        elif any(kw in instruction_lower for kw in ["search", "find", "look for"]):
            analysis["type"] = "search"
        
        elif any(kw in instruction_lower for kw in ["go to", "open", "visit", "navigate"]):
            analysis["type"] = "navigation"
        
        # Generate suggestions
        if analysis["requires_credentials"] and not analysis["has_credentials"] and not use_random_data:
            analysis["suggestions"].append("This instruction requires credentials but none were provided")
            analysis["suggestions"].append("Either add credentials to instruction or enable Random Data")
        
        if analysis["has_credentials"] and use_random_data:
            analysis["data_mode"] = "mixed"
            analysis["suggestions"].append("Will use provided credentials + generate missing fields")
        elif not analysis["has_credentials"] and use_random_data:
            analysis["data_mode"] = "random"
            analysis["suggestions"].append("Will generate all required fields")
        elif analysis["has_credentials"] and not use_random_data:
            analysis["data_mode"] = "provided"
            analysis["suggestions"].append("Will use only provided credentials")
        
        print(f"✅ Analysis complete: {analysis['type']} on {analysis['site']}")
        
        return jsonify({
            "success": True,
            "analysis": analysis
        })
    
    except Exception as e:
        print(f"❌ Error in api_analyze_instruction: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Analysis Error: {str(e)}"
        }), 500

# Update all other API functions to use file storage instead of session
# For example, in api_download_report():

@app.route("/api/download-report/<format>", methods=["POST"])
def api_download_report(format):
    """Download enhanced report with multiple formats"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        report_id = data.get("report_id")
        
        if not report_id:
            return jsonify({"success": False, "error": "No report ID provided"}), 400
        
        user_id = session.get('user_id')
        
        if user_id:
            report_data = db.get_report_detail(report_id)
        else:
            # FIX: Load from FILE instead of session
            reports_list = load_guest_reports_from_file()
            report_data = next((r for r in reports_list if r.get('report_id') == report_id), None)
        
        if not report_data:
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        # Enhance report data with data usage info if not present
        if 'data_usage' not in report_data:
            report_data['data_usage'] = {
                'provided': [],
                'generated': [],
                'mode': 'unknown'
            }
        
        if 'metadata' not in report_data:
            report_data['metadata'] = {
                'browser': 'Chromium',
                'headless': True,
                'start_time': report_data.get('created_at', datetime.now().isoformat()),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': 0,
                'screenshots': []
            }
        
        try:
            if format == "html":
                filepath = report_gen.generate_html_report(report_data)
                return send_file(
                    filepath, 
                    as_attachment=True, 
                    download_name=f"novaqa_report_{report_id}.html",
                    mimetype='text/html'
                )
            
            elif format == "pdf":
                filepath = report_gen.generate_pdf_report(report_data)
                return send_file(
                    filepath, 
                    as_attachment=True, 
                    download_name=f"novaqa_report_{report_id}.pdf",
                    mimetype='application/pdf'
                )
            
            elif format == "json":
                # Generate JSON report using the enhanced generator
                json_filepath = report_gen.generate_json_report(report_data)
                return send_file(
                    json_filepath, 
                    as_attachment=True, 
                    download_name=f"novaqa_report_{report_id}.json",
                    mimetype='application/json'
                )
            
            else:
                return jsonify({"success": False, "error": "Invalid format"}), 400
        
        except Exception as e:
            print(f"❌ Error generating report: {str(e)}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to generate report: {str(e)}"}), 500
    
    except Exception as e:
        print(f"❌ Error in api_download_report: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# Similarly update other functions that access guest_reports from session:
# api_get_screenshots(), api_generate_analysis_report(), api_generate_json_pdf(),
# api_generate_json_report(), api_generate_enhanced_pdf(), api_delete_report()

@app.route("/api/delete-report/<report_id>", methods=["DELETE"])
def api_delete_report(report_id):
    """Delete a report and associated screenshots"""
    try:
        user_id = session.get('user_id')
        
        if user_id:
            # Get report data first to get screenshot info
            report_data = db.get_report_detail(report_id)
            deleted = db.delete_report(report_id, user_id=user_id)
        else:
            # FIX: Load from FILE, delete from FILE
            reports_list = load_guest_reports_from_file()
            report_data = next((r for r in reports_list if r.get('report_id') == report_id), None)
            
            if report_data:
                # Remove from list
                updated_reports = [r for r in reports_list if r.get('report_id') != report_id]
                
                # Save updated list to file
                session_id = get_guest_session_id()
                guest_reports_dir = os.path.join(PROJECT_ROOT, 'guest_reports')
                session_file = os.path.join(guest_reports_dir, f"{session_id}.json")
                
                with open(session_file, 'w') as f:
                    json.dump(updated_reports, f, indent=2)
                
                deleted = True
                print(f"[DELETE] Removed guest report {report_id} from file. Remaining: {len(updated_reports)}")
            else:
                deleted = False
        
        # Delete associated screenshots
        if deleted and report_data:
            screenshots = report_data.get('metadata', {}).get('screenshots', [])
            for screenshot in screenshots:
                if isinstance(screenshot, str):
                    screenshot_path = os.path.join(report_gen.screenshots_dir, screenshot)
                    if os.path.exists(screenshot_path):
                        try:
                            os.remove(screenshot_path)
                            print(f"🗑️ Deleted screenshot: {screenshot}")
                        except Exception as e:
                            print(f"⚠️ Failed to delete screenshot {screenshot}: {e}")
        
        if deleted:
            return jsonify({"success": True, "message": "Report deleted successfully"})
        else:
            return jsonify({"success": False, "error": "Report not found"}), 404
    
    except Exception as e:
        print(f"❌ Error in api_delete_report: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get-stats", methods=["GET"])
def api_get_stats():
    """Get session statistics"""
    stats = session.get('test_stats', {
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'success_rate': 0
    })
    
    return jsonify({
        "success": True,
        "stats": stats
    })

@app.route("/api/test-examples", methods=["GET"])
def api_test_examples():
    """Get test examples with smart categorization"""
    examples = [
        {
            "category": "✅ Provided Credentials (Always Works)",
            "description": "All required credentials are provided in instruction",
            "tests": [
                {
                    "text": "signup on linkedin with email test@mail.com password test123",
                    "data_mode": "provided",
                    "notes": "Uses provided email and password"
                },
                {
                    "text": "login to twitter with username myuser password mypass",
                    "data_mode": "provided", 
                    "notes": "Uses provided username and password"
                }
            ]
        },
        {
            "category": "🎲 Random Data Required",
            "description": "No credentials provided - requires Random Data",
            "tests": [
                {
                    "text": "create an account on linkedin",
                    "data_mode": "random",
                    "notes": "Requires Random Data enabled"
                },
                {
                    "text": "signup on github",
                    "data_mode": "random",
                    "notes": "Requires Random Data enabled"
                }
            ]
        },
        {
            "category": "🔍 Search & Navigation",
            "description": "No credentials needed",
            "tests": [
                {
                    "text": "search laptop on amazon and add to cart",
                    "data_mode": "none",
                    "notes": "No login required"
                },
                {
                    "text": "search python on google",
                    "data_mode": "none",
                    "notes": "Simple search test"
                },
                {
                    "text": "go to wikipedia and search quantum physics",
                    "data_mode": "none",
                    "notes": "Wikipedia search test"
                }
            ]
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Page not found",
        "message": "The requested URL was not found on the server"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"❌ Internal Server Error: {error}")
    traceback.print_exc()
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": str(error) if app.debug else "Something went wrong"
    }), 500

# ==================== RUN ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 NovaQA Enhanced Test Automation Server")
    print("=" * 60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"📁 Project: {PROJECT_ROOT}")
    print(f"📂 Reports: {REPORTS_DIR}")
    print(f"🤖 AI Parser: {'ENABLED' if GEMINI_API_KEY else 'SMART REGEX'}")
    print(f"📊 Enhanced Reporting: ENABLED")
    print(f"📸 Analysis Reports: ENABLED")
    print(f"💡 Enhanced Features:")
    print(f"  • Final screenshots on success/failure")
    print(f"  • Analysis reports with recommendations")
    print(f"  • JSON to PDF conversion")
    print(f"  • Step-level analysis in reports")
    print(f"  • Download individual screenshots")
    print(f"  • Result page content extraction")
    print(f"🎲 Smart Data Management: ENABLED")
    print(f"🔧 Supported: Twitter/X, Amazon, LinkedIn, Wikipedia, Reddit, GitHub")
    print("=" * 60)
    
    # Create guest reports directory
    guest_reports_dir = os.path.join(PROJECT_ROOT, 'guest_reports')
    os.makedirs(guest_reports_dir, exist_ok=True)
    print(f"📁 Guest reports directory: {guest_reports_dir}")
    
    # Test random data generation
    import random
    first_names = ["John", "Emma", "Michael", "Sarah", "David", "Lisa", "Robert", "Maria"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "zoho.com"]
    
    random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    random_email = f"{random.choice(first_names).lower()}{random.choice(last_names).lower()}{random.randint(100, 999)}@{random.choice(domains)}"
    print(f"🎲 Random Data Test: {random_name} - {random_email}")
    
    # Test report generator directories
    print("\n🧪 Report Generator Test:")
    for dir_name, dir_path in [
        ("HTML directory", report_gen.html_dir),
        ("JSON directory", report_gen.json_dir),
        ("PDF directory", report_gen.pdf_dir),
        ("Screenshots directory", report_gen.screenshots_dir),
        ("Analysis directory", report_gen.analysis_dir)
    ]:
        if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
            print(f"  ✅ {dir_name}: {dir_path}")
        else:
            print(f"  ❌ {dir_name}: {dir_path} - NOT WRITABLE")
    
    print("\n✅ All systems ready!")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=5000, debug=True)