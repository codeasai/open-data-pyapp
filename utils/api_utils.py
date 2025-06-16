import requests
import json
import streamlit as st
from typing import Dict, List, Tuple, Optional
import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataGoAPI:
    """คลาสสำหรับจัดการการเชื่อมต่อกับ data.go.th API"""
    
    BASE_URL = "https://data.go.th"
    API_VERSION = "3"
    
    def __init__(self, api_key: str):
        """เริ่มต้น API client
        
        Args:
            api_key (str): API key สำหรับการเชื่อมต่อ
        """
        self.api_key = api_key
        self.headers = {
            'Authorization': f"Bearer {api_key}",
            'Accept': 'application/json'
        }
        self.base_url = self.BASE_URL
        self.api_version = self.API_VERSION
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Tuple[bool, Dict]:
        """ทำการเรียก API
        
        Args:
            endpoint (str): API endpoint
            params (Dict, optional): พารามิเตอร์สำหรับ request
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, ข้อมูลที่ได้รับ)
        """
        url = f"{self.base_url}/api/{self.api_version}/action/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return False, {"error": str(e)}
    
    def test_connection(self) -> Tuple[bool, str]:
        """ทดสอบการเชื่อมต่อกับ API
        
        Returns:
            Tuple[bool, str]: (สำเร็จหรือไม่, ข้อความ)
        """
        success, data = self._make_request("site_read")
        if success:
            return True, "เชื่อมต่อสำเร็จ"
        return False, f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {data.get('error', 'ไม่ทราบสาเหตุ')}"
    
    def get_organizations(self) -> Tuple[bool, List[Dict]]:
        """ดึงข้อมูลรายการหน่วยงาน
        
        Returns:
            Tuple[bool, List[Dict]]: (สำเร็จหรือไม่, รายการหน่วยงาน)
        """
        success, data = self._make_request("organization_list")
        if success and isinstance(data, dict) and 'result' in data:
            return True, data['result']
        return False, []
    
    def get_organization_details(self, org_id: str) -> Tuple[bool, Dict]:
        """ดึงรายละเอียดของหน่วยงาน
        
        Args:
            org_id (str): รหัสหน่วยงาน
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, รายละเอียดหน่วยงาน)
        """
        success, data = self._make_request("organization_show", {"id": org_id})
        if success and isinstance(data, dict) and 'result' in data:
            return True, data['result']
        return False, {}
    
    def get_organization_datasets(self, org_id: str) -> Tuple[bool, List[Dict]]:
        """ดึงข้อมูลชุดข้อมูลของหน่วยงาน
        
        Args:
            org_id (str): รหัสหน่วยงาน
            
        Returns:
            Tuple[bool, List[Dict]]: (สำเร็จหรือไม่, รายการชุดข้อมูล)
        """
        success, data = self._make_request("organization_activity_list", {"id": org_id})
        if success and isinstance(data, dict) and 'result' in data:
            return True, data['result']
        return False, []

