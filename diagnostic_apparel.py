import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss9751","https://b2b.fjordnansen.com/product-eng-45138-VIK-STRETCH-SCARF-chimney.html"],["ss9750","https://b2b.fjordnansen.com/product-eng-45137-VIK-STRETCH-SCARF-chimney.html"],["mw2216","https://b2b.fjordnansen.com/product-eng-42993-VIK-STRETCH-SCARF-chimney.html"],["ss8067","https://b2b.fjordnansen.com/product-eng-41402-HEADGEAR-PABLO-8in1-multifunctional-sling.html"],["ss8065","https://b2b.fjordnansen.com/product-eng-41398-HEADGEAR-MOUNTAIN-WAVE-OLIVE-multifunctional-sling-8in1.html"],["ss8062","https://b2b.fjordnansen.com/product-eng-41387-HEADGEAR-AQUA-8in1-multifunctional-sling.html"],["ss8061","https://b2b.fjordnansen.com/product-eng-41386-HEADGEAR-SPLASH-multifunctional-sling-8in1.html"],["ss8060","https://b2b.fjordnansen.com/product-eng-41385-HEADGEAR-KALEIDOSCOPE-multifunctional-sling-8in1.html"],["ss8059","https://b2b.fjordnansen.com/product-eng-41384-HEADGEAR-COLOR-TUNES-multifunctional-sling-8in1.html"],["ss7476","https://b2b.fjordnansen.com/product-eng-39436-HEADGEAR-FLEECE-BLACK-multifunctional-sling-8in1.html"],["ss5868","https://b2b.fjordnansen.com/product-eng-35700-HEADGEAR-WAVE-8in1-multifunctional-sling.html"],["ss3944","https://b2b.fjordnansen.com/product-eng-28931-HEADGEAR-SHAPES-multifunctional-sling-8in1.html"],["ss3943","https://b2b.fjordnansen.com/product-eng-28930-HEADGEAR-LOGO-PRINT-NAVY-8in1-multifunctional-sling.html"],["ss1675","https://b2b.fjordnansen.com/product-eng-22355-HEADGEAR-VIKING-multifunctional-sling-8in1.html"],["kj0212","https://b2b.fjordnansen.com/product-eng-7527-FIKKE-chimney-sweater.html"],["kj0124","https://b2b.fjordnansen.com/product-eng-6877-HEADGEAR-BLACK-8in1-Multifunctional-Sling.html"],["32051","https://b2b.fjordnansen.com/product-eng-4216-KAPRUN-windproof-headband.html"],["30842","https://b2b.fjordnansen.com/product-eng-2835-COURAGE-chimney-sweater.html"]]
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  row=parse_product(r.text,r.url)
  print("SCARF "+sku+" "+json.dumps({"stock":row.get("supplier_stock"),"attrs":row.get("attributes_json")},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
