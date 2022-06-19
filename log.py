from config import DEBUG, DEBUG_ERROR

def logD(log:str):
    if not DEBUG: return
    print("[DEBUG] "+str(log))

def logDE(e):
    if not DEBUG_ERROR: return
    print(f"[Exception] {type(e)} : {e}")