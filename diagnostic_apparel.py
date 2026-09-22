import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss11380","https://b2b.fjordnansen.com/product-eng-48786-TOUR-MERINO-KEVLAR-socks.html"],["ss10309","https://b2b.fjordnansen.com/product-eng-46127-TRIP-LONG-socks.html"],["ss9498","https://b2b.fjordnansen.com/product-eng-44781-SKI-KEVLAR-Socks.html"],["ss8389","https://b2b.fjordnansen.com/product-eng-42183-NEW-MOUNTAIN-KEVLAR-SOCKS.html"],["ss8375","https://b2b.fjordnansen.com/product-eng-42145-NEW-HIKE-KEVLAR-SOCKS.html"],["ss8374","https://b2b.fjordnansen.com/product-eng-42144-SCOV-SOCKS.html"],["ss8373","https://b2b.fjordnansen.com/product-eng-42143-TREK-KEVLAR-SOCKS.html"],["ss8372","https://b2b.fjordnansen.com/product-eng-42142-AXTER-KEVLAR-SOCKS.html"],["ss8371","https://b2b.fjordnansen.com/product-eng-42140-REVLE-ANTI-MOSQUITO-anti-tick-socks.html"],["ss8368","https://b2b.fjordnansen.com/product-eng-42135-NEW-HIKE-LOW-KEVLAR-SOCKS.html"],["ss7472","https://b2b.fjordnansen.com/product-eng-39415-HIKE-WATERPROOF-waterproof-socks.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  rows=[]
  for i,q in enumerate(s.select("[data-amount]")):
   raw=clean(q.get("data-amount"))
   if not raw or not raw.isdigit(): continue
   parent=q; text=""; classes=[]
   for d in range(6):
    if parent is None: break
    t=clean(" ".join(parent.stripped_strings))
    if len(t)>len(text): text=t
    classes.append(parent.get("class"))
    parent=parent.parent
   rows.append({"i":i,"name":q.get("name"),"amount":int(raw),"text":text[:300],"classes":classes})
  print("SOCK_NODES "+sku+" "+json.dumps(rows,ensure_ascii=False),flush=True); time.sleep(1.1)
if __name__=="__main__": main()
