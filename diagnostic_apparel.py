import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss10374","https://b2b.fjordnansen.com/product-eng-46234-HENDIG-SILVER-Carabiner.html"],["ss8060","https://b2b.fjordnansen.com/product-eng-41385-HEADGEAR-KALEIDOSCOPE-multifunctional-sling-8in1.html"],["ss8061","https://b2b.fjordnansen.com/product-eng-41386-HEADGEAR-SPLASH-multifunctional-sling-8in1.html"],["ss10320","https://b2b.fjordnansen.com/product-eng-46153-ARLA-Passport-Box.html"],["ss10353","https://b2b.fjordnansen.com/product-eng-46175-STORD-2-sachet.html"],["ss10935","https://b2b.fjordnansen.com/product-eng-47445-LIGHT-MERINOULL-BEANIE-Cap.html"],["ss8371","https://b2b.fjordnansen.com/product-eng-42140-REVLE-ANTI-MOSQUITO-anti-tick-socks.html"],["ss9191g","https://b2b.fjordnansen.com/product-eng-49003-TRUCKER-CAP-BWAH-olive-black-baseball-cap.html"],["ss6060","https://b2b.fjordnansen.com/product-eng-35831-TROMVIK-I-NG-1-5-kg-tent.html"],["ss8368","https://b2b.fjordnansen.com/product-eng-42135-NEW-HIKE-LOW-KEVLAR-SOCKS.html"]]
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
  print("FULLSRC6 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
