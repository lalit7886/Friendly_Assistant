import logfire
from unstructured.partition.auto import partition

def parse_office(file_path:str):
    with logfire.span("Starting Office parser",filename=file_path):
        try:
            elements=partition(file_path)
            full_text = "\n".join([str(el) for el in elements])
            
            if full_text.split():
                logfire.info("Sucssfully parsed the office file ")
                
            else:
                logfire.warning(f"failed to parse office file {file_path}")
            
            return full_text
        except Exception as e:
            logfire.error(f"office parse failed as {e}")
            raise e
        