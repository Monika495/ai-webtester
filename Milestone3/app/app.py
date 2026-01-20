from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sys
import os
from datetime import datetime

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import agents and database
from agent.basic_agent import BasicAgent
from agent.report_generator import ReportGenerator
from agent.database import Database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'novaqa-secret-key-2026-monika'

# Create reports directory
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Initialize components
agent = BasicAgent()
report_gen = ReportGenerator(reports_dir=REPORTS_DIR)
db = Database(db_path=os.path.join(PROJECT_ROOT, 'novaqa.db'))

# ==================== SESSION MANAGEMENT ====================

@app.before_request
def init_session():
    """Initialize session for guests"""
    if 'initialized' not in session:
        session['initialized'] = True
        session['guest_reports'] = []  # In-memory reports for guests

# ==================== AUTH ROUTES ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.verify_user(username, password)
        if user:
            # Clear guest session data
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
            # Clear guest session data
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
    return render_template("dashboard.html", username=username, logged_in=user_id is not None)

@app.route("/reports")
def reports():
    """Reports page"""
    user_id = session.get('user_id')
    
    if user_id:
        # Logged in user - fetch from database
        reports_list = db.get_reports(user_id=user_id)
    else:
        # Guest user - get from session only (in-memory)
        reports_list = session.get('guest_reports', [])
    
    return render_template("reports.html", reports=reports_list, logged_in=user_id is not None)

@app.route("/reports/<report_id>")
def report_detail(report_id):
    """Individual report"""
    user_id = session.get('user_id')
    
    if user_id:
        # Logged in user - fetch from database
        report = db.get_report_detail(report_id)
        if report:
            return render_template("report_detail.html", report=report)
        else:
            return "Report not found", 404
    else:
        # Guest user - find in session
        guest_reports = session.get('guest_reports', [])
        report = next((r for r in guest_reports if r.get('report_id') == report_id), None)
        
        if report:
            return render_template("report_detail.html", report=report)
        else:
            return "Report not found", 404

# ==================== API ENDPOINTS ====================

@app.route("/api/run-test", methods=["POST"])
def api_run_test():
    """Run test API"""
    try:
        if request.is_json:
            data = request.get_json()
            instruction = data.get("instruction", "").strip()
            headless = data.get("headless", True)
        else:
            instruction = request.form.get("instruction", "").strip()
            headless = request.form.get("headless", "true").lower() == "true"
        
        if not instruction:
            return jsonify({
                "success": False,
                "error": "Please provide a test instruction"
            }), 400
        
        print(f"[API] Processing instruction: {instruction}")
        
        # Process test
        result = agent.process_instructions(instruction, headless=headless)
        
        user_id = session.get('user_id')
        
        if user_id:
            # Logged in user - save to database
            report_id = db.save_report(result, user_id=user_id)
            print(f"[API] Logged-in user. Saved to database: {report_id}")
        else:
            # Guest user - store in session only (in-memory)
            report_id = f"GUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            execution = result.get("execution", [])
            total = len(execution)
            passed = len([s for s in execution if s.get("status") == "Passed"])
            failed = total - passed
            rate = (passed / total * 100) if total > 0 else 0
            status = "PASSED" if failed == 0 else "FAILED"
            
            guest_report = {
                "report_id": report_id,
                "instruction": result.get("instruction", ""),
                "total_steps": total,
                "passed_steps": passed,
                "failed_steps": failed,
                "success_rate": rate,
                "status": status,
                "execution": execution,
                "generated_code": result.get("generated_code", ""),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if 'guest_reports' not in session:
                session['guest_reports'] = []
            
            session['guest_reports'].append(guest_report)
            session.modified = True
            
            print(f"[API] Guest user. Stored in session: {report_id}")
        
        return jsonify({
            "success": True,
            "report_id": report_id,
            "instruction": result.get("instruction"),
            "parsed": result.get("parsed", []),
            "execution": result.get("execution", []),
            "generated_code": result.get("generated_code", "")
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}"
        }), 500

@app.route("/api/download-report/<format>", methods=["POST"])
def api_download_report(format):
    """Download report"""
    try:
        report_id = request.get_json().get("report_id")
        
        if not report_id:
            return jsonify({"success": False, "error": "No report ID provided"}), 400
        
        user_id = session.get('user_id')
        
        if user_id:
            # Logged in user - fetch from database
            report_data = db.get_report_detail(report_id)
        else:
            # Guest user - fetch from session
            guest_reports = session.get('guest_reports', [])
            report_data = next((r for r in guest_reports if r.get('report_id') == report_id), None)
        
        if not report_data:
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        if format == "html":
            filepath = report_gen.generate_html_report(report_data)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        
        elif format == "pdf":
            filepath = report_gen.generate_pdf_report(report_data)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        
        else:
            return jsonify({"success": False, "error": "Invalid format"}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/delete-report/<report_id>", methods=["DELETE"])
def api_delete_report(report_id):
    """Delete a report"""
    try:
        user_id = session.get('user_id')
        
        if user_id:
            # Logged in user - delete from database
            deleted = db.delete_report(report_id, user_id=user_id)
        else:
            # Guest user - delete from session
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
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== RUN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 NovaQA - Starting Server")
    print("=" * 60)
    print(f"📍 URL: http://localhost:5000")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📂 Reports Dir: {REPORTS_DIR}")
    print("🧠 AI-Powered Test Automation")
    print("👩‍💻 Developed by: Monika")
    print("💡 Guest Mode: Reports stored in memory only")
    print("💡 Logged-in Mode: Reports saved to database")
    print("=" * 60)
    
    app.run(debug=True, host="0.0.0.0", port=5000)