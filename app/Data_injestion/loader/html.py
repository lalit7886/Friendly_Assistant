from bs4 import BeautifulSoup
import logfire

def parse_html(file_path:str):
    with logfire.span("HTML Parsing",filename=file_path):
        try:
            with open(file_path,'r',encoding="utf-8",errors="ignore") as f:
                content=f.read()
                
            soup=BeautifulSoup(content,"html.parser")
            
            for script in soup(["script","style","meta","noscript"]):
                script.decompose()
                
            text_=soup.get_text(separator="\n")
            
            lines=[line.strip() for line in text_.splitlines() if line.strip()]
            chunks=[phrase.strip() for line in lines for phrase in line.split(" ")]
            text_clean = '\n'.join(chunk for chunk in chunks if chunk)
            return text_clean
        except Exception as e:
            logfire.error(f"HTML parse failed error : {e}")
            raise e
             
             
    