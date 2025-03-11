import os
from utils.db_utils import Database
import pandas as pd

def check_database():
    """ตรวจสอบการมีอยู่ของฐานข้อมูล SQLite"""
    db_file = 'data/database.sqlite'
    return os.path.exists(db_file)

def create_sample_data(db):
    """สร้างข้อมูลตัวอย่างและบันทึกลงฐานข้อมูล"""
    try:
        # ตรวจสอบข้อมูลที่มีอยู่
        existing_data = db.get_datasets()
        if existing_data:
            df = pd.DataFrame(existing_data)
            return True, "✅ พบข้อมูลในฐานข้อมูล", df

        # สร้างข้อมูลตัวอย่าง
        sample_data = {
            'datasets': [
                {
                    'title': 'ชุดข้อมูลตัวอย่าง 1',
                    'organization': 'หน่วยงาน A',
                    'resource_count': 2,
                    'file_types': 'CSV, JSON',
                    'last_updated': '2024-03-20',
                    'package_id': 'sample-1',
                    'url': 'https://example.com/1'
                },
                {
                    'title': 'ชุดข้อมูลตัวอย่าง 2',
                    'organization': 'หน่วยงาน B',
                    'resource_count': 3,
                    'file_types': 'PDF, XLSX',
                    'last_updated': '2024-03-21',
                    'package_id': 'sample-2',
                    'url': 'https://example.com/2'
                }
            ],
            'resources': [
                {
                    'dataset_id': 'sample-1',
                    'file_name': 'data1.csv',
                    'format': 'CSV',
                    'url': 'https://example.com/1/csv',
                    'description': 'ข้อมูล CSV',
                    'ranking': 4
                },
                {
                    'dataset_id': 'sample-1',
                    'file_name': 'data1.json',
                    'format': 'JSON',
                    'url': 'https://example.com/1/json',
                    'description': 'ข้อมูล JSON',
                    'ranking': 4
                },
                {
                    'dataset_id': 'sample-2',
                    'file_name': 'data2.pdf',
                    'format': 'PDF',
                    'url': 'https://example.com/2/pdf',
                    'description': 'ข้อมูล PDF',
                    'ranking': 4
                },
                {
                    'dataset_id': 'sample-2',
                    'file_name': 'data2.xlsx',
                    'format': 'XLSX',
                    'url': 'https://example.com/2/xlsx',
                    'description': 'ข้อมูล XLSX',
                    'ranking': 4
                }
            ]
        }
        
        # บันทึกข้อมูลตัวอย่าง
        if db.init_sample_data(sample_data):
            df = pd.DataFrame(sample_data['datasets'])
            return True, "✅ สร้างข้อมูลตัวอย่างสำเร็จ", df
        return False, "❌ ไม่สามารถสร้างข้อมูลตัวอย่างได้", None
    except Exception as e:
        return False, f"❌ เกิดข้อผิดพลาดในการสร้างข้อมูลตัวอย่าง: {str(e)}", None

def main(silent=False):
    """
    ตรวจสอบและจัดการข้อมูล
    
    Args:
        silent (bool): ถ้าเป็น True จะไม่แสดงข้อความสถานะ
    
    Returns:
        tuple: (success, message, df)
            - success: bool สถานะการทำงาน
            - message: str ข้อความแสดงผล
            - df: DataFrame ข้อมูลที่โหลดมา
    """
    db = Database()
    db_exists = check_database()
    
    if not silent:
        print(f"🗄️ ฐานข้อมูล SQLite: {'✅ พร้อมใช้งาน' if db_exists else '❌ ไม่พบไฟล์'}")
    
    try:
        # ตรวจสอบข้อมูลที่มีอยู่
        if db_exists:
            datasets = db.get_datasets()
            if datasets:
                df = pd.DataFrame(datasets)
                return True, "✅ โหลดข้อมูลสำเร็จ", df
        
        # ถ้าไม่มีข้อมูล สร้างข้อมูลตัวอย่าง
        return create_sample_data(db)

    except Exception as e:
        return False, f"❌ เกิดข้อผิดพลาดในการจัดการข้อมูล: {str(e)}", None

if __name__ == "__main__":
    success, message, df = main()
    print(message)
    if success and df is not None:
        print(f"จำนวนข้อมูลที่โหลด: {len(df)} รายการ")