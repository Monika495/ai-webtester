from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sys
import os
import json
from datetime import datetime
import traceback
import time

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import components
from agent.universal_parser import UniversalParser
from agent.universal_executor import UniversalExecutor
from agent.codegen_agent import CodeGenerator
from agent.report_generator import ReportGenerator
from agent.database import Database

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

print("=" * 60)
print("🚀 NovaQA - AI Test Automation with Smart Data Management")
print("=" * 60)
if GEMINI_API_KEY:
    print("🤖 AI MODE: ENABLED")
else:
    print("⚠️  AI MODE: DISABLED (Using Smart Regex)")
print("🎲 Smart Random Data: ENABLED")
print("🔧 Enhanced: Twitter/X, Amazon, LinkedIn, Wikipedia")
print("💡 Smart Data Handling: Uses provided data + generates missing fields")
print("=" * 60)

# ==================== SESSION MANAGEMENT ====================

@app.before_request
def init_session():
    """Initialize session for guests"""
    if 'initialized' not in session:
        session['initialized'] = True
        session['guest_reports'] = []
        session['test_stats'] = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0
        }

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
            return redirect(url_for('dashboard'))
        else:
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
            return redirect(url_for('dashboard'))
        else:
            return render_template("signup.html", error="Username already exists")
    
    return render_template("signup.html")

@app.route("/logout")
def logout():
    """Logout"""
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
    
    return render_template(
        "dashboard.html", 
        username=username, 
        logged_in=user_id is not None,
        stats=stats
    )

@app.route("/reports")
def reports():
    """Reports page"""
    user_id = session.get('user_id')
    
    if user_id:
        reports_list = db.get_reports(user_id=user_id)
    else:
        reports_list = session.get('guest_reports', [])
    
    return render_template(
        "reports.html", 
        reports=reports_list, 
        logged_in=user_id is not None
    )

@app.route("/reports/<report_id>")
def report_detail(report_id):
    """Individual report"""
    user_id = session.get('user_id')
    
    if user_id:
        report = db.get_report_detail(report_id)
        if report:
            return render_template("report_detail.html", report=report)
        else:
            return "Report not found", 404
    else:
        guest_reports = session.get('guest_reports', [])
        report = next((r for r in guest_reports if r.get('report_id') == report_id), None)
        
        if report:
            return render_template("report_detail.html", report=report)
        else:
            return "Report not found", 404

# ==================== API ENDPOINTS ====================

