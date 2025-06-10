import streamlit as st
import pandas as pd
from utils.data_utils import get_dataset_files, get_dataset_rankings
from utils.file_utils import format_file_types
from utils.ui_utils import create_action_cell, apply_custom_css, create_ranking_selector, toggle_theme
from migrate_data import main as migrate_main

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="หน้าหลัก | ข้อมูลเปิดภาครัฐ",
    page_icon="📊",
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

@st.cache_data(ttl=3600)
def get_unique_file_types(df):
    """รวบรวมประเภทไฟล์ที่มีทั้งหมด"""
    if df is None or 'file_types' not in df.columns:
        return []
    all_file_types = []
    for types in df['file_types'].dropna():
        all_file_types.extend([t.strip() for t in types.split(',')])
    return sorted(list(set(all_file_types)))

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
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    search_term = st.text_input("ค้นหาจากชื่อชุดข้อมูล", "")
with col2:
    selected_org = st.selectbox(
        "กรองตามหน่วยงาน",
        ["ทั้งหมด"] + sorted(df['organization'].unique().tolist())
    )
with col3:
    # เพิ่มตัวกรองประเภทองค์กร
    org_types = ["ทั้งหมด", "กระทรวง", "กรม", "จังหวัด", "องค์กรปกครองส่วนท้องถิ่น", "รัฐวิสาหกิจ", "มหาวิทยาลัย", "อื่นๆ"]
    selected_org_type = st.selectbox(
        "ประเภทองค์กร",
        org_types
    )
with col4:
    # เพิ่มตัวกรองจังหวัด
    provinces = ["ทั้งหมด"] + sorted([p for p in df['organization'].unique() if "จังหวัด" in p])
    selected_province = st.selectbox(
        "จังหวัด",
        provinces
    )
with col5:
    # สร้างรายการประเภทไฟล์ทั้งหมดที่มี
    unique_file_types = get_unique_file_types(df)
    
    selected_file_type = st.selectbox(
        "กรองตามประเภทไฟล์",
        ["ทั้งหมด"] + unique_file_types
    )
with col6:
    # เพิ่มตัวกรองตาม ranking
    ranking_filter = st.selectbox(
        "กรองตาม Ranking",
        ["⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐", "ทั้งหมด"],
        index=0,
        help="กรองข้อมูลตามระดับคุณภาพ"
    )

# กรองข้อมูล
filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
if selected_org != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['organization'] == selected_org]
if selected_org_type != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['organization'].str.contains(selected_org_type, case=False, na=False)]
if selected_province != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['organization'] == selected_province]
if selected_file_type != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['file_types'].str.contains(selected_file_type, case=False, na=False)]

# กรองตาม ranking
if ranking_filter != "ทั้งหมด":
    ranking_value = len(ranking_filter)  # นับจำนวนดาว
    filtered_df = filter_by_ranking(filtered_df, ranking_value)

# แสดงผลข้อมูลในรูปแบบตาราง
st.subheader("📊 สรุปข้อมูลตามหน่วยงาน")

# สร้างตารางสรุปข้อมูลหน่วยงาน
org_summary = df.groupby('organization').agg({
    'title': 'count',
    'resource_count': 'sum'
}).reset_index()
org_summary.columns = ['หน่วยงาน', 'จำนวนชุดข้อมูล', 'จำนวนทรัพยากร']
org_summary = org_summary.sort_values('จำนวนชุดข้อมูล', ascending=False)

