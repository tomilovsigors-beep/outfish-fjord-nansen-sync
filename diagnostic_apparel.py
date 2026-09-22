import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss9752","https://b2b.fjordnansen.com/product-eng-45140-VIK-LEGGINGS-UNISEX-gaiters.html"],["mw2218","https://b2b.fjordnansen.com/product-eng-42999-VIK-LEGGINGS-UNISEX-gaiters.html"]]
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
  label=text.split(" ")[0]
  out.append({"label":label,"quantity":0 if unavailable and qty is None else qty,"unavailable":unavailable,"text":text[:180]})
 return out
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 res=[]
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  sizes=parse_sizes(r.text); res.append({"sku":sku,"url":r.url,"sizes":sizes})
  print("FOUND "+sku+" "+json.dumps(sizes,ensure_ascii=False),flush=True); time.sleep(1.5)
 print("WOMENS_PANTS_MORE="+json.dumps(res,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
