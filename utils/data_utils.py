import json
import requests
import time
import streamlit as st
import pandas as pd
from .db_utils import Database
import os

# สร้าง global database instance
db = Database()

def init_database():
    """เตรียมข้อมูลเริ่มต้นถ้ายังไม่มี"""
    # ตรวจสอบว่าเคยรันแล้วหรือไม่
    if 'db_initialized' in st.session_state:
        return True

    print("\n🔄 เริ่มต้นการตรวจสอบฐานข้อมูล...")

    has_sqlite = os.path.exists('data/database.sqlite')
    json_files = {
        'datasets': 'data/datasets_info.json',
        'resources': 'data/dataset_files.json'
    }
    has_json = all(os.path.exists(path) for path in json_files.values())

    # ตรวจสอบว่ามีข้อมูลใน SQLite หรือไม่
    if has_sqlite:
        try:
            cursor = db.conn.execute("SELECT COUNT(*) FROM datasets")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"✅ พบข้อมูลในฐานข้อมูล SQLite แล้ว ({count} รายการ)")
                st.session_state.db_initialized = True
                return True
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการตรวจสอบฐานข้อมูล: {str(e)}")
            # ถ้าเกิดข้อผิดพลาด ให้ลบไฟล์ database เพื่อสร้างใหม่
            try:
                os.remove('data/database.sqlite')
                print("🔄 ลบฐานข้อมูลที่มีปัญหาและจะสร้างใหม่")
                has_sqlite = False
            except:
                pass

    # ถ้ามีไฟล์ JSON ให้ migrate ข้อมูลก่อน
    if has_json:
        print("\n📥 พบไฟล์ JSON ครบถ้วน เริ่มการ migrate...")
        
        # ตรวจสอบจำนวนข้อมูลใน JSON
        try:
            with open(json_files['datasets'], 'r', encoding='utf-8') as f:
                datasets = json.load(f)
            with open(json_files['resources'], 'r', encoding='utf-8') as f:
                resources = json.load(f)
            print(f"📊 พบข้อมูล {len(datasets)} ชุดข้อมูล และ {len(resources)} ทรัพยากร")
        except Exception as e:
            print(f"❌ ไม่สามารถอ่านไฟล์ JSON: {str(e)}")
            datasets = []
            resources = []

        # ถ้ามีข้อมูลใน JSON ให้ migrate
        if len(datasets) > 0 and len(resources) > 0:
            print("🔄 กำลัง migrate ข้อมูล...")
            if db.migrate_from_json():
                print("✅ Migrate ข้อมูลสำเร็จ")
                st.session_state.db_initialized = True
                return True
            else:
                print("❌ ไม่สามารถ migrate ข้อมูลได้")
        else:
            print("⚠️ ไม่พบข้อมูลในไฟล์ JSON")

    # สร้างข้อมูลตัวอย่างเฉพาะเมื่อไม่มีทั้ง SQLite และ JSON
    if not has_sqlite and not has_json:
        print("\n🔄 ไม่พบฐานข้อมูล กำลังสร้างข้อมูลตัวอย่าง...")
        
        # สร้างข้อมูลเริ่มต้น
        sample_data = {
            'datasets': [{
                'package_id': 'sample',
                'title': 'ตัวอย่างชุดข้อมูล',
                'organization': 'หน่วยงานตัวอย่าง',
                'url': 'https://data.go.th',
                'resource_count': 1,
                'file_types': 'CSV',
                'last_updated': '2024-03-19'
            }],
            'resources': [{
                'dataset_id': 'sample',
                'file_name': 'sample.csv',
                'format': 'CSV',
                'url': 'https://data.go.th',
                'description': 'ไฟล์ตัวอย่าง',
                'ranking': 4
            }]
        }
        
        # บันทึกข้อมูลลง database
        if db.init_sample_data(sample_data):
            print("✅ เตรียมฐานข้อมูลเสร็จสิ้น")
            st.session_state.db_initialized = True
            return True
        else:
            print("❌ ไม่สามารถสร้างข้อมูลตัวอย่างได้")
            return False

    return False

def load_datasets():
    """โหลดข้อมูลชุดข้อมูล"""
    # เตรียมข้อมูลเริ่มต้นถ้ายังไม่มี
    if not init_database():
        st.error("ไม่สามารถเตรียมฐานข้อมูลได้")
        return None
    
    try:
        data = db.get_datasets()
        # แปลงข้อมูลเป็น DataFrame และเปลี่ยนชื่อคอลัมน์
        df = pd.DataFrame(data)
        # ตรวจสอบคอลัมน์ที่มีอยู่
        print("Columns in DataFrame:", df.columns.tolist())
        
        # ตรวจสอบข้อมูลตัวอย่าง
        print("\nSample data:")
        print(df.head())
        
        # ไม่ต้องเปลี่ยนชื่อคอลัมน์เพราะชื่อตรงกับที่กำหนดใน SQL แล้ว
        return df
    except Exception as e:
        print(f"Error loading datasets: {str(e)}")
        st.error(f"ไม่สามารถอ่านข้อมูลได้: {str(e)}")
        return None

