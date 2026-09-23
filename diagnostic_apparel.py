import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss8375","https://b2b.fjordnansen.com/product-eng-42145-NEW-HIKE-KEVLAR-SOCKS.html"],["ss10747/mw","https://b2b.fjordnansen.com/product-eng-46730-HYGGE-BEANIE-Cap.html"],["ss10750/mw","https://b2b.fjordnansen.com/product-eng-46733-HYGGE-BEANIE-Cap.html"],["ss10748/mw","https://b2b.fjordnansen.com/product-eng-46731-HYGGE-BEANIE-Cap.html"],["ss10749/mw","https://b2b.fjordnansen.com/product-eng-46732-HYGGE-BEANIE-Cap.html"],["ss10755/mw","https://b2b.fjordnansen.com/product-eng-46738-LIGHT-MERINOULL-BEANIE-Cap.html"],["ss9085","https://b2b.fjordnansen.com/product-eng-43872-NORDKAPP-300-MID-LEFT-down-sleeping-bag-1-C-650-g.html"],["ss9086","https://b2b.fjordnansen.com/product-eng-43873-NORDKAPP-300-XL-RIGHT-1-C-700-g-sleeping-bag.html"],["ss5613","https://b2b.fjordnansen.com/product-eng-35043-FALL-200-cap.html"],["ss9498","https://b2b.fjordnansen.com/product-eng-44781-SKI-KEVLAR-Socks.html"]]
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
  print("FULLSRC5 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
