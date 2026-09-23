import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["MS18","https://b2b.fjordnansen.com/product-eng-44176-STAVANGER-XL-LEFT-sleeping-bag-7-C-2100g.html"],["ss6106","https://b2b.fjordnansen.com/product-eng-35895-PROFI-LINER-sheet.html"],["kj0359","https://b2b.fjordnansen.com/product-eng-4091-FROTA-towel-XL-290g-150-x-63cm.html"],["kj0358","https://b2b.fjordnansen.com/product-eng-9013-TRAMP-L-160g-120x60cm-towel.html"],["ss8923","https://b2b.fjordnansen.com/product-eng-43524-ADVENTURE-BACKPACK-23L.html"],["ss8925","https://b2b.fjordnansen.com/product-eng-43531-HIP-BAG-3L-Waterproof-Hip-Bag.html"],["ss8396","https://b2b.fjordnansen.com/product-eng-42191-NEW-STRIPE-SOCKS.html"],["ss10309","https://b2b.fjordnansen.com/product-eng-46127-TRIP-LONG-socks.html"],["ss1868","https://b2b.fjordnansen.com/product-eng-22837-TOMTE-20-backpack.html"],["ss1873","https://b2b.fjordnansen.com/product-eng-22842-BODO-40-backpack.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  short=clean(" ".join(s.select_one(".product_name__block.--description").stripped_strings)) if s.select_one(".product_name__block.--description") else ""
  long=clean(" ".join(s.select_one("section.longdescription").stripped_strings)) if s.select_one("section.longdescription") else ""
  specs=[]
  for p in s.select("section.dictionary .dictionary__param"):
   name=clean(" ".join(p.select_one(".dictionary__name").stripped_strings)) if p.select_one(".dictionary__name") else ""
   vals=clean(" ".join(p.select_one(".dictionary__values").stripped_strings)) if p.select_one(".dictionary__values") else ""
   if name and vals and "Entity responsible" not in name:
    specs.append([name,vals])
  print("FULLSRC3 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