def update_dataset(package_id):
    """อัพเดทข้อมูล dataset"""
    try:
        # สร้าง progress bar
        progress_text = "กำลังอัพเดทข้อมูล..."
        progress_bar = st.progress(0, text=progress_text)
        
        print(f"\n🔄 เริ่มอัพเดทข้อมูลสำหรับ dataset ID: {package_id}")
        
        # ขั้นตอนที่ 1: ดึงข้อมูลจาก API
        progress_bar.progress(0.2, text="กำลังดึงข้อมูลจาก API...")
        PACKAGE_SHOW_URL = f"https://data.go.th/api/3/action/package_show?id={package_id}"
        response = requests.get(PACKAGE_SHOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success"):
            progress_bar.empty()
            print("❌ API ไม่สามารถดึงข้อมูลได้")
            return "❌ ไม่สามารถดึงข้อมูลจาก API ได้"
        
        # ขั้นตอนที่ 2: เตรียมข้อมูลสำหรับอัพเดท
        progress_bar.progress(0.4, text="กำลังเตรียมข้อมูล...")
        package = data['result']
        
        # เตรียมข้อมูล dataset
        resources = package.get('resources', [])
        
        # รวบรวมประเภทไฟล์และ URL
        file_types = set()
        resource_urls = []
        for resource in resources:
            if resource.get('format'):
                file_types.add(resource['format'].upper())
            if resource.get('url'):
                resource_urls.append(resource['url'])
        
        dataset_data = {
            'package_id': package_id,
            'title': package.get('title', ''),
            'organization': package.get('organization', {}).get('title', ''),
            'url': package.get('url', '') or (resource_urls[0] if resource_urls else ''),
            'last_updated': package.get('metadata_modified', ''),
            'resource_count': len(resources),
            'file_types': ', '.join(sorted(file_types)) if file_types else ''
        }
        
        # เตรียมข้อมูล resources
        resources_data = []
        for resource in resources:
            file_format = resource.get('format', '').upper()
            resources_data.append({
                'dataset_id': package_id,
                'file_name': resource.get('name', '') or f"ไฟล์ {file_format}" if file_format else 'ไฟล์ไม่ระบุชื่อ',
                'format': file_format,
                'url': resource.get('url', ''),
                'description': resource.get('description', ''),
                'ranking': 0  # เก็บ ranking เดิมไว้
            })
        
        # ขั้นตอนที่ 3: อัพเดทฐานข้อมูล
        progress_bar.progress(0.8, text="กำลังบันทึกข้อมูล...")
        
        # ดึง ranking เดิมก่อนอัพเดท
        existing_resources = db.get_dataset_files(package_id)
        ranking_map = {r['file_name']: r.get('ranking', 0) for r in existing_resources} if existing_resources else {}
        
        # อัพเดท ranking ในข้อมูลใหม่
        for resource in resources_data:
            resource['ranking'] = ranking_map.get(resource['file_name'], 0)
        
        if db.update_dataset(dataset_data, resources_data):
            # เสร็จสิ้น
            progress_bar.progress(1.0, text="อัพเดทข้อมูลสำเร็จ!")
            time.sleep(1)
            progress_bar.empty()
            
            print(f"✅ อัพเดทข้อมูลสำเร็จ: {package_id}")
            print(f"📁 ประเภทไฟล์: {dataset_data['file_types']}")
            print(f"🔗 URL: {dataset_data['url']}\n")
            
            # เพิ่มการอัพเดท session state
            if 'last_update' not in st.session_state:
                st.session_state.last_update = {}
            st.session_state.last_update[package_id] = time.time()
            
            return "✅ อัพเดทข้อมูลสำเร็จ"
        else:
            progress_bar.empty()
            return "❌ ไม่สามารถบันทึกข้อมูลลงฐานข้อมูลได้"
    except Exception as e:
        if 'progress_bar' in locals():
            progress_bar.empty()
        error_msg = f"เกิดข้อผิดพลาด: {str(e)}"
        print(f"❌ {error_msg}")
        return f"❌ {error_msg}"

def update_dataset_ranking(dataset_id, ranking):
    """อัพเดท ranking ของ dataset"""
    return db.update_dataset_ranking(dataset_id, ranking)

def get_dataset_files(package_id):
    """ดึงข้อมูลไฟล์ของ dataset ที่ระบุ"""
    db = Database()
    return db.get_dataset_files(package_id)

def get_dataset_rankings(package_ids):
    """ดึง ranking สูงสุดของหลาย datasets พร้อมกัน"""
    db = Database()
    return db.get_dataset_rankings(package_ids) 