# แสดงตารางสรุปหน่วยงาน
edited_df = st.data_editor(
    org_summary,
    column_config={
        "หน่วยงาน": st.column_config.TextColumn(
            "หน่วยงาน",
            width="large",
            disabled=True
        ),
        "จำนวนชุดข้อมูล": st.column_config.NumberColumn(
            "จำนวนชุดข้อมูล",
            width="medium",
            disabled=True
        ),
        "จำนวนทรัพยากร": st.column_config.NumberColumn(
            "จำนวนทรัพยากร",
            width="medium",
            disabled=True
        )
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    key="org_summary_table"
)

# เพิ่มลิงค์สำหรับแต่ละหน่วยงาน
for _, row in org_summary.iterrows():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.link_button(
            "🔗",
            f"/Organization?org={row['หน่วยงาน']}",
            help=f"ดูข้อมูลเพิ่มเติมของ {row['หน่วยงาน']}"
        )
    with col2:
        st.markdown(f"**{row['หน่วยงาน']}** - {row['จำนวนชุดข้อมูล']} ชุดข้อมูล, {row['จำนวนทรัพยากร']} ทรัพยากร")

st.markdown("---")

# ดึงข้อมูลหน่วยงานที่เลือกจากตาราง
if st.session_state.org_summary_table["edited_rows"]:
    selected_row = list(st.session_state.org_summary_table["edited_rows"].keys())[0]
    selected_org_detail = edited_df.iloc[selected_row]["หน่วยงาน"]
else:
    selected_org_detail = "ทั้งหมด"

# ถ้ามีการเลือกหน่วยงาน
if selected_org_detail != "ทั้งหมด":
    st.subheader(f"📋 รายการข้อมูลของ {selected_org_detail}")
    
    # กรองข้อมูลเฉพาะหน่วยงานที่เลือก
    org_data = filtered_df[filtered_df['organization'] == selected_org_detail].copy()
    
    # แสดงข้อมูลในรูปแบบตาราง
    st.dataframe(
        org_data[['title', 'resource_count', 'file_types', 'last_updated']],
        column_config={
            "title": st.column_config.TextColumn("ชื่อชุดข้อมูล", width="large"),
            "resource_count": st.column_config.NumberColumn("จำนวนทรัพยากร", width="medium"),
            "file_types": st.column_config.TextColumn("ประเภทไฟล์", width="medium"),
            "last_updated": st.column_config.TextColumn("ปรับปรุงล่าสุด", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )

    # เพิ่มลิงค์ไปยังหน้า organization_data
    st.link_button(
        "🔗 ดูข้อมูลเพิ่มเติม",
        f"/Organization?org={selected_org_detail}",
        help=f"ดูข้อมูลเพิ่มเติมของ {selected_org_detail}",
        use_container_width=True
    )

st.markdown("---")

# แสดงรายการชุดข้อมูล
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
    <div style="flex: 2">หน่วยงาน</div>
    <div style="flex: 1">จำนวนทรัพยากร</div>
    <div style="flex: 2">ประเภทไฟล์</div>
    <div style="flex: 1">ปรับปรุงล่าสุด</div>
    <div style="flex: 1">⭐</div>
    <div style="flex: 1">Action</div>
</div>
""", unsafe_allow_html=True)

# สร้างปุ่มสำหรับ sort
sort_cols = st.columns([3, 2, 1, 2, 1, 1, 1])

# ปุ่ม sort สำหรับจำนวนทรัพยากร
with sort_cols[2]:
    if st.button("🔄", key="sort_resources", help="เรียงลำดับตามจำนวนทรัพยากร"):
        toggle_sort('จำนวนทรัพยากร')

# ปุ่ม sort สำหรับประเภทไฟล์
with sort_cols[3]:
    if st.button("🔄", key="sort_filetypes", help="เรียงลำดับตามประเภทไฟล์"):
        toggle_sort('ประเภทไฟล์')

# ปุ่ม sort สำหรับวันที่ปรับปรุง
with sort_cols[4]:
    if st.button("🔄", key="sort_date", help="เรียงลำดับตามวันที่ปรับปรุง"):
        toggle_sort('ปรับปรุงล่าสุด')

# แสดงทิศทางการเรียงลำดับปัจจุบัน
if st.session_state.sort_column:
    direction = "น้อยไปมาก ⬆️" if st.session_state.sort_ascending else "มากไปน้อย ⬇️"
    st.caption(f"เรียงตาม {st.session_state.sort_column} ({direction})")

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
