import streamlit as st
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import os

# Google OAuth settings
GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
ALLOWED_EMAILS = st.secrets["ALLOWED_ADMIN_EMAILS"].split(",")

def check_user():
    """ตรวจสอบการ login ของผู้ใช้"""
    if 'user_token' not in st.session_state:
        return False
    
    try:
        # ตรวจสอบ token
        idinfo = id_token.verify_oauth2_token(
            st.session_state.user_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # ตรวจสอบว่าเป็น email ที่อนุญาตหรือไม่
        if idinfo['email'] in ALLOWED_EMAILS:
            return True
            
        st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return False
        
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return False

def login_page():
    """แสดงหน้า login"""
    st.title("🔐 เข้าสู่ระบบ")
    st.markdown("---")
    
    st.write("กรุณาเข้าสู่ระบบด้วยบัญชี Google ที่ได้รับอนุญาต")
    
    # Google Sign-In Button
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 2em;">
        <div id="googleSignIn"></div>
    </div>
    
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <script>
        function handleCredentialResponse(response) {
            window.parent.postMessage({
                type: 'streamlit:googleSignIn',
                token: response.credential
            }, '*');
        }
        
        window.onload = function () {
            google.accounts.id.initialize({
                client_id: '""" + GOOGLE_CLIENT_ID + """',
                callback: handleCredentialResponse
            });
            google.accounts.id.renderButton(
                document.getElementById("googleSignIn"),
                { theme: "outline", size: "large" }
            );
        }
    </script>
    """, unsafe_allow_html=True)
    
    # รับ token จาก JavaScript
    components.html("""
    <script>
        window.addEventListener('message', function(e) {
            if (e.data.type === 'streamlit:googleSignIn') {
                window.parent.postMessage({
                    type: 'streamlit:setSessionState',
                    key: 'user_token',
                    value: e.data.token
                }, '*');
            }
        });
    </script>
    """, height=0) 