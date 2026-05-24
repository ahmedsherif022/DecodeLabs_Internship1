import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Load preprocessed student advisor database
DATA_FILE = 'student_advisor_data.json'
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        advisor_data = json.load(f)
    role_profiles = advisor_data.get('role_profiles', {})
    role_aliases = advisor_data.get('role_aliases', {})
    global_stats = advisor_data.get('global_stats', {})
    print(f"[*] Loaded knowledge base successfully: {len(role_profiles)} role profiles available.")
except Exception as e:
    print(f"[!] Error loading {DATA_FILE}: {e}")
    role_profiles = {}
    role_aliases = {}
    global_stats = {}

# Configure Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if api_key and api_key != "your_gemini_api_key_here":
    genai.configure(api_key=api_key)
    print("[*] Gemini API successfully configured.")
else:
    print("[!] Warning: GEMINI_API_KEY is not set. Chatbot will run in mock/error description mode.")

def find_matched_role(message):
    """
    Search message to detect if any developer career/role is mentioned.
    Uses aliases first (longest key first) and then canonical names to prevent partial overrides.
    """
    message_lower = message.lower()
    
    # Sort aliases by length descending
    sorted_aliases = sorted(role_aliases.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias in message_lower:
            return role_aliases[alias]
            
    # Sort role profiles canonical names by length descending
    sorted_roles = sorted(role_profiles.keys(), key=len, reverse=True)
    for role in sorted_roles:
        if role.lower() in message_lower:
            return role
            
    return None

@app.route('/')
def index():
    """Serve the single-page application static file."""
    return app.send_static_file('index.html')

@app.route('/student_advisor_data.json')
def get_advisor_data():
    """Endpoint to serve preprocessed JSON survey data directly to frontend."""
    return jsonify(advisor_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint for chatbot.
    Receives JSON body: { "message": "query", "history": [...] }
    Returns: { "reply": "AI response", "matched_role": "Data Scientist" or null }
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({"error": "Message is empty"}), 400

    # 1. Match career role
    matched_role = find_matched_role(message)
    
    # If no role matched in the current message, check if there was a matched role in the previous turns
    # to maintain contextual grounding, or fallback to general advice.
    # Note: frontend handles rendering the dashboard based on the matched_role.

    # 2. Build the system instruction for grounding
    system_instruction = (
        "You are the Student Career Advisor, a warm, professional, encouraging, and data-driven mentor.\n"
        "Your mission is to help students explore developer career paths by translating raw statistics into friendly, conversational, and practical advice.\n\n"
    )
    
    if matched_role:
        profile = role_profiles[matched_role]
        
        # Format key metrics to ensure perfect grounding
        salary = profile.get('salary', {})
        exp = profile.get('experience', {})
        
        stats_md = (
            f"### Official Survey Data for '{matched_role}':\n"
            f"- **Sample size**: Based on {profile.get('sample_count', 0):,} real developer responses from the 2024 survey.\n"
            f"- **Annual Salary (USD)**: Median is ${salary.get('median_usd', 0):,}/year. (25th percentile: ${salary.get('p25_usd', 0):,}/yr, 75th percentile: ${salary.get('p75_usd', 0):,}/yr).\n"
            f"- **Coding Experience**: Median is {exp.get('median_years', 0)} years. (25th percentile: {exp.get('p25_years', 0)} yrs, 75th percentile: {exp.get('p75_years', 0)} yrs).\n"
            f"- **Top 5 Languages Have Worked With**: {', '.join([x['name'] for x in profile.get('languages', [])[:5]])}.\n"
            f"- **Top 5 Languages Want To Learn**: {', '.join([x['name'] for x in profile.get('languages_wanted', [])[:5]])}.\n"
            f"- **Top 5 Databases**: {', '.join([x['name'] for x in profile.get('databases', [])[:5]])}.\n"
            f"- **Top 5 Web Frameworks**: {', '.join([x['name'] for x in profile.get('frameworks', [])[:5]])}.\n"
            f"- **Top 5 Platforms/Tools**: {', '.join([x['name'] for x in profile.get('platforms', [])[:5]])}.\n"
            f"- **Top 3 Learning Resources**: {', '.join([x['name'] for x in profile.get('learning_resources', [])[:3]])}.\n"
            f"- **Education Profile**: {', '.join([f'{k}' for k in list(profile.get('education', {}).keys())[:2]])}.\n\n"
        )
        
        system_instruction += (
            f"You are advising a student about a career as a **{matched_role}**.\n"
            f"CRITICAL GROUNDING RULES:\n"
            f"1. You MUST use the exact figures from the profile above. Never invent, extrapolate, or hallucinate stats (e.g. never state a salary or experience level different from the numbers listed above).\n"
            f"2. Cite the survey context nicely (e.g., 'According to real response data from {profile.get('sample_count', 0):,} professional developers...').\n"
            f"3. Explain these numbers in a encouraging, easily understandable way. Mention that a median salary of ${salary.get('median_usd', 0):,}/yr represents highly stable compensation.\n"
            f"4. Provide actionable, structured guidance on what languages and tools they should focus on first, utilizing the top resource categories (like online courses or books) to help them plan their studies.\n"
            f"Here is the context data to ground your advice:\n{stats_md}"
        )
    else:
        system_instruction += (
            "Greet the student warmly and introduce yourself as their Career Advisor.\n"
            "Explain that you have rich data-driven profiles on 19 different developer career paths compiled from 49,191 developers worldwide.\n"
            "Ask them conversational questions about what they enjoy doing (e.g. building visual designs, working with backend databases, mobile apps, artificial intelligence, or cloud infrastructure) to help narrow down their goals.\n"
            "Suggest a few roles they might be interested in, such as Data Scientist, Full-Stack Developer, or Cybersecurity Engineer, and explain they can click on any career or ask questions like 'How can I become a Back-End Developer?' to learn more."
        )

    # 3. Format history for Google API
    formatted_history = []
    for turn in history:
        role = turn.get('role')
        content = turn.get('content', '')
        if role and content:
            formatted_history.append({
                "role": "user" if role == "user" else "model",
                "parts": [content]
            })

    # 4. Invoke Gemini API
    if not api_key or api_key == "your_gemini_api_key_here":
        # Mock Response when API Key is missing, to allow local exploration
        mock_reply = (
            f"Hello! I am your **Student Career Advisor** chatbot. I see you are interested in exploring "
            f"developer paths! 🚀\n\n"
            f"Currently, my **Gemini API Key** is not configured in the `.env` file, so I cannot hold a full generative chat. "
            f"However, I successfully detected that you want to learn about **{matched_role if matched_role else 'careers'}**! "
            f"Look at the interactive **Career Dashboard** to your right to see the real-world statistical graphs and insights compiled from our developer survey database!"
        )
        return jsonify({
            "reply": mock_reply,
            "matched_role": matched_role
        })

    try:
        # Create GenerativeModel with System Instruction
        model = genai.GenerativeModel(
            model_name='gemini-3.5-flash',
            system_instruction=system_instruction
        )
        
        # Start chat session
        chat_session = model.start_chat(history=formatted_history)
        
        # Send current user message
        response = chat_session.send_message(message)
        
        return jsonify({
            "reply": response.text,
            "matched_role": matched_role
        })
        
    except Exception as e:
        error_msg = f"Gemini API Error: {str(e)}"
        print(f"[!] {error_msg}")
        return jsonify({
            "reply": f"Sorry, I encountered an error communicating with the Gemini API. {error_msg}\n\nBut check the interactive dashboard to the right for matching statistics!",
            "matched_role": matched_role
        }), 500

if __name__ == '__main__':
    # Load configuration port or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"[*] Starting Career Advisor Chatbot server on http://127.0.0.1:{port} (Debug: {debug})...")
    app.run(host='0.0.0.0', port=port, debug=debug)
