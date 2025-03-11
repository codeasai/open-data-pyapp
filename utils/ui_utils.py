import streamlit as st
import time
from .data_utils import update_dataset
import json

def create_action_cell(row):
    """สร้างปุ่มกดในตาราง"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f'<a href="{row["url"]}" target="_blank">🔗</a>', unsafe_allow_html=True)
    with col2:
        if st.button("Load", key=f"load_{row['package_id']}", help=f"อัพเดทข้อมูล"):
            result = update_dataset(row['package_id'])
            st.toast(result)
            if "✅" in result:
                time.sleep(1)
                st.rerun()

def apply_custom_css():
    """ใส่ CSS สำหรับตกแต่งหน้าเว็บ"""
    st.markdown("""
    <style>
    /* ปรับแต่งการแสดงผลไฟล์ */
    .file-type {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 8px;
        background-color: rgba(0, 0, 0, 0.05);
        white-space: nowrap;
    }

    /* ปรับแต่งลิงก์ */
    [data-testid="column"]:nth-child(4) a {
        text-decoration: none;
        color: inherit;
        transition: all 0.2s;
    }

    [data-testid="column"]:nth-child(4) a:hover {
        background-color: rgba(0, 0, 0, 0.1);
    }

    /* ปรับแต่งข้อความประเภทไฟล์ */
    .format-text {
        font-size: 0.9em;
        color: #666;
    }

    /* ... rest of your CSS ... */
    </style>
    """, unsafe_allow_html=True)

def create_ranking_selector(row):
    """สร้าง dropdown สำหรับเลือก ranking"""
    ranking_options = {
        "⭐⭐⭐⭐": 4,
        "⭐⭐⭐": 3,
        "⭐⭐": 2,
        "⭐": 1,
        "ไม่มี": 0
    }
    
    # อ่านค่า ranking ปัจจุบัน
    current_ranking = 0
    try:
        with open('data/dataset_files.json', 'r', encoding='utf-8') as f:
            all_files = json.load(f)
            for file in all_files:
                if file['dataset_id'] == row['package_id']:
                    current_ranking = file.get('ranking', 0)
                    break
    except:
        pass
    
    # แปลงค่า ranking เป็นตัวเลือก
    current_option = next(
        (k for k, v in ranking_options.items() if v == current_ranking),
        "ไม่มี"
    )
    
    # สร้าง dropdown
    selected = st.selectbox(
        "Ranking",
        options=list(ranking_options.keys()),
        index=list(ranking_options.keys()).index(current_option),
        key=f"rank_{row['package_id']}"
    )
    
    # เมื่อมีการเปลี่ยนแปลง
    if selected != current_option:
        from .data_utils import update_dataset_ranking
        if update_dataset_ranking(row['package_id'], ranking_options[selected]):
            st.toast(f"✅ อัพเดท ranking เป็น {selected} สำเร็จ")
            time.sleep(1)
            st.rerun()
        else:
            st.toast("❌ ไม่สามารถอัพเดท ranking ได้") 