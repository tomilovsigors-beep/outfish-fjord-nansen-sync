import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss8388","https://b2b.fjordnansen.com/product-eng-42182-NIS-SNEAKER-KEVLAR-SOCKS.html"],["ss10314","https://b2b.fjordnansen.com/product-eng-46141-NIS-SNEAKER-KEVLAR-Socks.html"],["ss1871","https://b2b.fjordnansen.com/product-eng-22840-BODO-32-backpack.html"],["ss1870","https://b2b.fjordnansen.com/product-eng-22839-BODO-32-backpack.html"],["ss5826","https://b2b.fjordnansen.com/product-eng-35617-TOLLA-ALU-menagerie-900-ml.html"],["ss11296","https://b2b.fjordnansen.com/product-eng-48439-DRY-BAG-30L-waterproof-bag.html"],["ss11520","https://b2b.fjordnansen.com/product-eng-49044-NIVA-poles-2-0.html"],["ss12502","https://b2b.fjordnansen.com/product-eng-51013-MJUKA-THERMAL-LINER-sleeping-bag-insert.html"],["ss10972","https://b2b.fjordnansen.com/product-eng-47523-NORDKAPP-400-XL-RIGHT-3-C-sleeping-bag.html"]]
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
  print("FULLSRC7 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