class GDCatalogAPI:
    """คลาสสำหรับจัดการการเชื่อมต่อกับ GDCatalog API"""
    
    def __init__(self):
        """เริ่มต้น API client"""
        self.headers = {
            'Accept': 'application/json'
        }
    
    def _make_request(self, url: str, params: Dict = None) -> Tuple[bool, Dict]:
        """ทำการเรียก API
        
        Args:
            url (str): URL สำหรับเรียก API
            params (Dict, optional): พารามิเตอร์สำหรับ request
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, ข้อมูลที่ได้รับ)
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GDCatalog API request failed: {str(e)}")
            return False, {"error": str(e)}
    
    def get_datasets(self, province: str = None) -> Tuple[bool, Dict]:
        """ดึงข้อมูลชุดข้อมูลจาก GDCatalog
        
        Args:
            province (str, optional): ชื่อจังหวัดที่ต้องการดึงข้อมูล
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, ข้อมูลที่ได้รับ)
        """
        if province:
            url = f"https://{province}.gdcatalog.go.th/api/datasets"
        else:
            url = "https://gdcatalog.go.th/api/datasets"
        return self._make_request(url)
    
    def get_dataset_details(self, dataset_id: str, province: str = None) -> Tuple[bool, Dict]:
        """ดึงรายละเอียดชุดข้อมูล
        
        Args:
            dataset_id (str): รหัสชุดข้อมูล
            province (str, optional): ชื่อจังหวัดที่ต้องการดึงข้อมูล
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, ข้อมูลที่ได้รับ)
        """
        if province:
            url = f"https://{province}.gdcatalog.go.th/api/datasets/{dataset_id}"
        else:
            url = f"https://gdcatalog.go.th/api/datasets/{dataset_id}"
        return self._make_request(url)

class GovSpendingAPI:
    """คลาสสำหรับจัดการการเชื่อมต่อกับ Government Spending API"""
    
    BASE_URL = "https://opend.data.go.th"
    
    def __init__(self, api_key: str):
        """เริ่มต้น API client
        
        Args:
            api_key (str): API key สำหรับการเชื่อมต่อ
        """
        self.api_key = api_key
        self.headers = {
            'Accept': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Tuple[bool, Dict]:
        """ทำการเรียก API
        
        Args:
            endpoint (str): API endpoint
            params (Dict, optional): พารามิเตอร์สำหรับ request
            
        Returns:
            Tuple[bool, Dict]: (สำเร็จหรือไม่, ข้อมูลที่ได้รับ)
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # เพิ่ม API key ใน params
        if params is None:
            params = {}
        params['api-key'] = self.api_key
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Government Spending API request failed: {str(e)}")
            return False, {"error": str(e)}
    
    def test_connection(self) -> Tuple[bool, str]:
        """ทดสอบการเชื่อมต่อกับ API
        
        Returns:
            Tuple[bool, str]: (สำเร็จหรือไม่, ข้อความ)
        """
        success, data = self.get_departments(limit=1)
        if success:
            return True, "เชื่อมต่อสำเร็จ"
        return False, f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {data.get('error', 'ไม่ทราบสาเหตุ')}"
    
    def get_departments(self, offset: int = 0, limit: int = 1000) -> Tuple[bool, List[Dict]]:
        """ดึงข้อมูลรายการหน่วยงาน
        
        Args:
            offset (int): จุดเริ่มต้นของข้อมูล
            limit (int): จำนวนข้อมูลที่ต้องการ
            
        Returns:
            Tuple[bool, List[Dict]]: (สำเร็จหรือไม่, รายการหน่วยงาน)
        """
        params = {
            'offset': offset,
            'limit': limit
        }
        success, data = self._make_request("govspending/egpdepartment", params)
        if success and isinstance(data, dict):
            # ตรวจสอบโครงสร้างข้อมูลที่ได้รับ
            if 'result' in data:
                return True, data['result']
            elif isinstance(data, list):
                return True, data
            else:
                return True, [data] if data else []
        return False, []

def get_api_client() -> Optional[DataGoAPI]:
    """สร้าง API client จาก API key ที่เก็บไว้ใน secrets
    
    Returns:
        Optional[DataGoAPI]: API client หรือ None ถ้าไม่พบ API key
    """
    try:
        api_key = st.secrets["DATA_GO_TH_API_KEY"]
        return DataGoAPI(api_key)
    except Exception as e:
        logger.error(f"Failed to create API client: {str(e)}")
        return None

def get_govspending_client() -> Optional[GovSpendingAPI]:
    """สร้าง Government Spending API client
    
    Returns:
        Optional[GovSpendingAPI]: API client หรือ None ถ้าไม่พบ API key
    """
    try:
        # ใช้ API key เดียวกันหรือสร้าง key ใหม่สำหรับ Government Spending API
        api_key = "lOKImv9DFtADXhgA0GlmGBVPzQxvAGOz"  # API key ที่ระบุในคำขอ
        return GovSpendingAPI(api_key)
    except Exception as e:
        logger.error(f"Failed to create Government Spending API client: {str(e)}")
        return None

def test_all_endpoints() -> Dict[str, Tuple[bool, str]]:
    """ทดสอบการเชื่อมต่อกับทุก endpoint
    
    Returns:
        Dict[str, Tuple[bool, str]]: ผลการทดสอบแต่ละ endpoint
    """
    results = {}
    
    # ทดสอบ DataGo API
    client = get_api_client()
    if client:
        endpoints = [
            "site_read",
            "organization_list",
            "organization_show",
            "organization_activity_list"
        ]
        
        for endpoint in endpoints:
            success, data = client._make_request(endpoint)
            if success:
                results[endpoint] = (True, "เชื่อมต่อสำเร็จ")
            else:
                results[endpoint] = (False, data.get("error", "ไม่ทราบสาเหตุ"))
    else:
        results["api_client"] = (False, "ไม่สามารถสร้าง API client ได้")
    
    # ทดสอบ GDCatalog API
    gdcatalog = GDCatalogAPI()
    success, data = gdcatalog.get_datasets()
    if success:
        results["gdcatalog"] = (True, "เชื่อมต่อสำเร็จ")
    else:
        results["gdcatalog"] = (False, data.get("error", "ไม่ทราบสาเหตุ"))
    
    # ทดสอบ Government Spending API
    govspending = get_govspending_client()
    if govspending:
        success, message = govspending.test_connection()
        results["govspending_departments"] = (success, message)
    else:
        results["govspending_departments"] = (False, "ไม่สามารถสร้าง Government Spending API client ได้")
    
    return results 