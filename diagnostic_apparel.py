import json,re
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
URL="https://b2b.fjordnansen.com/product-eng-49516-Oxiva-Merino-Longsleeve-Men.html"
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 r=c.session.get(URL,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
 rows=[]
 for i,q in enumerate(s.select("[data-amount]")):
  raw=clean(q.get("data-amount"))
  if not raw or not raw.isdigit(): continue
  p=q; text=""
  for _ in range(6):
   if p is None: break
   t=clean(" ".join(p.stripped_strings))
   if len(t)>len(text): text=t
   p=p.parent
  rows.append({"i":i,"name":q.get("name"),"amount":int(raw),"text":text[:450]})
 print("OXIVA_TOP_NODES="+json.dumps(rows,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
