import streamlit as st
import google.generativeai as genai
import time
import json
import re
import os
import base64
import concurrent.futures
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from huggingface_hub import InferenceClient

# Load env variables
load_dotenv()

# Setup Streamlit page config
st.set_page_config(page_title="Dungeon Echoes", page_icon="📜", layout="centered", initial_sidebar_state="collapsed")

# -----------------
# 1. CSS & THEME
# -----------------
st.markdown("""
<style>
    /* Full-Screen Background Image */
    .stApp {
        background: linear-gradient(rgba(10, 10, 10, 0.7), rgba(0, 0, 0, 0.95)), url('https://image.pollinations.ai/prompt/dark%20fantasy%20landscape%20epic%20scale?width=1000&height=1000&nologo=true');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .mobile-container {
        width: 100%;
        max-width: 500px;
        margin: 0 auto;
        padding: 5px;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }

    /* Streamlit Global Alignment */
    .block-container {
        max-width: 500px !important;
        padding-top: 2rem !important;
    }
    div[data-testid="stBottomBlockContainer"] {
        max-width: 500px !important;
        margin: 0 auto !important;
    }

    /* Unified Game Card Container */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px #00F2FF; }
        50% { box-shadow: 0 0 25px #00F2FF; }
        100% { box-shadow: 0 0 10px #00F2FF; }
    }
    .unified-card {
        width: 100%;
        max-width: 500px;
        border: 2px solid #00F2FF;
        border-radius: 10px;
        animation: pulseGlow 3s infinite;
        overflow: hidden;
        margin-bottom: 20px; /* Space for floating input */
        display: flex;
        flex-direction: column;
        position: relative;
    }

    /* Hero Image Container */
    .hero-image-container {
        width: 100%;
        aspect-ratio: 1 / 1;
        background: #111;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
    }

    .hero-image-container img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
    }

    .spinner-text {
        color: #00F2FF;
        font-family: monospace;
        font-size: 1.2rem;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.5; text-shadow: 0 0 5px #00F2FF; }
        50% { opacity: 1; text-shadow: 0 0 15px #00F2FF; }
        100% { opacity: 0.5; text-shadow: 0 0 5px #00F2FF; }
    }

    /* Game Over Overlays */
    .victory-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(255, 215, 0, 0.2);
        box-shadow: inset 0 0 80px rgba(255, 215, 0, 0.6);
        border: 4px solid #FFD700;
        z-index: 20;
        display: flex;
        justify-content: center;
        align-items: center;
        pointer-events: none;
    }
    .defeat-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(139, 0, 0, 0.3);
        box-shadow: inset 0 0 80px rgba(139, 0, 0, 0.8);
        border: 4px solid #8B0000;
        z-index: 20;
        display: flex;
        justify-content: center;
        align-items: center;
        pointer-events: none;
    }
    .game-over-text {
        font-size: 4rem;
        font-family: 'Georgia', serif;
        font-weight: bold;
        text-shadow: 0 0 10px #000, 0 0 20px #000;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 5px;
    }
    .victory-text { color: #FFD700; }
    .defeat-text { color: #FF2222; }

    /* Diegetic HUD Overlay */
    .floating-hud {
        position: absolute;
        top: 15px; 
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 8px 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 10;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }

    .stat-mini-row {
        display: flex;
        align-items: center;
        width: 48%;
    }

    .stat-bar-mini-bg {
        flex-grow: 1;
        background: rgba(255,255,255,0.1);
        height: 4px; /* Ultra-thin */
        border-radius: 2px;
        margin: 0 8px;
        overflow: hidden;
    }
    .health-bar-mini-fill {
        background: #FF0055;
        box-shadow: 0 0 8px #FF0055;
        height: 100%;
        transition: width 0.3s;
    }
    .xp-bar-mini-fill {
        background: #00F2FF;
        box-shadow: 0 0 8px #00F2FF;
        height: 100%;
        transition: width 0.3s;
    }
    .hud-label {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: bold;
        font-size: 0.75rem;
        text-shadow: 1px 1px 2px #000;
    }

    /* Story Text Box */
    .story-box {
        background: #EAE0C8; /* Parchment color */
        padding: 18px;
        color: #2C2A24;
        font-size: 1.05rem;
        line-height: 1.6;
        font-family: 'Georgia', 'Merriweather', serif;
        box-shadow: inset 0 0 15px rgba(139, 90, 43, 0.2), 0 -4px 10px rgba(0,0,0,0.4);
        height: auto;
        max-height: 40vh; /* Scrollable constraints */
        overflow-y: auto;
        z-index: 5;
    }

    .story-box::-webkit-scrollbar {
        width: 6px;
    }
    .story-box::-webkit-scrollbar-track {
        background: rgba(139, 90, 43, 0.1); 
    }
    .story-box::-webkit-scrollbar-thumb {
        background: #8B5A2B; 
        border-radius: 3px;
    }
    
    .user-box {
        width: 100%;
        max-width: 500px;
        text-align: right;
        margin-bottom: 10px;
        color: #A9A9A9;
        font-style: italic;
        padding-right: 15px;
        border-right: 3px solid #FF0055;
        font-family: 'Georgia', 'Merriweather', serif;
    }

    /* Inventory Slots Grid */
    .inventory-drawer {
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px dashed rgba(139, 90, 43, 0.4);
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        justify-content: flex-start;
    }
    
    .inventory-slot {
        width: 38px;
        height: 38px;
        background: rgba(0,0,0,0.05);
        border: 1px solid rgba(139, 90, 43, 0.5);
        border-radius: 4px;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        font-size: 1.2rem;
    }
    
    .inventory-title {
        width: 100%;
        font-size: 0.75rem;
        color: #8B5A2B;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: bold;
        margin-bottom: 2px;
    }
    
</style>
""", unsafe_allow_html=True)

