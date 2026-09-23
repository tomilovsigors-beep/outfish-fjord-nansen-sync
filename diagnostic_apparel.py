import json,re,time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient
TARGETS=[["ss10347","https://b2b.fjordnansen.com/product-eng-46163-TORDIS-II-PTB-Tent-2-0-2-6-kg.html"],["ss10395","https://b2b.fjordnansen.com/product-eng-46287-Tent-ANDY-III-4-1-kg.html"],["ss10319","https://b2b.fjordnansen.com/product-eng-46150-REKVIK-II-NG-2-0-2-4-kg-tent.html"],["ss2029","https://b2b.fjordnansen.com/product-eng-23024-BIVAK-8-C-1190g-sleeping-bag.html"],["kj0516","https://b2b.fjordnansen.com/product-eng-9820-FJORD-NANSEN-ALU-Carabiner.html"],["ss5503","https://b2b.fjordnansen.com/product-eng-34675-JACON-TITANIUM-SPORK-Spoon-Fork.html"],["ss5827","https://b2b.fjordnansen.com/product-eng-35618-TOLLA-ALU-meniscus-500-ml.html"],["ss9146","https://b2b.fjordnansen.com/product-eng-44178-ALU-APNER-Carabiner.html"],["ss10356","https://b2b.fjordnansen.com/product-eng-46184-PILLER-pendant.html"],["ss10509","https://b2b.fjordnansen.com/product-eng-46457-PUMP-SACK-LIGHT-25L-pump-sack.html"]]
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
  short=clean(" ".join((s.select_one(".product_name__block.--description") or []).stripped_strings)) if s.select_one(".product_name__block.--description") else ""
  long=clean(" ".join((s.select_one("section.longdescription") or []).stripped_strings)) if s.select_one("section.longdescription") else ""
  specs=[]
  for p in s.select("section.dictionary .dictionary__param"):
   name=clean(" ".join((p.select_one(".dictionary__name") or []).stripped_strings)) if p.select_one(".dictionary__name") else ""
   vals=clean(" ".join((p.select_one(".dictionary__values") or []).stripped_strings)) if p.select_one(".dictionary__values") else ""
   if name and vals and "Entity responsible" not in name:
    specs.append([name,vals])
  print("FULLSRC "+sku+" "+json.dumps({"short":short,"long":long,"specs":specs},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
