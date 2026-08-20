# import logfire
 
# def parse_text(file_path:str):
#     with logfire.span("Started text parsing"):
#         try:
#             with open(file_path,'r','utf-8',errors="ignore") as f:
#                 if f.read().split():
#                     logfire.info("Succesfully parsed text")
#                     return f.read()
#                 else:
#                     logfire.warning(f"unable to parse the text {file_path}")
#         except Exception as e:
#             logfire.error(f"Failed text parsing {file_path}: {e}")
#             raise e
                
    
import logfire

def parse_text(file_path: str):
    """
    Parses plain text files.
    """
    with logfire.span("📄 Text Parsing", filename=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logfire.error(f"❌ Text Parse Failed: {e}")
            raise e