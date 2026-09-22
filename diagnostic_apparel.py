import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss12496","https://b2b.fjordnansen.com/product-eng-51007-BWAH-MEN-t-shirt.html"],["ss10317","https://b2b.fjordnansen.com/product-eng-46146-KJERAG-MEN-T-Shirt.html"],["ss9241","https://b2b.fjordnansen.com/product-eng-44375-BASIC-MEN-rocky-grey-t-shirt.html"],["ss9239","https://b2b.fjordnansen.com/product-eng-44373-SKOG-MEN-olive-t-shirt.html"],["ss9238","https://b2b.fjordnansen.com/product-eng-44372-NORTH-CAPE-MEN-navy-T-shirt.html"],["ss8042","https://b2b.fjordnansen.com/product-eng-41348-RIX-SPORTS-SLEEVELESS-MEN-T-Shirt.html"],["ss8041","https://b2b.fjordnansen.com/product-eng-41346-RIX-SPORTS-SLEEVELESS-MEN-T-Shirt.html"],["ss8015","https://b2b.fjordnansen.com/product-eng-41225-RIX-PRINT-T-shirt-Men.html"],["ss8014","https://b2b.fjordnansen.com/product-eng-41224-RIX-PRINT-T-SHIRT-MEN-T-Shirt.html"],["ss8013","https://b2b.fjordnansen.com/product-eng-41223-RIX-PRINT-T-SHIRT-MEN-T-Shirt.html"],["ss7901","https://b2b.fjordnansen.com/product-eng-40842-RIX-LONGSLEEVE-MEN-T-Shirt.html"],["ss7900","https://b2b.fjordnansen.com/product-eng-40841-RIX-LONGSLEEVE-MEN-T-Shirt.html"],["ss7899","https://b2b.fjordnansen.com/product-eng-40838-RIX-T-SHIRT-MEN-T-Shirt.html"],["ss7893","https://b2b.fjordnansen.com/product-eng-40758-RIX-T-SHIRT-MEN-T-Shirt.html"],["ss7892","https://b2b.fjordnansen.com/product-eng-40757-RIX-T-SHIRT-MEN-T-Shirt.html"],["ss7890","https://b2b.fjordnansen.com/product-eng-40747-RIX-T-SHIRT-MEN-T-Shirt.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def parse_sizes(html):
 s=BeautifulSoup(html,"html.parser"); out=[]
 for b in s.select(".projector_versions__size"):
  text=clean(" ".join(b.stripped_strings))
  if not text: continue
  q=b.select_one(".projector_versions__quantity[data-amount]")
  raw=clean(q.get("data-amount")) if q else ""
  qty=int(raw) if raw.isdigit() else None
  unavailable=b.select_one(".projector_versions__tell_availability") is not None
  label=text.split(" ")[0].upper().replace("XXL","2XL").replace("XXXL","3XL")
  out.append({"label":label,"quantity":0 if unavailable and qty is None else qty,"unavailable":unavailable,"text":text[:170]})
 return out
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 res=[]
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  sizes=parse_sizes(r.text); res.append({"sku":sku,"url":r.url,"sizes":sizes})
  pos=sum(1 for x in sizes if isinstance(x.get("quantity"),int) and x["quantity"]>0)
  print("FOUND "+sku+" positive="+str(pos)+" "+json.dumps(sizes,ensure_ascii=False),flush=True)
  time.sleep(1.2)
 print("MENS_SHIRTS_ALL="+json.dumps(res,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
