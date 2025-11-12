import streamlit as st

def authenticate():
    """Handle user authentication"""
    if st.session_state.get('logged_in'):
        return True
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background: white;
    }
    .stTextInput input { width: 100%; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("🔐 RGA Task Manager")
    st.subheader("Login Required")
    username = st.text_input("Username", value="Rohan.gunjal")
    password = st.text_input("Password", type="password", value="Cagunjal@168043")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            if username == "Rohan.gunjal" and password == "Cagunjal@168043":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials!")
    with col2:
        if st.button("Clear", use_container_width=True):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    return False
