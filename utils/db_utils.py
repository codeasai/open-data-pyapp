import sqlite3
import json
from pathlib import Path
import threading

class Database:
    def __init__(self):
        # สร้างโฟลเดอร์ data ถ้ายังไม่มี
        Path("data").mkdir(exist_ok=True)
        self._local = threading.local()
        self._create_tables()
    
    @property
    def conn(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect('data/database.sqlite')
        return self._local.conn
    
    def close(self):
        """ปิดการเชื่อมต่อ"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn
    
    def _create_tables(self):
        """สร้างตารางในฐานข้อมูล"""
        conn = sqlite3.connect('data/database.sqlite')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                package_id TEXT PRIMARY KEY,
                title TEXT,
                organization TEXT,
                url TEXT,
                resource_count INTEGER,
                file_types TEXT,
                last_updated TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT,
                file_name TEXT,
                format TEXT,
                url TEXT,
                description TEXT,
                ranking INTEGER DEFAULT 0,
                FOREIGN KEY (dataset_id) REFERENCES datasets(package_id)
            )
        """)
        conn.commit()
        conn.close()
    
    def __del__(self):
        """ปิดการเชื่อมต่อเมื่อ object ถูกทำลาย"""
        self.close()
    
    def migrate_from_json(self):
        """ย้ายข้อมูลจาก JSON เข้า SQLite"""
        try:
            # ตรวจสอบว่ามีไฟล์ JSON หรือไม่
            json_files = {
                'datasets': 'data/datasets_info.json',
                'resources': 'data/dataset_files.json'
            }

            for name, path in json_files.items():
                if not Path(path).exists():
                    print(f"❌ ไม่พบไฟล์ {path}")
                    return False

            # ย้ายข้อมูล datasets
            with open('data/datasets_info.json', 'r', encoding='utf-8') as f:
                datasets = json.load(f)
                for dataset in datasets:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO datasets 
                        (package_id, title, organization, url, resource_count, file_types, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dataset['package_id'],
                        dataset['title'],
                        dataset['organization'],
                        dataset['url'],
                        dataset['resource_count'],
                        dataset['file_types'],
                        dataset['last_updated']
                    ))
            
            # ย้ายข้อมูล resources และ rankings
            with open('data/dataset_files.json', 'r', encoding='utf-8') as f:
                resources = json.load(f)
            
            for resource in resources:
                ranking = resource.get('ranking', 0)  # ใช้ ranking จาก resource โดยตรง
                self.conn.execute("""
                    INSERT OR REPLACE INTO resources 
                    (dataset_id, file_name, format, url, description, ranking)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    resource['dataset_id'],
                    resource['file_name'],
                    resource['format'],
                    resource['url'],
                    resource.get('description', ''),
                    ranking
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error migrating data: {str(e)}")
            return False
    
    def get_datasets(self):
        """ดึงข้อมูลทั้งหมดจากตาราง datasets"""
        cursor = self.conn.execute("""
            SELECT 
                package_id,
                title,
                organization,
                url,
                resource_count,
                file_types,
                last_updated
            FROM datasets
        """)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_dataset_files(self, dataset_id):
        """ดึงข้อมูลไฟล์ของ dataset ที่ระบุ"""
        cursor = self.conn.execute(
            "SELECT * FROM resources WHERE dataset_id = ?", 
            (dataset_id,)
        )
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_dataset_ranking(self, dataset_id, ranking):
        """อัพเดท ranking ของ dataset"""
        try:
            self.conn.execute(
                "UPDATE resources SET ranking = ? WHERE dataset_id = ?",
                (ranking, dataset_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating ranking: {str(e)}")
            return False
    
    def update_dataset(self, dataset_data, resources_data):
        """อัพเดทข้อมูล dataset และ resources"""
        try:
            # อัพเดทข้อมูล dataset
            self.conn.execute("""
                INSERT OR REPLACE INTO datasets 
                (package_id, title, organization, url, resource_count, file_types, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_data['package_id'],
                dataset_data['title'],
                dataset_data['organization'],
                dataset_data['url'],
                dataset_data['resource_count'],
                dataset_data['file_types'],
                dataset_data['last_updated']
            ))
            
            # ลบ resources เก่า
            self.conn.execute(
                "DELETE FROM resources WHERE dataset_id = ?",
                (dataset_data['package_id'],)
            )
            
            # เพิ่ม resources ใหม่
            for resource in resources_data:
                self.conn.execute("""
                    INSERT INTO resources 
                    (dataset_id, file_name, format, url, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    resource['dataset_id'],
                    resource['file_name'],
                    resource['format'],
                    resource['url'],
                    resource.get('description', '')
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating dataset: {str(e)}")
            return False
    
    def init_sample_data(self, data):
        """เพิ่มข้อมูลตัวอย่าง"""
        try:
            # เพิ่มข้อมูล datasets
            for dataset in data['datasets']:
                self.conn.execute("""
                    INSERT OR REPLACE INTO datasets 
                    (package_id, title, organization, url, resource_count, file_types, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    dataset['package_id'],
                    dataset['title'],
                    dataset['organization'],
                    dataset['url'],
                    dataset['resource_count'],
                    dataset['file_types'],
                    dataset['last_updated']
                ))
            
            # เพิ่มข้อมูล resources
            for resource in data['resources']:
                self.conn.execute("""
                    INSERT OR REPLACE INTO resources 
                    (dataset_id, file_name, format, url, description, ranking)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    resource['dataset_id'],
                    resource['file_name'],
                    resource['format'],
                    resource['url'],
                    resource['description'],
                    resource['ranking']
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error initializing sample data: {str(e)}")
            return False 