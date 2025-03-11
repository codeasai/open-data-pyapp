import streamlit as st
import pandas as pd
from utils.data_utils import db, update_dataset
from utils.auth import check_user, login_page
from utils.ui_utils import toggle_theme
import os
import json

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ผู้ดูแลระบบ | ข้อมูลเปิดภาครัฐ",
    page_icon="⚙️",
    layout="wide"
)

# แสดงปุ่มสลับ theme
toggle_theme()

# ตรวจสอบการ login
if not check_user():
    login_page()
    st.stop()

# หัวข้อหลัก
st.title("⚙️ Administrator")
st.markdown("---")

# แสดงสถานะฐานข้อมูล
st.subheader("📊 สถานะฐานข้อมูล")

# เพิ่มการเปรียบเทียบจำนวนข้อมูล
st.write("#### 🔄 เปรียบเทียบจำนวนข้อมูล")

# สร้างตารางเปรียบเทียบ
comparison_data = {
    'แหล่งข้อมูล': ['JSON', 'SQLite'],
    'ชุดข้อมูล': [0, 0],
    'ทรัพยากร': [0, 0]
}

# นับจำนวนข้อมูลจาก JSON
json_files = {
    'datasets': 'data/datasets_info.json',
    'resources': 'data/dataset_files.json'
}

if all(os.path.exists(path) for path in json_files.values()):
    try:
        with open(json_files['datasets'], 'r', encoding='utf-8') as f:
            datasets = json.load(f)
            comparison_data['ชุดข้อมูล'][0] = len(datasets)
        with open(json_files['resources'], 'r', encoding='utf-8') as f:
            resources = json.load(f)
            comparison_data['ทรัพยากร'][0] = len(resources)
    except Exception as e:
        st.warning(f"ไม่สามารถอ่านไฟล์ JSON: {str(e)}")

# นับจำนวนข้อมูลจาก SQLite
if os.path.exists('data/database.sqlite'):
    try:
        cursor = db.conn.execute("SELECT COUNT(*) FROM datasets")
        comparison_data['ชุดข้อมูล'][1] = cursor.fetchone()[0]
        cursor = db.conn.execute("SELECT COUNT(*) FROM resources")
        comparison_data['ทรัพยากร'][1] = cursor.fetchone()[0]
    except Exception as e:
        st.warning(f"ไม่สามารถอ่านข้อมูลจาก SQLite: {str(e)}")

# แสดงตารางเปรียบเทียบ
df_comparison = pd.DataFrame(comparison_data)
st.table(df_comparison.style.apply(lambda x: ['background-color: #f0f2f6' if i % 2 else '' for i in range(len(x))]))

# แสดงสถานะไฟล์
col1, col2, col3 = st.columns(3)

with col1:
    # ตรวจสอบไฟล์ JSON
    json_exists = all(os.path.exists(path) for path in json_files.values())
    st.metric(
        "ไฟล์ JSON", 
        "พร้อมใช้งาน ✅" if json_exists else "ไม่พบไฟล์ ❌"
    )

with col2:
    # ตรวจสอบฐานข้อมูล SQLite
    db_exists = os.path.exists('data/database.sqlite')
    st.metric(
        "ฐานข้อมูล SQLite", 
        "พร้อมใช้งาน ✅" if db_exists else "ไม่พบไฟล์ ❌"
    )

with col3:
    # จำนวนข้อมูลในฐานข้อมูล
    if db_exists:
        cursor = db.conn.execute("SELECT COUNT(*) FROM datasets")
        dataset_count = cursor.fetchone()[0]
        cursor = db.conn.execute("SELECT COUNT(*) FROM resources")
        resource_count = cursor.fetchone()[0]
        st.metric("จำนวนข้อมูล", f"{dataset_count} ชุดข้อมูล, {resource_count} ทรัพยากร")
    else:
        st.metric("จำนวนข้อมูล", "ไม่สามารถนับได้")

# การจัดการข้อมูล
st.subheader("🔄 การจัดการข้อมูล")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Migrate ข้อมูลจาก JSON", use_container_width=True):
        with st.spinner("กำลัง migrate ข้อมูล..."):
            if db.migrate_from_json():
                st.success("Migrate ข้อมูลสำเร็จ")
            else:
                st.error("ไม่สามารถ migrate ข้อมูลได้")

with col2:
    if st.button("🗑️ ล้างฐานข้อมูล", use_container_width=True, type="secondary"):
        if st.warning("⚠️ การล้างฐานข้อมูลจะลบข้อมูลทั้งหมด คุณแน่ใจหรือไม่?"):
            try:
                db.close()  # ปิดการเชื่อมต่อก่อน
                if os.path.exists('data/database.sqlite'):
                    os.remove('data/database.sqlite')
                st.success("ล้างฐานข้อมูลสำเร็จ")
                st.info("กรุณารีโหลดหน้าเว็บเพื่อสร้างฐานข้อมูลใหม่")
            except Exception as e:
                st.error(f"ไม่สามารถล้างฐานข้อมูลได้: {str(e)}")

# แสดงข้อมูลในฐานข้อมูล
st.subheader("📋 ข้อมูลในฐานข้อมูล")

# เลือกตารางที่ต้องการดู
table = st.selectbox(
    "เลือกตารางข้อมูล",
    ["datasets", "resources"]
)

if db_exists:
    # ดึงข้อมูลจากตารางที่เลือก
    cursor = db.conn.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchall()
    
    # แสดงข้อมูลในรูปแบบตาราง
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("ไม่พบฐานข้อมูล")

# อัพเดทข้อมูลรายการ
st.subheader("🔄 อัพเดทข้อมูลรายการ")

# ดึง package_id ทั้งหมด
if db_exists:
    cursor = db.conn.execute("SELECT package_id, title FROM datasets")
    datasets = {row[0]: row[1] for row in cursor.fetchall()}
    
    # เลือก dataset ที่ต้องการอัพเดท
    selected_id = st.selectbox(
        "เลือกชุดข้อมูลที่ต้องการอัพเดท",
        options=list(datasets.keys()),
        format_func=lambda x: f"{x} - {datasets[x]}"
    )
    
    if st.button("🔄 อัพเดทข้อมูล", use_container_width=True):
        result = update_dataset(selected_id)
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)
else:
    st.warning("ไม่พบฐานข้อมูล")

# Footer
st.markdown("---")
st.caption("⚠️ หน้านี้สำหรับผู้ดูแลระบบเท่านั้น") 