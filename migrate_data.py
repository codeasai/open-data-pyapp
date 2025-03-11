from utils.db_utils import Database

def main():
    db = Database()
    if db.migrate_from_json():
        print("✅ ย้ายข้อมูลสำเร็จ")
    else:
        print("❌ เกิดข้อผิดพลาดในการย้ายข้อมูล")

if __name__ == "__main__":
    main() 