import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss9584","https://b2b.fjordnansen.com/product-eng-44886-AGIR-WATERPROOF-Gloves-2-0.html"],["ss3715","https://b2b.fjordnansen.com/product-eng-28553-WIND-SMART-Gloves.html"],["ss3437","https://b2b.fjordnansen.com/product-eng-27646-GRIP-SMART-Gloves.html"],["kj0529","https://b2b.fjordnansen.com/product-eng-4234-MICROPILE-Gloves.html"]]
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 out=[]
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  row=parse_product(r.text,r.url)
  out.append({"sku":sku,"supplier_stock":row.get("supplier_stock"),"availability":row.get("availability"),"attrs":row.get("attributes_json")})
  print("GLOVE "+sku+" "+json.dumps(out[-1],ensure_ascii=False),flush=True); time.sleep(1.2)
 print("GLOVES_EXACT="+json.dumps(out,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