# -----------------
# 2. STATE LOGIC
# -----------------
if "started" not in st.session_state:
    st.session_state.started = False
if "health" not in st.session_state:
    st.session_state.health = 100
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "image_url" not in st.session_state:
    st.session_state.image_url = "https://image.pollinations.ai/prompt/medieval%20dungeon%20dark%20fantasy%20oil%20painting?width=450&height=450&nologo=true"
if "history" not in st.session_state:
    st.session_state.history = []
if "realm" not in st.session_state:
    st.session_state.realm = "The Whispering Dungeons"
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "is_game_over" not in st.session_state:
    st.session_state.is_game_over = False
if "game_result" not in st.session_state:
    st.session_state.game_result = "ongoing"

# -----------------
# 3. LLM & FLUX INITIALIZATION
# -----------------
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

genai.configure(api_key=GEMINI_KEY)

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "response_mime_type": "application/json",
    "response_schema": {
        "type": "OBJECT",
        "properties": {
            "narrative": {"type": "STRING"},
            "image_prompt": {"type": "STRING"},
            "health_delta": {"type": "INTEGER"},
            "xp_gain": {"type": "INTEGER"},
            "new_items": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            },
            "is_game_over": {"type": "BOOLEAN"},
            "game_result": {"type": "STRING"}
        },
        "required": ["narrative", "image_prompt", "health_delta", "xp_gain", "new_items", "is_game_over", "game_result"]
    }
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

model = genai.GenerativeModel("gemini-2.5-flash", generation_config=generation_config, safety_settings=safety_settings)

def generate_image(prompt):
    if not HF_TOKEN:
        return f"https://image.pollinations.ai/prompt/medieval%20fantasy%20dark?width=450&height=450&nologo=true"
        
    client = InferenceClient(token=HF_TOKEN)
    try:
        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print(f"HF Error: {e}")
        safe_prompt = prompt.replace(" ", "%20")[:150]
        return f"https://image.pollinations.ai/prompt/{safe_prompt}?width=450&height=450&nologo=true"

# -----------------
# 4. APP LOGIC
# -----------------

