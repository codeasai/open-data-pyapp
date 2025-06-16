import sys
import os

# เพิ่ม path ของโปรเจคเข้าไปใน sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.api_utils import get_api_client
import json

def test_organization_show():
    # สร้าง client สำหรับเรียกใช้ API
    client = get_api_client()
    
    if client:
        # ทดสอบการเชื่อมต่อพื้นฐาน
        try:
            result = client.test_connection()
            if result:
                print("✅ เชื่อมต่อสำเร็จ")
                
                # แสดงข้อมูล API
                print("#### 📋 ข้อมูล API")
                print(f"- Base URL: {client.base_url}")
                print(f"- API Version: {client.api_version}")
                print(f"- Authentication: Bearer Token")
            else:
                print("❌ ไม่สามารถเชื่อมต่อได้")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")

        # ทดสอบดึงข้อมูลหน่วยงาน
        try:
            success, orgs = client.get_organizations()
            if success and orgs:
                print(f"✅ ดึงข้อมูลสำเร็จ ({len(orgs)} หน่วยงาน)")
                # แสดงข้อมูลหน่วยงาน
                if isinstance(orgs, list) and len(orgs) > 0:
                    if isinstance(orgs[0], dict):
                        orgs_df = pd.DataFrame(orgs)
                        print(orgs_df.head(10))
                    else:
                        print(orgs[:10])
                else:
                    print(orgs)
            else:
                print("❌ ไม่สามารถดึงข้อมูลได้")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
    else:
        print("❌ ไม่สามารถเชื่อมต่อกับ API ได้ กรุณาตรวจสอบ API key")

def test_package_show():
    client = get_api_client()
    if not client:
        print("❌ ไม่สามารถเชื่อมต่อกับ API ได้ กรุณาตรวจสอบ API key")
        return
    # ตัวอย่าง package_id (ควรเปลี่ยนเป็น id ที่มีจริงในระบบ)
    sample_package_id = "sample"
    print(f"\n🔎 ทดสอบ package_show ด้วย package_id: {sample_package_id}")
    try:
        success, data = client._make_request("package_show", {"id": sample_package_id})
        if success:
            print("✅ package_show สำเร็จ")
            # แสดงข้อมูลบางส่วน
            if isinstance(data, dict):
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
            else:
                print(data)
        else:
            print(f"❌ package_show ไม่สำเร็จ: {data.get('error', data)}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    test_organization_show()
    test_package_show() 