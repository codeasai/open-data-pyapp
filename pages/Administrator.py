import streamlit as st
import pandas as pd
from utils.data_utils import db, update_dataset
from utils.auth import check_user, login_page
from utils.ui_utils import toggle_theme
from utils.api_utils import test_all_endpoints, get_api_client
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

# สร้าง tabs
tab1, tab2, tab3 = st.tabs(["📊 สถานะระบบ", "🔌 แหล่งข้อมูล", "🔄 จัดการข้อมูล"])

with tab1:
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

with tab2:
    # แสดงผลการทดสอบ API
    st.subheader("🔌 ทดสอบการเชื่อมต่อ API")

    # แสดงรายการ endpoints ที่ใช้
    st.write("#### 📋 Endpoint List")
    endpoints = {
        # DataGo API Endpoints
        "site_read": {
            "description": "ทดสอบการเชื่อมต่อพื้นฐาน",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "organization_list": {
            "description": "ดึงรายการหน่วยงาน",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "organization_show": {
            "description": "ดึงรายละเอียดหน่วยงาน",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "organization_activity_list": {
            "description": "ดึงข้อมูลชุดข้อมูลของหน่วยงาน",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "package_list": {
            "description": "ดึงรายการชุดข้อมูลทั้งหมด",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "package_show": {
            "description": "ดึงรายละเอียดชุดข้อมูล",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "package_search": {
            "description": "ค้นหาชุดข้อมูล",
            "base_url": "https://data.go.th/api/3/action/"
        },
        "resource_show": {
            "description": "ดึงรายละเอียดทรัพยากร",
            "base_url": "https://data.go.th/api/3/action/"
        },
        
        # GDCatalog API Endpoints
        "gdc_datasets": {
            "description": "ดึงรายการชุดข้อมูลจาก GDCatalog",
            "base_url": "https://gdcatalog.go.th/api/"
        },
        "gdc_dataset_details": {
            "description": "ดึงรายละเอียดชุดข้อมูลจาก GDCatalog",
            "base_url": "https://gdcatalog.go.th/api/"
        },
        "gdc_organization_datasets": {
            "description": "ดึงชุดข้อมูลตามหน่วยงานจาก GDCatalog",
            "base_url": "https://gdcatalog.go.th/api/"
        },
        
        # Budget API Endpoints
        "budget_province": {
            "description": "ดึงข้อมูลงบประมาณรายจังหวัด",
            "base_url": "https://www.bb.go.th/api/"
        },
        "budget_ministry": {
            "description": "ดึงข้อมูลงบประมาณกระทรวง",
            "base_url": "https://www.bb.go.th/api/"
        },
        "budget_agency": {
            "description": "ดึงข้อมูลงบประมาณหน่วยงาน",
            "base_url": "https://www.bb.go.th/api/"
        }
    }

    # สร้างตารางแสดง endpoints พร้อมปุ่มทดสอบ
    client = get_api_client()
    if client:
        # สร้างตาราง
        col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
        with col1:
            st.write("**Endpoint**")
        with col2:
            st.write("**คำอธิบาย**")
        with col3:
            st.write("**Base URL**")
        with col4:
            st.write("**ทดสอบ**")

        for endpoint, info in endpoints.items():
            col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
            with col1:
                st.write(endpoint)
            with col2:
                st.write(info["description"])
            with col3:
                st.write(info["base_url"])
            with col4:
                if st.button("ทดสอบ", key=f"test_{endpoint}"):
                    with st.spinner(f"กำลังทดสอบ {endpoint}..."):
                        try:
                            if endpoint.startswith('gdc_'):
                                # ทดสอบ GDCatalog API
                                if endpoint == 'gdc_datasets':
                                    response = client.get_datasets()
                                elif endpoint == 'gdc_dataset_details':
                                    response = client.get_dataset_details('test')
                                elif endpoint == 'gdc_organization_datasets':
                                    response = client.get_datasets(province='bangkok')
                                if response:
                                    st.success(f"✅ {endpoint}: เชื่อมต่อสำเร็จ")
                                else:
                                    st.error(f"❌ {endpoint}: ไม่สามารถเชื่อมต่อได้")
                            elif endpoint.startswith('budget_'):
                                # ทดสอบ Budget API
                                st.warning(f"⚠️ {endpoint}: ยังไม่มีการรองรับ API นี้")
                            else:
                                # ทดสอบ DataGo API
                                if endpoint == 'site_read':
                                    response = client.test_connection()
                                elif endpoint == 'organization_list':
                                    response = client.get_organizations()
                                elif endpoint == 'organization_show':
                                    response = client.get_organization_details('test')
                                elif endpoint == 'organization_activity_list':
                                    response = client.get_organization_activity('test')
                                elif endpoint == 'package_list':
                                    response = client.get_datasets()
                                elif endpoint == 'package_show':
                                    response = client.get_dataset_details('test')
                                elif endpoint == 'package_search':
                                    response = client.search_datasets('test')
                                elif endpoint == 'resource_show':
                                    response = client.get_resource_details('test')
                                
                                if response:
                                    st.success(f"✅ {endpoint}: เชื่อมต่อสำเร็จ")
                                else:
                                    st.error(f"❌ {endpoint}: ไม่สามารถเชื่อมต่อได้")
                        except Exception as e:
                            st.error(f"❌ {endpoint}: {str(e)}")

        # แสดงปุ่มทดสอบทั้งหมด
        st.write("#### 🔄 ทดสอบการเชื่อมต่อทั้งหมด")
        if st.button("ทดสอบการเชื่อมต่อทั้งหมด"):
            results = test_all_endpoints()
            for endpoint, (success, message) in results.items():
                if success:
                    st.success(f"{endpoint}: {message}")
                else:
                    st.error(f"{endpoint}: {message}")

        # แสดงข้อมูล API ที่ใช้
        st.write("#### 📊 ข้อมูล API ที่ใช้")
        api_info = {
            "DataGo API": {
                "Base URL": "https://data.go.th/api/3/action/",
                "Version": "3.0",
                "Authentication": "Bearer Token"
            },
            "GDCatalog API": {
                "Base URL": "https://gdcatalog.go.th/api/",
                "Version": "1.0",
                "Authentication": "API Key"
            },
            "Budget API": {
                "Base URL": "https://www.bb.go.th/api/",
                "Version": "1.0",
                "Authentication": "None"
            }
        }

        for api_name, info in api_info.items():
            st.write(f"**{api_name}**")
            for key, value in info.items():
                st.write(f"- {key}: {value}")
            st.write("---")
    else:
        st.error("ไม่สามารถเชื่อมต่อกับ API ได้ กรุณาตรวจสอบ API key")

with tab3:
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

    if os.path.exists('data/database.sqlite'):
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
    if os.path.exists('data/database.sqlite'):
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