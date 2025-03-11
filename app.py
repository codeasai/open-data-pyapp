import streamlit as st
import pandas as pd
from utils.data_utils import load_datasets
from utils.file_utils import format_file_types
from utils.ui_utils import create_action_cell, apply_custom_css

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

# ใส่ CSS
apply_custom_css()

# หัวข้อหลัก
st.title("📊 ระบบแสดงผลข้อมูลเปิดภาครัฐ")
st.markdown("---")

# แสดงภาพรวมข้อมูล
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("จำนวนชุดข้อมูลทั้งหมด", len(df))
with col2:
    st.metric("จำนวนหน่วยงาน", df['organization'].nunique())
with col3:
    total_resources = df['resource_count'].sum()
    st.metric("จำนวนทรัพยากรทั้งหมด", total_resources)

# ฟิลเตอร์ข้อมูล
st.subheader("🔍 ค้นหาและกรองข้อมูล")
col1, col2, col3 = st.columns(3)

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

# กรองข้อมูล
filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
if selected_org != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['organization'] == selected_org]
if selected_file_type != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['file_types'].str.contains(selected_file_type, case=False, na=False)]

# แสดงผลข้อมูลในรูปแบบตาราง
st.subheader(f"📋 รายการชุดข้อมูล ({len(filtered_df)} รายการ)")

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
    <div style="flex: 1">Action</div>
</div>
""", unsafe_allow_html=True)

# แสดงข้อมูลในรูปแบบตาราง
for _, row in display_df.iterrows():
    with st.container():
        cols = st.columns([3, 2, 1, 2, 1, 1])
        with cols[0]:
            st.markdown(f"""<div style="white-space: normal;">{row['ชื่อชุดข้อมูล']}</div>""", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""<div style="white-space: normal;">{row['หน่วยงาน']}</div>""", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"""<div style="text-align: center;">{row['จำนวนทรัพยากร']}</div>""", unsafe_allow_html=True)
        with cols[3]:
            # ประเภทไฟล์มี HTML อยู่แล้ว
            st.markdown(row['ประเภทไฟล์'], unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"""<div style="white-space: nowrap;">{row['ปรับปรุงล่าสุด'][:10]}</div>""", unsafe_allow_html=True)
        with cols[5]:
            create_action_cell({
                'package_id': row['package_id'],
                'url': row['url']
            })

# แสดงข้อความบอกจำนวนรายการที่กำลังแสดง
st.caption(f"กำลังแสดงรายการที่ {start_idx + 1} ถึง {end_idx} จากทั้งหมด {len(filtered_df)} รายการ")

# แสดงข้อมูลเชิงสถิติ
st.markdown("---")
st.subheader("📈 สถิติข้อมูล")

col1, col2 = st.columns(2)

with col1:
    # กราฟแสดงหน่วยงานที่มีข้อมูลมากที่สุด
    org_counts = df['organization'].value_counts().head(10)
    st.bar_chart(org_counts)
    st.caption("10 หน่วยงานที่มีชุดข้อมูลมากที่สุด")

with col2:
    # กราฟแสดงประเภทไฟล์ที่พบบ่อย
    file_types = []
    for types in df['file_types']:
        if types:
            file_types.extend([t.strip() for t in types.split(',')])
    
    file_type_counts = pd.Series(file_types).value_counts().head(10)
    st.bar_chart(file_type_counts)
    st.caption("10 ประเภทไฟล์ที่พบมากที่สุด")

# Footer
st.markdown("---")
st.markdown("🏢 พัฒนาโดยใช้ข้อมูลจาก [data.go.th](https://data.go.th)") 