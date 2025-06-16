import streamlit as st
import pandas as pd
from utils.data_utils import get_dataset_files, get_dataset_rankings, db
from utils.file_utils import format_file_types
from utils.ui_utils import create_action_cell, apply_custom_css, create_ranking_selector, toggle_theme
from migrate_data import main as migrate_main

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ข้อมูลหน่วยงาน | ข้อมูลเปิดภาครัฐ",
    page_icon="🏢",
    layout="wide"
)

# ใส่ CSS
apply_custom_css()

# ฟังก์ชันสำหรับการ filter ข้อมูล
@st.cache_data(ttl=3600)
def get_dataset_ranking(package_id):
    """ดึง ranking สูงสุดของชุดข้อมูล"""
    try:
        files = get_dataset_files(package_id)
        if not files:
            return 0
        return max((f.get('ranking', 0) for f in files), default=0)
    except Exception:
        return 0

@st.cache_data(ttl=3600)
def filter_by_ranking(df, ranking_value):
    """กรองข้อมูลตาม ranking"""
    filtered = df.copy()
    
    # ดึง rankings ทั้งหมดในครั้งเดียว
    package_ids = filtered['package_id'].tolist()
    rankings = get_dataset_rankings(package_ids)
    
    # กรองข้อมูลตาม ranking
    filtered['max_ranking'] = filtered['package_id'].map(rankings)
    result = filtered[filtered['max_ranking'] == ranking_value].drop('max_ranking', axis=1)
    return result

@st.cache_resource
def initialize_data():
    """โหลดและตรวจสอบข้อมูล"""
    try:
        success, message, df = migrate_main(silent=True)
        if not success or df is None or df.empty:
            st.error(f"ไม่สามารถโหลดข้อมูลได้: {message}")
            st.stop()
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}")
        st.stop()

# โหลดข้อมูล
with st.spinner("🔄 กำลังโหลดข้อมูล..."):
    df = initialize_data()

# ดึงชื่อหน่วยงานจาก query parameters
query_params = st.query_params
org_name = query_params.get("org", None)

if not org_name:
    st.error("ไม่พบข้อมูลหน่วยงาน")
    st.stop()

# กรองข้อมูลเฉพาะหน่วยงานที่เลือก
org_data = df[df['organization'] == org_name].copy()

if org_data.empty:
    st.error(f"ไม่พบข้อมูลของหน่วยงาน {org_name}")
    st.stop()

# หัวข้อหลัก
st.title(f"🏢 ข้อมูลหน่วยงาน {org_name}")
st.markdown("---")

# แสดงภาพรวมข้อมูล
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("จำนวนชุดข้อมูล", len(org_data))
with col2:
    st.metric("จำนวนทรัพยากรทั้งหมด", org_data['resource_count'].sum())
with col3:
    st.metric("ประเภทไฟล์", len(set(org_data['file_types'].str.split(',').explode())))

# แสดงข้อมูลในรูปแบบตาราง
st.subheader(f"📋 รายการข้อมูล ({len(org_data)} รายการ)")

# กำหนดจำนวนรายการต่อหน้า
rows_per_page = st.select_slider(
    "จำนวนรายการต่อหน้า",
    options=[10, 20, 50, 100],
    value=20
)

# คำนวณจำนวนหน้าทั้งหมด
total_pages = len(org_data) // rows_per_page + (1 if len(org_data) % rows_per_page > 0 else 0)

# เลือกหน้าที่ต้องการแสดง
if total_pages > 0:
    page_number = st.number_input(
        f"หน้า (1-{total_pages})", 
        min_value=1,
        max_value=total_pages,
        value=1
    )
else:
    page_number = 1

# คำนวณ index เริ่มต้นและสิ้นสุดของข้อมูลที่จะแสดง
start_idx = (page_number - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, len(org_data))

# เตรียมข้อมูลสำหรับแสดงในตาราง
display_df = org_data.iloc[start_idx:end_idx].copy()