def build_card_html(narrative_text=None):
    hp_pct = (st.session_state.health / 100.0) * 100
    xp_pct = min((st.session_state.xp / 100.0) * 100, 100)
    
    hud_html = f"""<div class="floating-hud">
  <div class="stat-mini-row">
    <span class="hud-label" style="color:#FF0055;">HP {st.session_state.health}</span>
    <div class="stat-bar-mini-bg"><div class="health-bar-mini-fill" style="width: {hp_pct}%;"></div></div>
  </div>
  <div class="stat-mini-row">
    <div class="stat-bar-mini-bg"><div class="xp-bar-mini-fill" style="width: {xp_pct}%;"></div></div>
    <span class="hud-label" style="color:#00F2FF;">XP {st.session_state.xp}</span>
  </div>
</div>"""

    overlay_html = ""
    if st.session_state.is_game_over:
        if st.session_state.game_result == 'victory':
            overlay_html = '<div class="victory-overlay"><div class="game-over-text victory-text">VICTORY</div></div>'
        else:
            overlay_html = '<div class="defeat-overlay"><div class="game-over-text defeat-text">DEFEAT</div></div>'

    unified_html = '<div class="unified-card">'
    
    if st.session_state.image_bytes or st.session_state.image_url:
        if st.session_state.image_bytes:
            b64_img = base64.b64encode(st.session_state.image_bytes).decode()
            img_src = f"data:image/png;base64,{b64_img}"
        else:
            img_src = st.session_state.image_url
            
        unified_html += f'''<div class="hero-image-container">
{overlay_html}
<img src="{img_src}" />
{hud_html}
</div>'''
    else:
        unified_html += f'''<div class="hero-image-container">
{overlay_html}
<div class="spinner-text">Summoning Vision...</div>
{hud_html}
</div>'''

    if st.session_state.history or narrative_text is not None:
        unified_html += '<div class="story-box">'
        
        if narrative_text is not None:
            unified_html += narrative_text
        else:
            dm_msgs = [m for m in st.session_state.history if m["role"] == "dm"]
            if dm_msgs:
                unified_html += dm_msgs[-1]["text"]
            
        unified_html += '<div class="inventory-drawer"><div class="inventory-title">📦 Inventory &nbsp;&nbsp;|&nbsp;&nbsp; Turn: ' + str(st.session_state.turn_count) + '</div>'
        max_slots = 6
        items = st.session_state.inventory
        for i in range(max_slots):
            if i < len(items):
                unified_html += f'<div class="inventory-slot" title="{items[i]}">🔮</div>'
            else:
                unified_html += '<div class="inventory-slot" style="opacity:0.3;">🛡️</div>'
                
        unified_html += '</div></div>' # Close drawer, close story box
        
    unified_html += '</div>' # Close unified card
    return unified_html

def process_turn(action, card_placeholder=None):
    st.session_state.turn_count += 1
    
    recent_dm_history = [m["text"] for m in st.session_state.history if m["role"] == "dm"][-3:]
    recent_context_str = " ".join(recent_dm_history) if recent_dm_history else "You have just entered the realm."

    prompt_context = f"""
    Current stats: HP={st.session_state.health}, XP={st.session_state.xp}
    Inventory: {', '.join(st.session_state.inventory) if st.session_state.inventory else 'None'}
    Realm: {st.session_state.realm}
    Turn Count: {st.session_state.turn_count}
    
    Recent Story Context (What just happened): "{recent_context_str}"
    
    User Action: "{action}"
    
    You are an experienced, grounded Tabletop RPG Dungeon Master running a classic High Fantasy / Medieval D&D game. 
    Respond ONLY in valid JSON. Do not use futuristic or overly poetic language.
    
    Monitor the turn_count. At turn 12, initiate the climax/Final Boss encounter. 
    If the player survives to turn 15, trigger a 'victory' game_result and set is_game_over to true. 
    If HP reaches 0 or below, trigger a 'defeat' game_result and set is_game_over to true. 
    Otherwise, game_result is 'ongoing' and is_game_over is false.
    
    Image Prompt rules: Focus closely on "Medieval Fantasy Art, oil painting style, D&D character art, atmospheric lighting".
    
    Narrative rules (Keep under 60 words total):
    1. 2-3 sentences of atmospheric description.
    2. 1 sentence describing a clear immediate problem or opportunity.
    3. End with a direct question to the player ("What do you do?").
    """
    
    try:
        # Step 1: Execute Gemini Request
        response = model.generate_content(prompt_context)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        raw_text = re.sub(r',\s*}', '}', raw_text)
        raw_text = re.sub(r',\s*]', ']', raw_text)
        
        data = json.loads(raw_text)
        
        # Apply State
        st.session_state.health += data.get("health_delta", 0)
        st.session_state.health = min(max(st.session_state.health, 0), 100)
        st.session_state.xp += data.get("xp_gain", 0)
        
        if data.get("is_game_over"):
            st.session_state.is_game_over = True
            st.session_state.game_result = data.get("game_result", "defeat")
            
        if st.session_state.health <= 0:
            st.session_state.is_game_over = True
            st.session_state.game_result = "defeat"
            
        if isinstance(data.get("new_items"), list):
            st.session_state.inventory.extend(data["new_items"])
            
        st.session_state.history.append({"role": "dm", "text": data["narrative"]})
        
        # Step 2: Image Prompt Modification
        enhanced_image_prompt = data["image_prompt"]
        if st.session_state.turn_count >= 12:
            enhanced_image_prompt += ", epic scale, intense boss battle, cinematic lighting, final confrontation"

        # Step 3: Fetch Image via ThreadPoolExecutor
        # Check if we should render streaming or not
        st.session_state.image_bytes = None
        st.session_state.image_url = None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_img = executor.submit(generate_image, enhanced_image_prompt)
            
            narrative = data["narrative"]
            if card_placeholder:
                typed_text = ""
                sleep_time = min(0.04, 2.0 / max(len(narrative), 1))
                for char in narrative:
                    typed_text += char
                    card_placeholder.markdown(build_card_html(narrative_text=typed_text), unsafe_allow_html=True)
                    time.sleep(sleep_time)

            img_res = future_img.result()

        if isinstance(img_res, str):
            st.session_state.image_url = img_res
            st.session_state.image_bytes = None
        else:
            st.session_state.image_bytes = img_res
            st.session_state.image_url = None
            
        if card_placeholder:
            card_placeholder.markdown(build_card_html(), unsafe_allow_html=True)
            
    except Exception as e:
        recovery_text = f"The weave of magic tangles, disrupting the scrying pool: **{e}**"
        st.session_state.history.append({"role": "dm", "text": recovery_text})
        st.session_state.image_bytes = None
        st.session_state.image_url = "https://image.pollinations.ai/prompt/shattered%20crystal%20ball%20dark%20medieval?width=450&height=450&nologo=true"
        print(f"Error Recovered: {e}")
        if card_placeholder:
            card_placeholder.markdown(build_card_html(), unsafe_allow_html=True)

