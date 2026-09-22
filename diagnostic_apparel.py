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
 allout=[]
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  rows=[]
  for i,q in enumerate(s.select("[data-amount]")):
   raw=clean(q.get("data-amount"))
   if not raw or not raw.lstrip("-").isdigit(): continue
   parent=q
   chain=[]
   for d in range(6):
    if parent is None: break
    chain.append({"d":d,"tag":parent.name,"class":parent.get("class"),"text":clean(" ".join(parent.stripped_strings))[:260]})
    parent=parent.parent
   rows.append({"i":i,"tag":q.name,"name":q.get("name"),"value":q.get("value"),"amount":int(raw),"class":q.get("class"),"chain":chain})
  allout.append({"sku":sku,"rows":rows})
  print("GLOVE_NODES "+sku+" "+json.dumps(rows,ensure_ascii=False),flush=True); time.sleep(1.2)
 print("GLOVE_NODES_ALL="+json.dumps(allout,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
