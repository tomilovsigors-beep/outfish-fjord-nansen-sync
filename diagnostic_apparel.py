import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss8700","https://b2b.fjordnansen.com/product-eng-42989-VIK-FULL-ZIP-MEN-Sweatshirt.html"],["ss8696","https://b2b.fjordnansen.com/product-eng-42982-VIK-1-4-ZIP-MEN-Sweatshirt.html"],["ss8695","https://b2b.fjordnansen.com/product-eng-42981-VIK-1-4-ZIP-MEN-Sweatshirt.html"],["ss8693","https://b2b.fjordnansen.com/product-eng-42976-VIK-1-4-ZIP-MEN-Sweatshirt.html"],["ss4296","https://b2b.fjordnansen.com/product-eng-30355-HASVIK-WIND-MEN-sweatshirt.html"]]
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
  sizes=parse_sizes(r.text); pos=sum(1 for x in sizes if isinstance(x.get("quantity"),int) and x["quantity"]>0)
  res.append({"sku":sku,"url":r.url,"sizes":sizes})
  print("FOUND "+sku+" positive="+str(pos)+" "+json.dumps(sizes,ensure_ascii=False),flush=True); time.sleep(1.2)
 print("MENS_SWEATS_ALL="+json.dumps(res,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
