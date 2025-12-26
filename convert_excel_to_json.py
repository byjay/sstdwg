import pandas as pd
import json
import os
import math

# 설정
EXCEL_FILE = r'f:\genmini\SSTDMS_project\BA21-OS-TOPS-CF-YU1002-EN_renamed_251021.xlsx'
JSON_OUTPUT_DIR = r'f:\genmini\SSTDMS_project\sstdms_mobile_app\data'
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, 'drawings.json')

def clean_value(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def convert_excel_to_json():
    print(f"Loading Excel: {EXCEL_FILE}")
    
    # 4번째 행(0-based index: 3)이 헤더인 것으로 확인됨 (header=4 means row 5 in Excel)
    # 이전 분석 결과 기반: header=4 used in previous analysis
    df = pd.read_excel(EXCEL_FILE, sheet_name='Drawing List TWP', header=4)
    
    # 컬럼 매핑 (실제 엑셀 헤더 -> JSON 키)
    # [3] YUIL SHOP DRAWING NUMBER\n(Internal Use)
    # [4] Contractor Dwg.-ID:\n(Include in drawing box)
    # [5] Employer Dwg.-ID: \n(Include in drawing box)
    # [6] DRAWING \nTITLE
    # [8] STR.CAT
    # [9] BLOCK
    # ...
    
    drawings = []
    
    # 유효한 데이터만 추출
    for index, row in df.iterrows():
        # 필수 값인 도면 번호가 없으면 스킵
        contractor_dwg = clean_value(row.iloc[4]) # Column index 4
        if not contractor_dwg:
            continue
            
        drawing = {
            "id": index,
            "shop_dwg_no": clean_value(row.iloc[3]),
            "contractor_dwg_no": contractor_dwg,
            "employer_dwg_no": clean_value(row.iloc[5]),
            "title": clean_value(row.iloc[6]),
            "category": clean_value(row.iloc[8]),
            "block": clean_value(row.iloc[9]),
            "location": clean_value(row.iloc[10]),
            "stage": clean_value(row.iloc[12]),
            "revision": clean_value(row.iloc[21]), # Current STATUS or DWG Rev
            "status": clean_value(row.iloc[22]),
            "date": clean_value(row.iloc[24])
        }
        drawings.append(drawing)
    
    # 디렉토리 생성
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    
    # JSON 저장
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(drawings, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully converted {len(drawings)} drawings to {JSON_OUTPUT_FILE}")

if __name__ == "__main__":
    convert_excel_to_json()
