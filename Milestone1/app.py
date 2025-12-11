from flask import Flask, render_template, request
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.basic_agent import BasicAgent

app = Flask(__name__)
agent = BasicAgent()

@app.route("/")
def home():
    """Home page"""
    return render_template("home.html")

@app.route("/run_test", methods=["POST"])
def run_test():
    """Run test from instruction"""
    try:
        instruction = request.form.get("instruction", "").strip()
        
        if not instruction:
            return render_template(
                "testpage.html",
                error="Please enter an instruction",
                instruction="",
                parsed=[],
                generated_code="",
                execution=[]
            )
        
        headless = request.form.get("headless", "on") == "on"
        
        # Process instruction
        result = agent.process_instructions(instruction, headless=headless)
        
        return render_template(
            "testpage.html",
            instruction=result["instruction"],
            parsed=result["parsed"],
            generated_code=result["generated_code"],
            execution=result["execution"],
            error=None
        )
    
    except Exception as e:
        return render_template(
            "testpage.html",
            error=f"Error: {str(e)}",
            instruction=instruction if 'instruction' in locals() else "",
            parsed=[],
            generated_code="",
            execution=[]
        )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)