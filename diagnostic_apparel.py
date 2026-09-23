import json,re
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
URL="https://b2b.fjordnansen.com/product-eng-23024-BIVAK-8-C-1190g-sleeping-bag.html"
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 r=c.session.get(URL,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
 classes=[]
 for tag in s.find_all(True):
  cls=" ".join(tag.get("class") or [])
  if cls and any(k in cls.lower() for k in ["desc","param","trait","spec","projector","dictionary","long"]):
   txt=clean(" ".join(tag.stripped_strings))
   if 20 <= len(txt) <= 4000:
    classes.append({"tag":tag.name,"class":cls,"text":txt[:3500]})
 print("CANDIDATES="+json.dumps(classes[:120],ensure_ascii=False),flush=True)
if __name__=="__main__": main()
