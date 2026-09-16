import pandas as pd
from pathlib import Path

def read_excel_(file_path:str):
    try:
        xls = pd.ExcelFile(file_path)
        # print(xls.sheet_names)
        df=pd.read_excel(file_path,sheet_name="vw_service_report")
        # print("DataFrame shape:", df.shape)
        # print("Columns:", len(df.columns))
        # print("Rows:", len(df))
        chunks=[]

        columns_=df.columns
        for _, row in df.iterrows():

            chunk = ""

            for col in df.columns:

                value = row[col]

                if pd.isna(value):
                    continue

                chunk += f"{col}: {value}\n"
            
            chunk=chunk.strip()
            if chunk:
                chunks.append(chunk)
            # chunks.append("\n\n")
            
        return chunks
    except Exception as e:
        raise e
    
if __name__ == "__main__":
    file_path = Path(__file__).resolve().parents[3] / "DATA" / "improved1.xlsx"
    chunks=read_excel_(file_path)
    print(len(chunks))
    for chunk in chunks:
        print(chunk)
    