import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
URL="https://b2b.fjordnansen.com/product-eng-44344-TREKKER-CAMPING-2-0-mattress-II-CATEGORY.html"
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 r=c.session.get(URL,timeout=30); r.raise_for_status()
 row=parse_product(r.text,r.url)
 print("TREKKER2="+json.dumps({"stock":row.get("supplier_stock"),"attrs":row.get("attributes_json")},ensure_ascii=False),flush=True)
if __name__=="__main__": main()
