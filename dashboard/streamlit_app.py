"""
Streamlit Dashboard - Main Entry Point
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Solana ML Scanner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main dashboard page"""
    
    st.title("🤖 Solana ML Scanner Dashboard")
    st.markdown("---")
    
    st.info("🚧 Dashboard is under construction. Check back soon!")
    
    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Capital", "€100.00", "0%")
    
    with col2:
        st.metric("Win Rate", "0%", "0%")
    
    with col3:
        st.metric("Alerts Today", "0")
    
    with col4:
        st.metric("ML Accuracy", "60%", "Baseline")
    
    st.markdown("---")
    st.info("ℹ️  Full dashboard will be available in the next update!")

if __name__ == "__main__":
    main()