# -----------------
# 5. UI RENDER
# -----------------
st.markdown('<div class="mobile-container">', unsafe_allow_html=True)

def reset_game():
    for key in ["started", "turn_count", "is_game_over", "game_result", "image_bytes", "image_url"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.health = 100
    st.session_state.xp = 0
    st.session_state.inventory = []
    st.session_state.history = []

if not st.session_state.started:
    st.markdown('''
    <style>
    .landing-title {
        font-size: 4.5rem;
        font-family: 'Georgia', serif;
        color: #00F2FF;
        text-shadow: 0 0 10px #00F2FF, 0 0 20px #00F2FF;
        text-align: center;
        margin-top: 10vh;
        margin-bottom: 5px;
    }
    .landing-subtitle {
        font-size: 1.5rem;
        font-family: 'Georgia', serif;
        color: #FFD700;
        font-style: italic;
        text-align: center;
        margin-bottom: 40px;
    }
    div.stButton > button {
        background: rgba(0, 242, 255, 0.1) !important;
        border: 2px solid #00F2FF !important;
        color: #00F2FF !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);
        padding: 15px 30px !important;
        font-family: 'Georgia', serif;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 2px;
        transition: 0.3s;
        margin-top: 20px;
    }
    div.stButton > button:hover {
        background: rgba(0, 242, 255, 0.3) !important;
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.8);
        color: #FFF !important;
    }
    /* Glassmorphic Selectbox styling attempt */
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 242, 255, 0.5) !important;
        color: #FFF !important;
    }
    </style>
    <div class="landing-title">Dungeon Echoes</div>
    <div class="landing-subtitle">Select Your Adventure</div>
    ''', unsafe_allow_html=True)
    
    realm_options = [
        "The Whispering Dungeons",
        "Coming Soon: Neon Nexus",
        "Coming Soon: Star-Bound Void"
    ]
    
    selected_realm = st.selectbox("Choose a World:", realm_options, index=0)
    
    if st.button("BEGIN THE JOURNEY", use_container_width=True):
        if "Coming Soon" in selected_realm:
            st.error("This realm is sealed. Choose another path.")
        else:
            st.session_state.started = True
            st.session_state.realm = selected_realm
            with st.spinner("Casting Vision..."):
                process_turn(f"I enter {selected_realm}.")
            st.rerun()

else:
    # 1. User Message
    user_box_placeholder = st.empty()
    if st.session_state.history and not st.session_state.is_game_over:
        user_msgs = [m for m in st.session_state.history if m["role"] == "user"]
        if user_msgs:
            user_box_placeholder.markdown(f'<div class="user-box">&gt; {user_msgs[-1]["text"]}</div>', unsafe_allow_html=True)

    # 2. Render Card
    card_placeholder = st.empty()
    card_placeholder.markdown(build_card_html(), unsafe_allow_html=True)
    
    # 4. Input OR Restart Game
    if st.session_state.is_game_over:
        if st.button("RESTART ADVENTURE", use_container_width=True, type="primary"):
            reset_game()
            st.rerun()
    else:
        action = st.chat_input("What is your next move?")
        if action:
            st.session_state.history.append({"role": "user", "text": action})
            user_box_placeholder.markdown(f'<div class="user-box">&gt; {action}</div>', unsafe_allow_html=True)
            
            with st.spinner("Weaving Fate..."):
                process_turn(action, card_placeholder)
                
            if st.session_state.is_game_over:
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
