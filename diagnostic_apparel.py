import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss9584","https://b2b.fjordnansen.com/product-eng-44886-AGIR-WATERPROOF-Gloves-2-0.html"],["ss3715","https://b2b.fjordnansen.com/product-eng-28553-WIND-SMART-Gloves.html"],["ss3437","https://b2b.fjordnansen.com/product-eng-27646-GRIP-SMART-Gloves.html"],["kj0529","https://b2b.fjordnansen.com/product-eng-4234-MICROPILE-Gloves.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  out=[]
  # use both size/sub wrappers because gloves vary
  blocks=s.select(".projector_versions__size, .projector_versions__sub")
  seen=set()
  for b in blocks:
   text=clean(" ".join(b.stripped_strings))
   if not text or text in seen: continue
   seen.add(text)
   q=b.select_one(".projector_versions__quantity[data-amount]")
   raw=clean(q.get("data-amount")) if q else ""
   qty=int(raw) if raw.isdigit() else None
   un=(b.select_one(".projector_versions__tell_availability") is not None) or ("Unavailable" in text)
   out.append({"text":text[:220],"quantity":0 if un and qty is None else qty,"unavailable":un})
  print("GLOVE_FULL "+sku+" "+json.dumps(out,ensure_ascii=False),flush=True); time.sleep(1)
if __name__=="__main__": main()
