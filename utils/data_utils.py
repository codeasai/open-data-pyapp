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
    # ตรวจสอบว่ามีไฟล์ database หรือไม่
    if not os.path.exists('data/database.sqlite'):
        print("🔄 กำลังเตรียมฐานข้อมูล...")
        
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
        db.init_sample_data(sample_data)
        print("✅ เตรียมฐานข้อมูลเสร็จสิ้น")

def load_datasets():
    """โหลดข้อมูลชุดข้อมูล"""
    # เตรียมข้อมูลเริ่มต้นถ้ายังไม่มี
    init_database()
    
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

def update_dataset(dataset_id):
    """อัพเดทข้อมูลสำหรับ dataset ที่ระบุ"""
    # สร้าง progress bar
    progress_text = "กำลังอัพเดทข้อมูล..."
    progress_bar = st.progress(0, text=progress_text)
    
    try:
        print(f"\n🔄 เริ่มอัพเดทข้อมูลสำหรับ dataset ID: {dataset_id}")
        
        # ขั้นตอนที่ 1: ดึงข้อมูลจาก API
        progress_bar.progress(0.2, text="กำลังดึงข้อมูลจาก API...")
        PACKAGE_SHOW_URL = f"https://data.go.th/api/3/action/package_show?id={dataset_id}"
        response = requests.get(PACKAGE_SHOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success"):
            progress_bar.empty()
            print("❌ API ไม่สามารถดึงข้อมูลได้")
            return "❌ ไม่สามารถดึงข้อมูลจาก API ได้"
        
        # ขั้นตอนที่ 2: อ่านข้อมูลเดิม
        progress_bar.progress(0.4, text="กำลังอ่านข้อมูลเดิม...")
        try:
            with open('data/processed/datasets.json', 'r', encoding='utf-8') as f:
                datasets = json.load(f)
            print("✅ อ่านข้อมูลเดิมสำเร็จ")
        except Exception as e:
            progress_bar.empty()
            print(f"❌ ไม่สามารถอ่านไฟล์ datasets.json: {str(e)}")
            return f"❌ ไม่สามารถอ่านข้อมูลเดิม: {str(e)}"
        
        # ขั้นตอนที่ 3: อัพเดทข้อมูล
        progress_bar.progress(0.6, text="กำลังอัพเดทข้อมูล...")
        package = data['result']
        
        # หาและอัพเดทข้อมูลที่ต้องการ
        for i, dataset in enumerate(datasets):
            if dataset['package_id'] == dataset_id:
                # อัพเดทข้อมูลทั่วไป
                datasets[i].update({
                    'title': package.get('title', ''),
                    'organization': package.get('organization', {}).get('title', ''),
                    'url': package.get('url', ''),
                    'last_updated': package.get('metadata_modified', '')
                })
                
                # อัพเดทข้อมูลทรัพยากร
                resources = package.get('resources', [])
                datasets[i]['resource_count'] = len(resources)
                
                # อัพเดทประเภทไฟล์
                file_types = set()
                for resource in resources:
                    if resource.get('format'):
                        file_types.add(resource['format'].upper())
                datasets[i]['file_types'] = ', '.join(sorted(file_types))
                
                # บันทึกข้อมูลไฟล์
                try:
                    with open('data/processed/resources.json', 'r', encoding='utf-8') as f:
                        all_files = json.load(f)
                except:
                    all_files = []
                
                # อัพเดทหรือเพิ่มข้อมูลไฟล์
                dataset_files = []
                for resource in resources:
                    file_info = {
                        'dataset_id': dataset_id,
                        'file_name': resource.get('name', ''),
                        'format': resource.get('format', '').upper(),
                        'url': resource.get('url', ''),
                        'description': resource.get('description', '')
                    }
                    dataset_files.append(file_info)
                
                # ลบไฟล์เก่าของ dataset นี้
                all_files = [f for f in all_files if f['dataset_id'] != dataset_id]
                # เพิ่มไฟล์ใหม่
                all_files.extend(dataset_files)
                
                # บันทึกข้อมูลไฟล์
                with open('data/processed/resources.json', 'w', encoding='utf-8') as f:
                    json.dump(all_files, f, ensure_ascii=False, indent=2)
                
                break
        
        # ขั้นตอนที่ 4: บันทึกข้อมูล
        progress_bar.progress(0.8, text="กำลังบันทึกข้อมูล...")
        with open('data/processed/datasets.json', 'w', encoding='utf-8') as f:
            json.dump(datasets, f, ensure_ascii=False, indent=2)
        
        # เสร็จสิ้น
        progress_bar.progress(1.0, text="อัพเดทข้อมูลสำเร็จ!")
        time.sleep(1)
        progress_bar.empty()
        
        print(f"✅ อัพเดทข้อมูลสำเร็จ: {dataset_id}\n")
        
        # เพิ่มการอัพเดท session state
        if 'last_update' not in st.session_state:
            st.session_state.last_update = {}
        st.session_state.last_update[dataset_id] = time.time()
        
        return "✅ อัพเดทข้อมูลสำเร็จ"
        
    except Exception as e:
        progress_bar.empty()
        error_msg = f"เกิดข้อผิดพลาด: {str(e)}"
        print(f"❌ {error_msg}")
        return f"❌ {error_msg}"

def update_dataset_ranking(dataset_id, ranking):
    """อัพเดท ranking ของ dataset"""
    return db.update_dataset_ranking(dataset_id, ranking)

def get_dataset_files(dataset_id):
    """ดึงข้อมูลไฟล์ของ dataset"""
    return db.get_dataset_files(dataset_id) 