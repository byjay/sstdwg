import pandas as pd

def read_excel_file(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.to_dict(orient='records')
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        data = read_excel_file(file_path)
        print(data)
    else:
        print('Usage: python read_excel.py <file_path>')

