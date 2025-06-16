import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.data_utils import db
from utils.ui_utils import toggle_theme
from utils.auth import check_user, login_page
import json

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="จัดการหน่วยงาน | ข้อมูลเปิดภาครัฐ",
    page_icon="🏢",
    layout="wide"
)

# แสดงปุ่มสลับ theme
toggle_theme()

# ตรวจสอบการ login
if not check_user():
    login_page()
    st.stop()

st.title("🏢 จัดการหน่วยงาน")
st.markdown("---")

# ฟังก์ชันสำหรับดึงข้อมูลหน่วยงานจาก SQLite
def get_all_organizations():
    try:
        # ดึงข้อมูลหน่วยงานทั้งหมดจากฐานข้อมูล
        cursor = db.conn.execute("""
            SELECT DISTINCT organization as name,
                   COUNT(*) as dataset_count,
                   MIN(package_id) as deptId
            FROM datasets
            GROUP BY organization
            ORDER BY name
        """)
        
        # แปลงเป็น DataFrame
        df = pd.DataFrame(cursor.fetchall(), columns=['name', 'dataset_count', 'deptId'])
        
        # เพิ่มคอลัมน์ประเภทหน่วยงาน
        df['org_type'] = df['name'].apply(get_org_type)
        
        # เพิ่มคอลัมน์จังหวัด
        df['province'] = df['name'].apply(get_province)
        
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
        return pd.DataFrame()

# รายชื่อจังหวัดในประเทศไทย
THAI_PROVINCES = [
    'กรุงเทพมหานคร', 'กระบี่', 'กาญจนบุรี', 'กาฬสินธุ์', 'กำแพงเพชร', 'ขอนแก่น', 'จันทบุรี', 'ฉะเชิงเทรา', 'ชลบุรี',
    'ชัยนาท', 'ชัยภูมิ', 'ชุมพร', 'เชียงราย', 'เชียงใหม่', 'ตรัง', 'ตราด', 'ตาก', 'นครนายก', 'นครปฐม', 'นครพนม',
    'นครราชสีมา', 'นครศรีธรรมราช', 'นครสวรรค์', 'นนทบุรี', 'นราธิวาส', 'น่าน', 'บึงกาฬ', 'บุรีรัมย์', 'ปทุมธานี',
    'ประจวบคีรีขันธ์', 'ปราจีนบุรี', 'ปัตตานี', 'พระนครศรีอยุธยา', 'พังงา', 'พัทลุง', 'พิจิตร', 'พิษณุโลก', 'เพชรบุรี',
    'เพชรบูรณ์', 'แพร่', 'ภูเก็ต', 'มหาสารคาม', 'มุกดาหาร', 'แม่ฮ่องสอน', 'ยโสธร', 'ยะลา', 'ร้อยเอ็ด', 'ระนอง',
    'ระยอง', 'ราชบุรี', 'ลพบุรี', 'ลำปาง', 'ลำพูน', 'เลย', 'ศรีสะเกษ', 'สกลนคร', 'สงขลา', 'สตูล', 'สมุทรปราการ',
    'สมุทรสงคราม', 'สมุทรสาคร', 'สระแก้ว', 'สระบุรี', 'สิงห์บุรี', 'สุโขทัย', 'สุพรรณบุรี', 'สุราษฎร์ธานี', 'สุรินทร์',
    'หนองคาย', 'หนองบัวลำภู', 'อ่างทอง', 'อำนาจเจริญ', 'อุดรธานี', 'อุตรดิตถ์', 'อุทัยธานี', 'อุบลราชธานี'
]

# ฟังก์ชันสำหรับแยกประเภทหน่วยงาน
def get_org_type(org_name):
    org_name = org_name.lower()
    if 'กระทรวง' in org_name:
        return 'กระทรวง'
    elif 'กรม' in org_name:
        return 'กรม'
    elif 'มหาวิทยาลัย' in org_name:
        return 'มหาวิทยาลัย'
    elif 'สำนักงาน' in org_name:
        return 'สำนักงาน'
    elif 'องค์การ' in org_name:
        return 'องค์การ'
    elif 'บริษัท' in org_name:
        return 'บริษัท'
    elif 'ธนาคาร' in org_name:
        return 'ธนาคาร'
    else:
        return 'อื่นๆ'

