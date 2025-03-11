import streamlit as st
import pandas as pd
import plotly.express as px
from utils.ui_utils import toggle_theme
from migrate_data import main as migrate_main

st.set_page_config(
    page_title="สถิติ | ข้อมูลเปิดภาครัฐ",
    page_icon="📊",
    layout="wide"
)

# โหลดข้อมูล
with st.spinner("🔄 กำลังโหลดข้อมูล..."):
    success, message, df = migrate_main(silent=True)
    if not success or df is None or df.empty:
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {message}")
        st.stop()

col1, col2 = st.columns(2)

with col1:
    # กราฟแสดงหน่วยงานที่มีข้อมูลมากที่สุด
    org_counts = df['organization'].value_counts().head(10)
    
    # สร้าง DataFrame สำหรับ plotly
    org_df = pd.DataFrame({
        'หน่วยงาน': org_counts.index,
        'จำนวนชุดข้อมูล': org_counts.values
    })
    
    # สร้าง bar chart ด้วย plotly
    fig = px.bar(
        org_df,
        x='จำนวนชุดข้อมูล',
        y='หน่วยงาน',
        orientation='h',
        title='10 หน่วยงานที่มีชุดข้อมูลมากที่สุด'
    )
    
    # ปรับแต่ง layout
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        height=400,
        yaxis={'categoryorder':'total ascending'}
    )
    
    # แสดงกราฟ
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # กราฟแสดงประเภทไฟล์ที่พบบ่อย
    file_types = []
    for types in df['file_types']:
        if types:
            file_types.extend([t.strip() for t in types.split(',')])
    
    file_type_counts = pd.Series(file_types).value_counts().head(10)
    st.bar_chart(file_type_counts)
    st.caption("10 ประเภทไฟล์ที่พบมากที่สุด")
    