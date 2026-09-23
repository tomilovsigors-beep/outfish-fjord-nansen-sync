import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss11432","https://b2b.fjordnansen.com/product-eng-48883-VEIG-II-3-kg-tent.html"],["ss11433","https://b2b.fjordnansen.com/product-eng-48884-VEIG-PRO-III-3-6-kg-tent.html"],["ss11434","https://b2b.fjordnansen.com/product-eng-48885-TORDIS-I-tent-2-0-2-1-kg.html"],["ss11435","https://b2b.fjordnansen.com/product-eng-48886-VINGER-II-tent-3-15-kg.html"],["ss10305","https://b2b.fjordnansen.com/product-eng-46117-Tent-KORSYKA-III-COMPACT-2-0-5-1-kg.html"],["31052","https://b2b.fjordnansen.com/product-eng-1562-Tent-SPLIT-VI-10-8-kg.html"],["ss8243","https://b2b.fjordnansen.com/product-eng-41826-FINMARK-MID-4-C-850g-sleeping-bag.html"],["ss9134","https://b2b.fjordnansen.com/product-eng-44141-KJOLEN-MID-LEFT-sleeping-bag-2-C-1300g.html"],["ss8235","https://b2b.fjordnansen.com/product-eng-41817-TROMS-XL-sleeping-bag-5-C-1514g.html"],["ss9485","https://b2b.fjordnansen.com/product-eng-44730-HADSEL-MID-RIGHT-sleeping-bag-8-C-1700g.html"]]
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
  print("FULLSRC2 "+sku+" "+json.dumps({"url":r.url,"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
