import re
from config import settings
from supplier_client import FjordNansenClient
URL="https://b2b.fjordnansen.com/product-eng-4234-MICROPILE-Gloves.html"
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 r=c.session.get(URL,timeout=30); r.raise_for_status()
 html=r.text
 for pat in ["kj0529","kj0530","kj0531","kj0532","kj0533","42341","42342","42343","42344","42345"]:
  for m in re.finditer(pat,re.I):
   a=max(0,m.start()-220); b=min(len(html),m.end()+420)
   print("HIT "+pat+" "+re.sub(r"\s+"," ",html[a:b])[:700],flush=True)
if __name__=="__main__": main()
