import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss10935","https://b2b.fjordnansen.com/product-eng-47445-LIGHT-MERINOULL-BEANIE-Cap.html"],["ss10755/mw","https://b2b.fjordnansen.com/product-eng-46738-LIGHT-MERINOULL-BEANIE-Cap.html"],["ss10750/mw","https://b2b.fjordnansen.com/product-eng-46733-HYGGE-BEANIE-Cap.html"],["ss10749/mw","https://b2b.fjordnansen.com/product-eng-46732-HYGGE-BEANIE-Cap.html"],["ss10748/mw","https://b2b.fjordnansen.com/product-eng-46731-HYGGE-BEANIE-Cap.html"],["ss10747/mw","https://b2b.fjordnansen.com/product-eng-46730-HYGGE-BEANIE-Cap.html"],["ss5613","https://b2b.fjordnansen.com/product-eng-35043-FALL-200-cap.html"],["ss2581","https://b2b.fjordnansen.com/product-eng-25028-FALL-WIND-Cap.html"],["32050","https://b2b.fjordnansen.com/product-eng-4212-FALL-cap.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 out=[]
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
  row=parse_product(r.text,r.url)
  nodes=[]
  for q in soup.select("[data-amount]"):
   raw=clean(q.get("data-amount"))
   if not raw or not raw.isdigit(): continue
   parent=q
   text=""
   for _ in range(5):
    if parent is None: break
    t=clean(" ".join(parent.stripped_strings))
    if len(t)>len(text): text=t
    parent=parent.parent
   nodes.append({"name":q.get("name"),"amount":int(raw),"text":text[:240]})
  item={"sku":sku,"stock":row.get("supplier_stock"),"availability":row.get("availability"),"nodes":nodes}
  out.append(item); print("HAT "+sku+" "+json.dumps(item,ensure_ascii=False),flush=True); time.sleep(1.2)
 print("HATS_ALL="+json.dumps(out,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
