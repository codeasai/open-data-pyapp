import json
import streamlit as st
from utils.data_utils import get_dataset_files

def get_file_type_icon(file_type):
    """แปลงประเภทไฟล์เป็นไอคอน"""
    icon_map = {
        'PDF': '📄',
        'JSON': '📋',
        'CSV': '📊',
        'XLSX': '📑',
        'XLS': '📑',
        'DOC': '📝',
        'DOCX': '📝',
        'XML': '📰',
        'ZIP': '📦',
        'RAR': '📦',
        'TXT': '📝',
    }
    return icon_map.get(file_type.upper(), '📎')

def format_file_types(row):
    """จัดรูปแบบการแสดงผลประเภทไฟล์"""
    if not row.get('ประเภทไฟล์'):
        return ""
    
    # กำหนดสีและไอคอนสำหรับแต่ละประเภทไฟล์
    file_type_styles = {
        'CSV': {'color': '#28a745', 'icon': '📊'},
        'JSON': {'color': '#ffc107', 'icon': '📝'},
        'XML': {'color': '#17a2b8', 'icon': '📋'},
        'XLS': {'color': '#28a745', 'icon': '📗'},
        'XLSX': {'color': '#28a745', 'icon': '📗'},
        'PDF': {'color': '#dc3545', 'icon': '📕'},
        'DOC': {'color': '#007bff', 'icon': '📘'},
        'DOCX': {'color': '#007bff', 'icon': '📘'},
        'ZIP': {'color': '#6c757d', 'icon': '📦'},
        'RAR': {'color': '#6c757d', 'icon': '📦'},
        'TXT': {'color': '#6c757d', 'icon': '📄'},
        'HTML': {'color': '#e83e8c', 'icon': '🌐'},
        'KML': {'color': '#20c997', 'icon': '🗺️'},
        'KMZ': {'color': '#20c997', 'icon': '🗺️'},
        'SHP': {'color': '#6f42c1', 'icon': '🗺️'},
        'GDB': {'color': '#6f42c1', 'icon': '🗺️'},
        'GEOJSON': {'color': '#20c997', 'icon': '🗺️'},
        'SQL': {'color': '#fd7e14', 'icon': '💾'},
        'MDB': {'color': '#fd7e14', 'icon': '💾'},
        'ACCDB': {'color': '#fd7e14', 'icon': '💾'},
        'ODS': {'color': '#28a745', 'icon': '📊'},
        'ODB': {'color': '#fd7e14', 'icon': '💾'},
        'ODT': {'color': '#007bff', 'icon': '📘'},
        'JPG': {'color': '#e83e8c', 'icon': '🖼️'},
        'JPEG': {'color': '#e83e8c', 'icon': '🖼️'},
        'PNG': {'color': '#e83e8c', 'icon': '🖼️'},
        'GIF': {'color': '#e83e8c', 'icon': '🖼️'},
        'SVG': {'color': '#e83e8c', 'icon': '🖼️'},
        'MP4': {'color': '#6f42c1', 'icon': '🎥'},
        'MP3': {'color': '#6f42c1', 'icon': '🎵'},
        'WAV': {'color': '#6f42c1', 'icon': '🎵'}
    }
    
    try:
        # ดึงข้อมูลไฟล์ของ dataset นี้
        dataset_files = get_dataset_files(row['package_id'])
        file_urls = {f['format'].upper(): f['url'] for f in dataset_files if f.get('format') and f.get('url')}
        
        # แยกประเภทไฟล์และสร้าง HTML
        file_types = [t.strip().upper() for t in str(row['ประเภทไฟล์']).split(',')]
        formatted_types = []
        
        for file_type in file_types:
            if not file_type:  # ข้ามถ้าเป็นค่าว่าง
                continue
                
            style = file_type_styles.get(file_type, {'color': '#6c757d', 'icon': '📄'})
            url = file_urls.get(file_type, '')
            
            if url:
                formatted_types.append(
                    f"""<a href="{url}" target="_blank" style="text-decoration: none;">
                        <span style="
                            display: inline-block;
                            padding: 2px 8px;
                            margin: 2px;
                            border-radius: 12px;
                            background-color: {style['color']};
                            color: white;
                            font-size: 0.8em;
                            white-space: nowrap;
                            cursor: pointer;
                        ">{style['icon']} {file_type}</span>
                    </a>"""
                )
            else:
                formatted_types.append(
                    f"""<span style="
                        display: inline-block;
                        padding: 2px 8px;
                        margin: 2px;
                        border-radius: 12px;
                        background-color: {style['color']};
                        color: white;
                        font-size: 0.8em;
                        white-space: nowrap;
                    ">{style['icon']} {file_type}</span>"""
                )
        
        return ' '.join(formatted_types)
    except Exception as e:
        print(f"Error in format_file_types: {str(e)}")
        return ""  # คืนค่าว่างถ้าเกิดข้อผิดพลาด 