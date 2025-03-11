import streamlit as st
import pandas as pd
from utils.data_utils import load_datasets, get_dataset_files
from utils.file_utils import format_file_types
from utils.ui_utils import create_action_cell, apply_custom_css, create_ranking_selector

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ข้อมูลเปิดภาครัฐ",
    page_icon="📊",
    layout="wide"
)

# โหลดข้อมูล
df = load_datasets()
if df is None:
    st.stop()

# ตรวจสอบว่ามีข้อมูลหรือไม่
if len(df) == 0:
    st.warning("ไม่พบข้อมูลในฐานข้อมูล กรุณาตรวจสอบไฟล์ข้อมูลใน data/*.json")
    st.stop()

# ใส่ CSS
apply_custom_css()

# หัวข้อหลัก
st.title("⭐⭐⭐⭐ ข้อมูลเปิดภาครัฐคุณภาพสูง")
st.markdown("---")

# แสดงภาพรวมข้อมูล
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("จำนวนชุดข้อมูลคุณภาพสูง", len(df))
with col2:
    # ตรวจสอบคอลัมน์ก่อนใช้งาน
    if 'organization' in df.columns:
        st.metric("จำนวนหน่วยงาน", df['organization'].nunique())
    else:
        st.error("ไม่พบคอลัมน์ 'organization' ในข้อมูล")
with col3:
    total_resources = df['resource_count'].sum()
    st.metric("จำนวนทรัพยากรทั้งหมด", total_resources)

# ฟิลเตอร์ข้อมูล
st.subheader("🔍 ค้นหาและกรองข้อมูล")
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_term = st.text_input("ค้นหาจากชื่อชุดข้อมูล", "")
with col2:
    selected_org = st.selectbox(
        "กรองตามหน่วยงาน",
        ["ทั้งหมด"] + sorted(df['organization'].unique().tolist())
    )
with col3:
    # สร้างรายการประเภทไฟล์ทั้งหมดที่มี
    all_file_types = []
    for types in df['file_types'].dropna():
        all_file_types.extend([t.strip() for t in types.split(',')])
    unique_file_types = sorted(list(set(all_file_types)))
    
    selected_file_type = st.selectbox(
        "กรองตามประเภทไฟล์",
        ["ทั้งหมด"] + unique_file_types
    )

with col4:
    # เพิ่มตัวกรองตาม ranking
    ranking_filter = st.selectbox(
        "กรองตาม Ranking",
        ["⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐", "ทั้งหมด"],  # ย้าย 4 ดาวขึ้นมาเป็นตัวแรก
        index=0,  # ตั้งค่าเริ่มต้นเป็นตัวเลือกแรก (4 ดาว)
        help="กรองข้อมูลตามระดับคุณภาพ"
    )

# กรองข้อมูล
filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
if selected_org != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['organization'] == selected_org]
if selected_file_type != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['file_types'].str.contains(selected_file_type, case=False, na=False)]

# กรองตาม ranking
if ranking_filter != "ทั้งหมด":
    ranking_value = len(ranking_filter)  # นับจำนวนดาว
    def has_ranking(row):
        files = get_dataset_files(row['package_id'])
        # หาค่า ranking สูงสุดของไฟล์ในชุดข้อมูล
        max_ranking = max((f.get('ranking', 0) for f in files), default=0)
        return max_ranking == ranking_value
    
    filtered_df = filtered_df[filtered_df.apply(has_ranking, axis=1)]

# แสดงผลข้อมูลในรูปแบบตาราง
st.subheader(f"รายการชุดข้อมูล ({len(filtered_df)} รายการ)")

# กำหนดจำนวนรายการต่อหน้า
rows_per_page = st.select_slider(
    "จำนวนรายการต่อหน้า",
    options=[10, 20, 50, 100],
    value=20
)

# คำนวณจำนวนหน้าทั้งหมด
total_pages = len(filtered_df) // rows_per_page + (1 if len(filtered_df) % rows_per_page > 0 else 0)

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
end_idx = min(start_idx + rows_per_page, len(filtered_df))

# เตรียมข้อมูลสำหรับแสดงในตาราง
display_df = filtered_df.iloc[start_idx:end_idx].copy()

# เปลี่ยนชื่อคอลัมน์ (เก็บ package_id และ url ไว้)
new_column_names = {
    'title': 'ชื่อชุดข้อมูล',
    'organization': 'หน่วยงาน',
    'resource_count': 'จำนวนทรัพยากร',
    'file_types': 'ประเภทไฟล์',
    'last_updated': 'ปรับปรุงล่าสุด',
    'package_id': 'package_id',  # เก็บ package_id ไว้
    'url': 'url'  # เก็บ url ไว้
}
display_df = display_df.rename(columns=new_column_names)

# อัพเดทการแสดงผลประเภทไฟล์ (ไม่ต้องใช้ resources)
display_df['ประเภทไฟล์'] = display_df.apply(format_file_types, axis=1)

# แสดงส่วนหัวของตาราง
st.markdown("""
<div style="display: flex; margin-bottom: 10px; font-weight: bold; background-color: rgba(128, 128, 128, 0.6); color: white; padding: 12px;">
    <div style="flex: 3">ชื่อชุดข้อมูล</div>
    <div style="flex: 2">หน่วยงาน</div>
    <div style="flex: 1">จำนวนทรัพยากร</div>
    <div style="flex: 2">ประเภทไฟล์</div>
    <div style="flex: 1">ปรับปรุงล่าสุด</div>
    <div style="flex: 1">⭐</div>
    <div style="flex: 1">Action</div>
</div>
""", unsafe_allow_html=True)

# แสดงข้อมูลในรูปแบบตาราง
for _, row in display_df.iterrows():
    with st.container():
        cols = st.columns([3, 2, 1, 2, 1, 1, 1])
        with cols[0]:
            st.markdown(f"""<div style="white-space: normal;">{row['ชื่อชุดข้อมูล']}</div>""", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""<div style="white-space: normal;">{row['หน่วยงาน']}</div>""", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"""<div style="text-align: center;">{row['จำนวนทรัพยากร']}</div>""", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(row['ประเภทไฟล์'], unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"""<div style="white-space: nowrap;">{row['ปรับปรุงล่าสุด'][:10]}</div>""", unsafe_allow_html=True)
        with cols[5]:
            create_ranking_selector(row)
        with cols[6]:
            create_action_cell({
                'package_id': row['package_id'],
                'url': row['url']
            })

# แสดงข้อความบอกจำนวนรายการที่กำลังแสดง
st.caption(f"กำลังแสดงรายการที่ {start_idx + 1} ถึง {end_idx} จากทั้งหมด {len(filtered_df)} รายการ")

# Footer
st.markdown("---")
st.markdown("🏢 พัฒนาโดยใช้ข้อมูลจาก [data.go.th](https://data.go.th)") 