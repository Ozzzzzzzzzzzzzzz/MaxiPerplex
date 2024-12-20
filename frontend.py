import streamlit as st
import requests
import json
import time

# Configure the page with a wider layout and custom theme
st.set_page_config(
    page_title="AI Search Engine",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        padding: 1rem;
        font-size: 1.1rem;
    }
    .search-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .result-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    h1 {
        color: #1e88e5;
        font-size: 3rem !important;
        margin-bottom: 1rem !important;
    }
    .source-link {
        text-decoration: none;
        color: #1e88e5;
        padding: 0.5rem;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    .source-link:hover {
        background-color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

# Create two columns for layout
col1, col2, col3 = st.columns([1,3,1])

with col2:
    # Header section
    st.markdown("<h1 style='text-align: center;'>🔎 AI Search Engine</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #666; margin-bottom: 2rem;'>
        Get comprehensive answers powered by AI and real-time web search
    </div>
    """, unsafe_allow_html=True)

    # Search input and button
    query = st.text_input(
        "",  # Remove label
        placeholder="What would you like to know?",
        key="search_input"
    )

    # Search button
    if st.button("🔍 Search", type="primary"):
        if query:
            # Progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Simulate progress while actually searching
            try:
                status_text.text("🔍 Searching the web...")
                progress_bar.progress(30)
                time.sleep(0.5)
                
                # Make request to your FastAPI backend
                response = requests.post(
                    "http://localhost:8000/search",
                    headers={"Content-Type": "application/json"},
                    json={"query": query}
                )
                
                progress_bar.progress(60)
                status_text.text("🤖 Analyzing results...")
                time.sleep(0.5)
                
                if response.status_code == 200:
                    data = response.json()
                    progress_bar.progress(100)
                    status_text.text("✨ Results ready!")
                    time.sleep(0.5)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display the answer
                    st.markdown("### 📝 Answer")
                    st.markdown(data["answer"])
                    
                    # Display sources
                    st.markdown("### 🔗 Sources")
                    for i, source in enumerate(data["sources"], 1):
                        st.markdown(f"{i}. [{source}]({source})")
                else:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Error: {response.text}")
            
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query.")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown(
        "<div style='text-align: center; color: #666;'>Powered by Linkup and OpenAI</div>",
        unsafe_allow_html=True
    )