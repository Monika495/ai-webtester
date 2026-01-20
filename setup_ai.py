"""
Setup and test script for NovaQA AI integration
Final Stable Version (Windows + venv compatible)
"""

import os
import sys

print("=" * 70)
print("🚀 NovaQA AI Setup & Testing (FINAL HYBRID VERSION)")
print("=" * 70)

# ==========================================================
# 1️⃣ CHECK REQUIRED PACKAGES
# ==========================================================
print("\n" + "=" * 60)
print("📦 Checking Required Packages...")
print("=" * 60)

packages = {
    "google.genai": "google-genai",
    "flask": "flask",
    "playwright": "playwright"
}

missing = []

for import_name, pip_name in packages.items():
    try:
        __import__(import_name)
        print(f"✅ {pip_name}")
    except ImportError:
        print(f"❌ {pip_name} - NOT INSTALLED")
        missing.append(pip_name)

if missing:
    print("\n❌ Missing packages:", ", ".join(missing))
    print("\n💡 Install using:")
    print(f"   python -m pip install {' '.join(missing)}")
    sys.exit(1)

print("\n✅ All required packages are installed!")

# ==========================================================
# 2️⃣ CHECK GEMINI API KEY
# ==========================================================
print("\n" + "=" * 60)
print("🔑 Checking Gemini API Key...")
print("=" * 60)

api_key = os.getenv("GEMINI_API_KEY")
ai_available = False

if not api_key:
    print("⚠️ GEMINI_API_KEY not found")
    print("⚠️ Running in REGEX FALLBACK mode")
else:
    print(f"✅ API Key found: {api_key[:8]}...")

    try:
        from google import genai

        print("🧪 Testing Gemini API connection...")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Reply only with the word OK"
        )

        if response.text and "OK" in response.text.upper():
            print("✅ Gemini API is WORKING")
            ai_available = True
        else:
            print("⚠️ Unexpected response:", response.text)

    except Exception as e:
        print("❌ Gemini API test failed")
        print("   Reason:", str(e)[:120])
        print("⚠️ Falling back to REGEX mode")

# ==========================================================
# 3️⃣ TEST INSTRUCTION PARSER
# ==========================================================
print("\n" + "=" * 60)
print("🧪 Testing Instruction Parser...")
print("=" * 60)

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

try:
    from agent.ai_parser_agent import InstructionParser

    parser = InstructionParser()
    print("✅ InstructionParser loaded")

    test_inputs = [
        "open google.com and search artificial intelligence",
        "go to youtube and search python tutorial",
        "visit wikipedia.org"
    ]

    print(f"\nRunning {len(test_inputs)} test instructions...")
    print("-" * 60)

    for i, text in enumerate(test_inputs, 1):
        print(f"\n{i}. Instruction: {text}")
        actions = parser.parse(text)

        if not actions:
            print("   ❌ No actions parsed")
        else:
            print(f"   ✅ {len(actions)} action(s):")
            for j, act in enumerate(actions, 1):
                print(f"      {j}. {act.get('action')} → {act.get('description', '')}")

    print("\n" + "=" * 60)
    if parser.use_ai:
        print("🎉 SUCCESS! NovaQA running in AI MODE (Gemini)")
    else:
        print("✅ SUCCESS! NovaQA running in FALLBACK MODE (Regex)")
    print("=" * 60)

except ImportError as e:
    print("❌ InstructionParser not found")
    print("   Check file: agent/ai_parser_agent.py")
    print("   Error:", e)
    sys.exit(1)

except Exception as e:
    print("❌ Parser test failed")
    print(str(e))
    sys.exit(1)

# ==========================================================
# FINAL MESSAGE
# ==========================================================
print("\n" + "=" * 70)
print("🎯 SETUP COMPLETE! NovaQA is READY 🚀")
print("=" * 70)

print("\n▶ Next Steps:")
print("   1. Run server: python app/app.py")
print("   2. Open: http://localhost:5000")
print("   3. Enter natural language test cases")