# ฟังก์ชันสำหรับแยกจังหวัด
def get_province(org_name):
    for province in THAI_PROVINCES:
        if province in org_name:
            return province
    return 'ไม่ระบุจังหวัด'

# ดึงข้อมูลหน่วยงานทั้งหมด
orgs_df = get_all_organizations()

# สร้างตัวกรอง
col1, col2, col3 = st.columns(3)

with col1:
    # ค้นหาหน่วยงาน
    search_term = st.text_input("🔍 ค้นหาหน่วยงาน")

with col2:
    # กรองตามประเภทหน่วยงาน
    org_types = sorted(orgs_df['org_type'].unique())
    selected_types = st.multiselect(
        "🏛️ ประเภทหน่วยงาน",
        options=org_types,
        default=[]
    )

with col3:
    # กรองตามจังหวัด
    provinces = sorted(orgs_df['province'].unique())
    selected_provinces = st.multiselect(
        "🗺️ จังหวัด",
        options=provinces,
        default=[]
    )

# กรองข้อมูล
filtered_df = orgs_df.copy()

# กรองตามคำค้นหา
if search_term:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False)]

# กรองตามประเภทหน่วยงาน
if selected_types:
    filtered_df = filtered_df[filtered_df['org_type'].isin(selected_types)]

# กรองตามจังหวัด
if selected_provinces:
    filtered_df = filtered_df[filtered_df['province'].isin(selected_provinces)]

# แสดงรายการหน่วยงาน
st.subheader(f"📋 รายการหน่วยงาน ({len(filtered_df)} รายการ)")

# แสดงข้อมูลในตาราง
if not filtered_df.empty:
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "deptId": "รหัสหน่วยงาน",
            "name": "ชื่อหน่วยงาน",
            "org_type": "ประเภทหน่วยงาน",
            "province": "จังหวัด",
            "dataset_count": st.column_config.NumberColumn(
                "จำนวนชุดข้อมูล",
                help="จำนวนชุดข้อมูลทั้งหมดของหน่วยงาน"
            )
        }
    )
    
    # เลือกหน่วยงานเพื่อดูรายละเอียด
    selected_org = st.selectbox(
        "เลือกหน่วยงานเพื่อดูรายละเอียด",
        options=filtered_df['name'].tolist()
    )
    
    if selected_org:
        st.subheader(f"📊 ชุดข้อมูลของ {selected_org}")
        
        # ดึงข้อมูลชุดข้อมูลของหน่วยงานจากฐานข้อมูล
        try:
            cursor = db.conn.execute("""
                SELECT 
                    package_id,
                    title,
                    resource_count,
                    file_types,
                    last_updated
                FROM datasets
                WHERE organization = ?
                ORDER BY last_updated DESC
            """, (selected_org,))
            
            datasets_df = pd.DataFrame(cursor.fetchall(), columns=[
                'id', 'title', 'resource_count', 'file_types', 'last_updated'
            ])
            
            if not datasets_df.empty:
                st.dataframe(
                    datasets_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": "รหัสชุดข้อมูล",
                        "title": "ชื่อชุดข้อมูล",
                        "resource_count": st.column_config.NumberColumn(
                            "จำนวนทรัพยากร",
                            help="จำนวนทรัพยากรในชุดข้อมูล"
                        ),
                        "file_types": "ประเภทไฟล์",
                        "last_updated": "ปรับปรุงล่าสุด"
                    }
                )
            else:
                st.info("ไม่พบชุดข้อมูลของหน่วยงานนี้")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลชุดข้อมูล: {str(e)}")
else:
    st.info("ไม่พบข้อมูลหน่วยงาน") 