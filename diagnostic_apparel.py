import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss9490","https://b2b.fjordnansen.com/product-eng-44738--KJOLEN-XL-RIGHT-2-C-1400g-sleeping-bag.html"],["44700","https://b2b.fjordnansen.com/product-eng-2784-MAP-CASE-REGULAR-Mapbook.html"],["ss1956","https://b2b.fjordnansen.com/product-eng-22936-BACKCOUNTRY-poles.html"],["ss9217","https://b2b.fjordnansen.com/product-eng-44313-LETT-CAP.html"],["ss9196","https://b2b.fjordnansen.com/product-eng-44241-LETT-CAP.html"],["ss12504","https://b2b.fjordnansen.com/product-eng-51016-Underquilt-synthetic-NEVIS-LIGHT.html"],["ss12505","https://b2b.fjordnansen.com/product-eng-51022-Domyslna-nazwa.html"],["ss12635","https://b2b.fjordnansen.com/product-eng-51269-DRY-BAG-10L-waterproof-bag.html"],["ss5868","https://b2b.fjordnansen.com/product-eng-35700-HEADGEAR-WAVE-8in1-multifunctional-sling.html"]]
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
  print("FULLSRC8 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
