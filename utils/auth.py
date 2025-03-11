import streamlit as st
import streamlit.components.v1 as components
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import os

# Google OAuth settings
# ทดสอบด้วยค่าเริ่มต้น
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "192088934065-1ir6bfujj0ttb95echq0vev3d2ur8uv9.apps.googleusercontent.com"
)
ALLOWED_EMAILS = os.getenv(
    "ALLOWED_ADMIN_EMAILS",
    "cybergigz@gmail.com,anothainbth@gmail.com,wirojwm@gmail.com"
).split(",")

def check_user():
    """ตรวจสอบการ login ของผู้ใช้"""
    # ทดสอบ: อนุญาตให้เข้าถึงได้เสมอ
    return True

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