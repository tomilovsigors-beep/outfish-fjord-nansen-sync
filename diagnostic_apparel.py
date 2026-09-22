import re,time
from config import settings
from supplier_client import FjordNansenClient
URL="https://b2b.fjordnansen.com/product-eng-4234-MICROPILE-Gloves.html"
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 ok=False
 for attempt in range(5):
  resp,auth=c._authenticate()
  if resp is not None and auth.get("authenticated"):
   ok=True; break
  print("AUTH_RETRY "+str(attempt+1)+" "+str(auth),flush=True)
  time.sleep(3*(attempt+1))
 if not ok: raise RuntimeError("Authentication failed after retries")
 r=c.session.get(URL,timeout=30); r.raise_for_status()
 html=r.text
 for pat in ["kj0529","kj0530","kj0531","kj0532","kj0533","42341","42342","42343","42344","42345"]:
  found=False
  for m in re.finditer(pat,re.I):
   found=True
   a=max(0,m.start()-300); b=min(len(html),m.end()+500)
   print("HIT "+pat+" "+re.sub(r"\s+"," ",html[a:b])[:900],flush=True)
  if not found: print("NOHIT "+pat,flush=True)
if __name__=="__main__": main()
