import streamlit as st
import pandas as pd
from utils.data_utils import load_datasets

st.title("📈 สถิติข้อมูล")

# โหลดข้อมูล
df = load_datasets()
if df is None:
    st.stop()

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

# ... add your statistics code here ... 