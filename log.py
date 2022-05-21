from config import DEBUG

def logD(log:str):
    if not DEBUG: return
    print("[DEBUG] "+str(log))

def logDE(e):
    if not DEBUG: return
    print(f"[Exception] {type(e)} : {e}")