import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss11473","https://b2b.fjordnansen.com/product-eng-48945-Tent-TROMVIK-II-2-0-2-15-kg.html"],["ss11474","https://b2b.fjordnansen.com/product-eng-48947-TORDIS-I-UL-tent-1-75-kg.html"],["ss10346","https://b2b.fjordnansen.com/product-eng-46162-NOKKEL-key-ring.html"],["ss11367","https://b2b.fjordnansen.com/product-eng-48736-BRANN-SPORK-Spoon-Fork.html"],["ss11498","https://b2b.fjordnansen.com/product-eng-48988-KALDI-BOTTLE.html"],["ss11499","https://b2b.fjordnansen.com/product-eng-48989-KALDI-BOTTLE.html"],["kj0529","https://b2b.fjordnansen.com/product-eng-4234-MICROPILE-Gloves.html"],["ss3437","https://b2b.fjordnansen.com/product-eng-27646-GRIP-SMART-Gloves.html"],["ss3944","https://b2b.fjordnansen.com/product-eng-28931-HEADGEAR-SHAPES-multifunctional-sling-8in1.html"],["ss8062","https://b2b.fjordnansen.com/product-eng-41387-HEADGEAR-AQUA-8in1-multifunctional-sling.html"]]
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
  print("FULLSRC4 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
