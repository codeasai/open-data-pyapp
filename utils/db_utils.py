import sqlite3
import json
from pathlib import Path

class Database:
    def __init__(self):
        # สร้างโฟลเดอร์ data ถ้ายังไม่มี
        Path("data").mkdir(exist_ok=True)
        self.conn = sqlite3.connect('data/database.sqlite')
        self.create_tables()
    
    def create_tables(self):
        """สร้างตารางในฐานข้อมูล"""
        self.conn.execute("""
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
        
        self.conn.execute("""
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
        self.conn.commit()
    
    def migrate_from_json(self):
        """ย้ายข้อมูลจาก JSON เข้า SQLite"""
        try:
            # ย้ายข้อมูล datasets
            with open('data/processed/datasets.json', 'r', encoding='utf-8') as f:
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
            with open('data/processed/resources.json', 'r', encoding='utf-8') as f:
                resources = json.load(f)
            with open('data/processed/rankings.json', 'r', encoding='utf-8') as f:
                rankings = json.load(f)
                
            for resource in resources:
                ranking = rankings.get(resource['dataset_id'], 0)
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
        cursor = self.conn.execute("SELECT * FROM datasets")
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