import json
import streamlit as st

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
    """แปลงประเภทไฟล์เป็นไอคอนและลิงก์"""
    file_types_str = row['ประเภทไฟล์']
    dataset_id = row['package_id']
    
    if not file_types_str:
        return ''
    
    try:
        with open('data/dataset_files.json', 'r', encoding='utf-8') as f:
            all_files = json.load(f)
        
        dataset_files = [f for f in all_files if f['dataset_id'] == dataset_id]
        
        file_links = []
        for file in dataset_files:
            file_type = file.get('format', '').strip().upper()
            if file_type:
                icon = get_file_type_icon(file_type)
                url = file.get('url', '')
                name = file.get('file_name', '')
                
                if url:
                    link = f'''
                        <a href="{url}" target="_blank" alt="{name}" title="{name}">
                            <span class="file-type">
                                {icon}
                                <span class="format-text">{file_type}</span>
                            </span>
                        </a>
                    '''
                    file_links.append(link)
                else:
                    file_links.append(f'<span class="file-type">{icon} {file_type}</span>')
        
        return ' '.join(file_links) if file_links else file_types_str
        
    except Exception as e:
        print(f"ไม่สามารถอ่านข้อมูลไฟล์: {str(e)}")
        return file_types_str 