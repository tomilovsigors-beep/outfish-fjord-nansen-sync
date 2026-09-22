import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss8374","https://b2b.fjordnansen.com/product-eng-42144-SCOV-SOCKS.html"],["ss7472","https://b2b.fjordnansen.com/product-eng-39415-HIKE-WATERPROOF-waterproof-socks.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  rows=[]
  for b in s.select(".projector_versions__sub"):
   text=clean(" ".join(b.stripped_strings))
   if not text: continue
   q=b.select_one(".projector_versions__quantity[data-amount]")
   raw=clean(q.get("data-amount")) if q else ""
   qty=int(raw) if raw.isdigit() else None
   un=b.select_one(".projector_versions__tell_availability") is not None or "Unavailable" in text
   rows.append({"text":text[:500],"quantity":0 if un and qty is None else qty,"unavailable":un})
  print("SOCK_SIZEBLOCKS "+sku+" "+json.dumps(rows,ensure_ascii=False),flush=True); time.sleep(1)
if __name__=="__main__": main()
