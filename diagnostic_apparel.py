import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss11380","https://b2b.fjordnansen.com/product-eng-48786-TOUR-MERINO-KEVLAR-socks.html"],["ss10997","https://b2b.fjordnansen.com/product-eng-47549-NEW-TOUR-MERINO-KEVLAR-socks.html"],["ss10817","https://b2b.fjordnansen.com/product-eng-46904-NEW-TOUR-MERINO-KEVLAR-socks.html"],["ss10314","https://b2b.fjordnansen.com/product-eng-46141-NIS-SNEAKER-KEVLAR-Socks.html"],["ss10309","https://b2b.fjordnansen.com/product-eng-46127-TRIP-LONG-socks.html"],["ss9498","https://b2b.fjordnansen.com/product-eng-44781-SKI-KEVLAR-Socks.html"],["ss8396","https://b2b.fjordnansen.com/product-eng-42191-NEW-STRIPE-SOCKS.html"],["ss8389","https://b2b.fjordnansen.com/product-eng-42183-NEW-MOUNTAIN-KEVLAR-SOCKS.html"],["ss8388","https://b2b.fjordnansen.com/product-eng-42182-NIS-SNEAKER-KEVLAR-SOCKS.html"],["ss8375","https://b2b.fjordnansen.com/product-eng-42145-NEW-HIKE-KEVLAR-SOCKS.html"],["ss8374","https://b2b.fjordnansen.com/product-eng-42144-SCOV-SOCKS.html"],["ss8373","https://b2b.fjordnansen.com/product-eng-42143-TREK-KEVLAR-SOCKS.html"],["ss8372","https://b2b.fjordnansen.com/product-eng-42142-AXTER-KEVLAR-SOCKS.html"],["ss8371","https://b2b.fjordnansen.com/product-eng-42140-REVLE-ANTI-MOSQUITO-anti-tick-socks.html"],["ss8368","https://b2b.fjordnansen.com/product-eng-42135-NEW-HIKE-LOW-KEVLAR-SOCKS.html"],["ss7472","https://b2b.fjordnansen.com/product-eng-39415-HIKE-WATERPROOF-waterproof-socks.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  rows=[]
  for b in s.select(".projector_versions__size"):
   text=clean(" ".join(b.stripped_strings))
   if not text: continue
   q=b.select_one(".projector_versions__quantity[data-amount]")
   raw=clean(q.get("data-amount")) if q else ""
   qty=int(raw) if raw.isdigit() else None
   unavailable=b.select_one(".projector_versions__tell_availability") is not None
   rows.append({"label":text.split(" ")[0],"quantity":0 if unavailable and qty is None else qty,"unavailable":unavailable,"text":text[:180]})
  print("SOCK "+sku+" "+json.dumps(rows,ensure_ascii=False),flush=True); time.sleep(1.1)
if __name__=="__main__": main()