# เปลี่ยนชื่อคอลัมน์
new_column_names = {
    'title': 'ชื่อชุดข้อมูล',
    'resource_count': 'จำนวนทรัพยากร',
    'file_types': 'ประเภทไฟล์',
    'last_updated': 'ปรับปรุงล่าสุด',
    'package_id': 'package_id',
    'url': 'url'
}
display_df = display_df.rename(columns=new_column_names)

# อัพเดทการแสดงผลประเภทไฟล์
display_df['ประเภทไฟล์'] = display_df.apply(format_file_types, axis=1)

# Initialize session state
if 'sort_column' not in st.session_state:
    st.session_state.sort_column = None
if 'sort_ascending' not in st.session_state:
    st.session_state.sort_ascending = True

# จัดการการเรียงลำดับ
def toggle_sort(column):
    if st.session_state.sort_column == column:
        st.session_state.sort_ascending = not st.session_state.sort_ascending
    else:
        st.session_state.sort_column = column
        st.session_state.sort_ascending = True
    
    if column:
        display_df.sort_values(by=column, ascending=st.session_state.sort_ascending, inplace=True)

# แสดงส่วนหัวของตาราง
st.markdown("""
<div style="display: flex; margin-bottom: 10px; font-weight: bold; background-color: rgba(128, 128, 128, 0.6); color: white; padding: 12px;">
    <div style="flex: 3">ชื่อชุดข้อมูล</div>
    <div style="flex: 1">จำนวนทรัพยากร</div>
    <div style="flex: 2">ประเภทไฟล์</div>
    <div style="flex: 1">ปรับปรุงล่าสุด</div>
    <div style="flex: 1">⭐</div>
    <div style="flex: 1">Action</div>
</div>
""", unsafe_allow_html=True)

# สร้างปุ่มสำหรับ sort
sort_cols = st.columns([3, 1, 2, 1, 1, 1])

# ปุ่ม sort สำหรับจำนวนทรัพยากร
with sort_cols[1]:
    if st.button("🔄", key="sort_resources", help="เรียงลำดับตามจำนวนทรัพยากร"):
        toggle_sort('จำนวนทรัพยากร')

# ปุ่ม sort สำหรับประเภทไฟล์
with sort_cols[2]:
    if st.button("🔄", key="sort_filetypes", help="เรียงลำดับตามประเภทไฟล์"):
        toggle_sort('ประเภทไฟล์')

# ปุ่ม sort สำหรับวันที่ปรับปรุง
with sort_cols[3]:
    if st.button("🔄", key="sort_date", help="เรียงลำดับตามวันที่ปรับปรุง"):
        toggle_sort('ปรับปรุงล่าสุด')

# แสดงทิศทางการเรียงลำดับปัจจุบัน
if st.session_state.sort_column:
    direction = "น้อยไปมาก ⬆️" if st.session_state.sort_ascending else "มากไปน้อย ⬇️"
    st.caption(f"เรียงตาม {st.session_state.sort_column} ({direction})")

# แสดงข้อมูลในรูปแบบตาราง
for _, row in display_df.iterrows():
    with st.container():
        cols = st.columns([3, 1, 2, 1, 1, 1])
        with cols[0]:
            st.markdown(f"""<div style="white-space: normal;">{row['ชื่อชุดข้อมูล']}</div>""", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""<div style="text-align: center;">{row['จำนวนทรัพยากร']}</div>""", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(row['ประเภทไฟล์'], unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"""<div style="white-space: nowrap;">{row['ปรับปรุงล่าสุด'][:10]}</div>""", unsafe_allow_html=True)
        with cols[4]:
            create_ranking_selector(row)
        with cols[5]:
            create_action_cell({
                'package_id': row['package_id'],
                'url': row['url']
            })

# แสดงข้อความบอกจำนวนรายการที่กำลังแสดง
st.caption(f"กำลังแสดงรายการที่ {start_idx + 1} ถึง {end_idx} จากทั้งหมด {len(org_data)} รายการ")

# Footer
st.markdown("---")
st.markdown("🏢 พัฒนาโดยใช้ข้อมูลจาก [data.go.th](https://data.go.th)")

# ปุ่มกลับไปหน้าหลัก
st.link_button(
    "🔙 กลับไปหน้าหลัก",
    "/",
    use_container_width=True
) 