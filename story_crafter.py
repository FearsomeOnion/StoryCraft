import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import textwrap


# Load environment variables
load_dotenv()


# Configure Gemini API
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API key not found. Set it in .env or Streamlit secrets")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')


# Story generation pipeline
def generate_story(prompt, keywords, mood, genre, temperature):
    """Generate a story using Gemini with enhanced prompt engineering"""
    # Create structured prompt template
    system_prompt = textwrap.dedent(f"""
    **Role**: Professional Story Generator
    **Task**: Create an engaging narrative based on user inputs
    
    **Requirements**:
    - Incorporate keywords: {', '.join(keywords)}
    - Maintain {mood} mood throughout
    - Perfectly fit {genre} genre
    - Clear story structure: beginning → conflict → resolution
    - Length: 300-500 words
    - Use vivid descriptions and natural dialogue
    
    **Story Structure**:
    1. Setup: Introduce characters and setting
    2. Conflict: Present central challenge
    3. Resolution: Deliver satisfying conclusion
    
    **User Prompt**:
    """)
    
    # Generate content with enhanced configuration
    try:
        SAFETY_MAP = {
            "Strict (Recommended)": {
                'HARASSMENT': 'BLOCK_MEDIUM_AND_ABOVE',
                'HATE_SPEECH': 'BLOCK_MEDIUM_AND_ABOVE',
                'SEXUAL': 'BLOCK_MEDIUM_AND_ABOVE',
                'DANGEROUS': 'BLOCK_MEDIUM_AND_ABOVE'
            },
            "Moderate": {
                'HARASSMENT': 'BLOCK_ONLY_HIGH',
                'HATE_SPEECH': 'BLOCK_ONLY_HIGH',
                'SEXUAL': 'BLOCK_ONLY_HIGH',
                'DANGEROUS': 'BLOCK_MEDIUM_AND_ABOVE'
            },
            "Creative Freedom": {
                'HARASSMENT': 'BLOCK_NONE',
                'HATE_SPEECH': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        }

        response = model.generate_content(
            system_prompt + prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048
            ),
            safety_settings = SAFETY_MAP[safety_level]
        )
        return response.text
    except Exception as e:
        st.error(f"Error generating story: {str(e)}")
        return None


# Story analysis functions
def analyze_story(story):
    """Provide analysis of generated story"""
    analysis_prompt = textwrap.dedent(f"""
    Analyze the following story and provide:
    1. Primary themes
    2. Character development score (1-5)
    3. Pacing assessment
    4. Emotional impact summary
    5. Potential improvements
    
    Story:
    {story}
    """)
    
    try:
        response = model.generate_content(analysis_prompt)
        return response.text
    except:
        return "Analysis unavailable"

def extract_key_elements(story):
    """Extract key story elements"""
    extraction_prompt = textwrap.dedent(f"""
    Extract from the story:
    - Main characters
    - Key locations
    - Central conflict
    - Resolution method
    - 3 most important symbols
    
    Return in JSON format with keys: characters, locations, conflict, resolution, symbols
    
    Story:
    {story}
    """)
    
    try:
        response = model.generate_content(extraction_prompt)
        return response.text
    except:
        return "Extraction failed"


# UI Components
def setup_sidebar():
    """Create sidebar controls"""
    with st.sidebar:
        st.header("Configuration")
        genre = st.selectbox(
            "Genre",
            ("Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Adventure"),
            index=1
        )
        mood = st.selectbox(
            "Mood",
            ("Whimsical", "Suspenseful", "Dark", "Hopeful", "Humorous", "Melancholic"),
            index=1
        )
        safety_level = st.sidebar.selectbox("Content Safety Level",
                                ["Strict (Recommended)", "Moderate", "Creative Freedom"], index=0)
        temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.1, 
                               help="Lower: more predictable, Higher: more creative")
        return genre, mood, temperature, safety_level

def setup_main_form(genre):
    """Create main input form"""
    with st.form("story_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            sci_fi_defaults = {
                "keywords": "spaceship, alien artifact, quantum drive",
                "prompt": "A lone astronaut discovers an ancient alien artifact that could change humanity's future..."
            }
            defaults = sci_fi_defaults if genre == "Sci-Fi" else {
                "keywords": "dragon, magic, ancient map",
                "prompt": "A young explorer discovers a hidden realm..."
            }
            
            keywords = st.text_input("Keywords (comma separated)", defaults["keywords"])
            prompt = st.text_area("Story Prompt", defaults["prompt"], height=150)
        
        with col2:
            st.subheader("Advanced Options")
            st.checkbox("Include story analysis", value=False, key="analysis")
            st.checkbox("Extract story elements", value=False, key="extraction")
            st.checkbox("Generate sequel hook", value=True, key="sequel")
        
        return st.form_submit_button("Craft My Story"), keywords, prompt


# Main application
st.set_page_config(page_title="StoryCrafter", page_icon="logo.png", layout="wide")

# Initialize Gemini
model = configure_gemini()


# Header
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("logo.png", width=60)
with col2:
    st.title("StoryCrafter")
st.subheader("Powered by Gemini 1.5 Flash")

# Setup UI components
genre, mood, temperature, safety_level = setup_sidebar()
generate_button, keywords, prompt = setup_main_form(genre)

# Story generation and display
if generate_button:
    with st.spinner("🧙‍♂️ Weaving your story with AI magic..."):
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        
        if not prompt:
            st.warning("Please enter a story prompt")
            st.stop()
            
        story = generate_story(prompt, keyword_list, mood, genre, temperature)
        
        if story:
            st.success("✨ Your Story is Ready!")
            st.divider()
            
            # Display story
            st.subheader(f"{genre} Story: {mood.capitalize()} Journey")
            with st.expander("Read Your Story", expanded=True):
                st.write(story)
            
            # Analysis section
            if st.session_state.analysis:
                st.divider()
                st.subheader("📊 Story Analysis")
                analysis = analyze_story(story)
                st.write(analysis)
            
            # Extraction section
            if st.session_state.extraction:
                st.divider()
                st.subheader("🔍 Key Story Elements")
                elements = extract_key_elements(story)
                st.write(elements)
            
            # Sequel hook
            if st.session_state.sequel:
                st.divider()
                st.subheader("🔮 Sequel Hook")
                sequel_prompt = f"Create a sequel hook for this story: {story[:500]}..."
                try:
                    sequel = model.generate_content(sequel_prompt)
                    st.write(sequel.text)
                except:
                    st.warning("Could not generate sequel hook")
            
            # Download button
            st.download_button(
                label="Download Story",
                data=story,
                file_name=f"{genre}_{mood}_story.txt",
                mime="text/plain"
            )