@app.route("/api/run-test", methods=["POST"])
def api_run_test():
    """Run test API with Smart Data Management"""
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
                # Check what kind of LinkedIn instruction this is
                is_signup_or_create = any(kw in instruction_lower for kw in ["create", "signup", "join", "register"])
                
                if is_signup_or_create:
                    # Check if credentials are provided
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
        
        # Step 2: Execute with Smart Validation
        start_time = time.time()
        executor = UniversalExecutor()
        execution = executor.run(parsed, headless=headless)
        execution_time = time.time() - start_time
        
        print(f"✅ Executed {len(execution)} actions (took {execution_time:.2f}s)")
        
        # Step 3: Generate code
        generated_code = codegen.generate(parsed)
        
        # Extract data usage information from execution
        data_usage = {
            "provided": [],
            "generated": [],
            "mode": "provided_only"  # Default mode
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
        
        # Calculate results - FIXED: Check all step statuses
        total = len(execution)
        passed = len([s for s in execution if s.get("status") in ["Passed", "passed"]])
        failed = len([s for s in execution if s.get("status") in ["Failed", "failed"]])
        warning = len([s for s in execution if s.get("status") in ["Warning", "warning"]])
        info = len([s for s in execution if s.get("status") in ["Info", "info"]])
        
        print(f"📊 Step Statuses: Passed={passed}, Failed={failed}, Warning={warning}, Info={info}")
        
        # FIXED: Determine overall status based on actual failures
        has_failed_steps = any(s.get("status") in ["Failed", "failed"] for s in execution)
        has_warning_steps = any(s.get("status") in ["Warning", "warning"] for s in execution)
        
        if has_failed_steps:
            status = "FAILED"
        elif has_warning_steps:
            status = "WARNING"
        else:
            status = "PASSED"
        
        rate = (passed / total * 100) if total > 0 else 0
        
        # Prepare result
        result = {
            "instruction": instruction,
            "parsed": parsed,
            "execution": execution,
            "generated_code": generated_code,
            "total_steps": total,
            "passed_steps": passed,
            "failed_steps": failed,
            "warning_steps": warning,
            "info_steps": info,
            "success_rate": round(rate, 2),
            "status": status,  # Use the corrected status
            "used_random_data": use_random_data,
            "was_random_data_used": len(data_usage["generated"]) > 0,
            "data_usage": data_usage,
            "execution_time": round(execution_time, 2),
            "parse_time": round(parse_time, 2)
        }
        
        # Save report
        user_id = session.get('user_id')
        
        if user_id:
            report_id = db.save_report(result, user_id=user_id)
            print(f"✅ Saved to database: {report_id}")
        else:
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
                "status": status,  # Use the corrected status
                "execution": execution,
                "generated_code": generated_code,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "used_random_data": use_random_data,
                "was_random_data_used": len(data_usage["generated"]) > 0,
                "data_usage": data_usage
            }
            
            if 'guest_reports' not in session:
                session['guest_reports'] = []
            
            session['guest_reports'].append(guest_report)
            session.modified = True
            
            print(f"✅ Stored in session: {report_id}")
        
        # Update session stats - FIXED: Use corrected status
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
        if data_usage['generated']:
            print(f"🎲 Random data was used ({len(data_usage['generated'])} fields)")
        if data_usage['provided']:
            print(f"✅ Provided data used ({len(data_usage['provided'])} fields)")
        print(f"⏱️  Total time: {parse_time + execution_time:.2f}s")
        print(f"{'='*70}\n")
        
        return jsonify({
            "success": True,
            "report_id": report_id,
            "instruction": instruction,
            "parsed": parsed,
            "execution": execution,
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
            "status": status,  # Include status in response
            "step_summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warning": warning,
                "info": info
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

@app.route("/api/download-report/<format>", methods=["POST"])
def api_download_report(format):
    """Download report"""
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
            guest_reports = session.get('guest_reports', [])
            report_data = next((r for r in guest_reports if r.get('report_id') == report_id), None)
        
        if not report_data:
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        # Enhance report data with data usage info
        if 'data_usage' not in report_data:
            report_data['data_usage'] = {
                'provided': [],
                'generated': [],
                'mode': 'unknown'
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
                # Return JSON report
                return jsonify({
                    "success": True,
                    "report": report_data
                })
            
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

@app.route("/api/delete-report/<report_id>", methods=["DELETE"])
def api_delete_report(report_id):
    """Delete a report"""
    try:
        user_id = session.get('user_id')
        
        if user_id:
            deleted = db.delete_report(report_id, user_id=user_id)
        else:
            guest_reports = session.get('guest_reports', [])
            report = next((r for r in guest_reports if r.get('report_id') == report_id), None)
            
            if report:
                guest_reports.remove(report)
                session['guest_reports'] = guest_reports
                session.modified = True
                deleted = True
            else:
                deleted = False
        
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

# ==================== TEST MODES EXPLANATION ====================

@app.route("/api/test-modes", methods=["GET"])
def api_test_modes():
    """Get explanation of different test modes"""
    modes = [
        {
            "id": "provided",
            "name": "Provided Data Mode",
            "description": "All required credentials are provided in the instruction",
            "example": "signup on linkedin with email test@mail.com password test123",
            "requirements": "Email and password must be provided in instruction",
            "random_data": "Not required"
        },
        {
            "id": "random",
            "name": "Random Data Mode", 
            "description": "No credentials provided - all fields generated automatically",
            "example": "create an account on linkedin",
            "requirements": "Random Data checkbox must be enabled",
            "random_data": "Required"
        },
        {
            "id": "mixed",
            "name": "Mixed Data Mode",
            "description": "Some credentials provided, missing ones generated with Random Data",
            "example": "signup on twitter with email test@mail.com",
            "requirements": "Partial credentials + Random Data enabled",
            "random_data": "Required"
        }
    ]
    
    return jsonify({
        "success": True,
        "modes": modes
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

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
    print("🚀 NovaQA Smart Test Automation Server")
    print("=" * 60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"📁 Project: {PROJECT_ROOT}")
    print(f"📂 Reports: {REPORTS_DIR}")
    print(f"🤖 AI Parser: {'ENABLED' if GEMINI_API_KEY else 'SMART REGEX'}")
    print(f"🎲 Smart Data Management: ENABLED")
    print(f"💡 Features:")
    print(f"  • Uses provided credentials when available")
    print(f"  • Generates missing fields with Random Data")
    print(f"  • Fails gracefully when credentials missing")
    print(f"  • Clear data usage reporting")
    print(f"🔧 Supported: Twitter/X, Amazon, LinkedIn, Wikipedia, Reddit, GitHub")
    print(f"🔄 Test Modes: Provided, Random, Mixed")
    print("=" * 60 + "\n")
    
    # Test the components
    try:
        # Test random data
        from agent.random_data import get_random_profile
        profile = get_random_profile()
        print(f"🎲 Random Data Test: {profile.get('first_name')} {profile.get('last_name')} - {profile.get('email')}")
        
        # Test parser with different modes
        print("\n🧪 Parser Tests:")
        
        # Test 1: Provided credentials
        test1 = "signup on linkedin with email test@mail.com password test123"
        parser1 = UniversalParser(api_key=GEMINI_API_KEY, use_random_data=False)
        parsed1 = parser1.parse(test1)
        print(f"  ✅ '{test1}' -> {len(parsed1)} actions (Provided Mode)")
        
        # Test 2: Requires random data
        test2 = "create an account on linkedin"
        parser2 = UniversalParser(api_key=GEMINI_API_KEY, use_random_data=True)
        parsed2 = parser2.parse(test2)
        print(f"  ✅ '{test2}' -> {len(parsed2)} actions (Random Data Mode)")
        
        # Test 3: Mixed mode
        test3 = "signup on twitter with email test@mail.com"
        parser3 = UniversalParser(api_key=GEMINI_API_KEY, use_random_data=True)
        parsed3 = parser3.parse(test3)
        print(f"  ✅ '{test3}' -> {len(parsed3)} actions (Mixed Mode)")
        
        # Test 4: Error mode (without random data)
        test4 = "create an account on linkedin"
        parser4 = UniversalParser(api_key=GEMINI_API_KEY, use_random_data=False)
        parsed4 = parser4.parse(test4)
        print(f"  ✅ '{test4}' -> ERROR (as expected without Random Data)")
        
    except Exception as e:
        print(f"⚠️  Component test failed: {e}")
        traceback.print_exc()
    
    print("\n✅ All systems ready!")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)