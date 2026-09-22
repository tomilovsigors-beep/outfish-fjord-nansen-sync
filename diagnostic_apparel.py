import json
import re
from bs4 import BeautifulSoup

from config import settings
from supplier_client import FjordNansenClient

PRODUCTS = [
("ss12497","https://b2b.fjordnansen.com/product-eng-?"), 
]

TARGETS = [
("ss12497","SKOG WOMEN Olive Sand"),
("ss9243","SKOG WOMEN Emerald"),
("ss9242","NORTH CAPE WOMEN Denim"),
("ss9138","RIX PRINT UNISEX HOODED Mountain&Wave Olive"),
("ss9136","RIX PRINT UNISEX HOODED"),
("ss8708","RIX PRINT UNISEX HOODED"),
("ss8707","RIX PRINT UNISEX HOODED"),
("ss8706","RIX PRINT UNISEX HOODED"),
("ss8704","RIX PRINT UNISEX HOODED"),
("ss8699","RIX PRINT UNISEX"),
("ss8698","RIX PRINT UNISEX"),
("ss8697","RIX PRINT UNISEX"),
("ss8047","HASVIK WOMEN"),
("ss8045","HASVIK WOMEN"),
("ss8044","HASVIK WOMEN"),
("ss8043","HASVIK WOMEN"),
("ss8039","HASVIK WOMEN"),
("ss8038","HASVIK WOMEN"),
("ss8010","VIK"),
("ss8009","VIK"),
("ss7910","RIX T-SHIRT WOMEN"),
("ss7909","RIX T-SHIRT WOMEN Rocky Grey"),
("ss7908","RIX T-SHIRT WOMEN"),
("ss7907","RIX T-SHIRT WOMEN"),
("ss7906","RIX T-SHIRT WOMEN"),
("ss7905","RIX T-SHIRT WOMEN"),
("ss7904","RIX T-SHIRT WOMEN"),
("ss7903","RIX T-SHIRT WOMEN"),
("ss7887","RIX PRINT T-SHIRT WOMEN"),
("ss4421","RIX PRINT T-SHIRT WOMEN"),
("ss4295","RIX PRINT T-SHIRT WOMEN"),
]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def sizes_from_page(soup):
    out=[]
    for block in soup.select(".projector_versions__size"):
        text=clean(" ".join(block.stripped_strings))
        if not text:
            continue
        # first token before price is usually size/color label
        label=text.split(" ")[0]
        qty=block.select_one(".projector_versions__quantity[data-amount]")
        name=qty.get("name") if qty else ""
        m=re.search(r"set_quantity\[(\d+)\]", name or "")
        variant_id=m.group(1) if m else ""
        amount_raw=clean(qty.get("data-amount")) if qty else ""
        amount=int(amount_raw) if amount_raw.isdigit() else None
        unavailable=block.select_one(".projector_versions__tell_availability") is not None
        out.append({"label":label,"variant_id":variant_id,"quantity":0 if unavailable and amount is None else amount,"unavailable":unavailable,"text":text[:220]})
    return out


def main():
    cfg=settings()
    client=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
    response,auth=client._authenticate()
    if response is None or not auth.get("authenticated"):
        raise RuntimeError("Authentication failed")

    # discover catalogue once, then map supplier SKU to URL by parsing each page
    from importer import discover_product_urls, parse_product
    urls=discover_product_urls(client)
    results=[]
    target_skus=set(x[0] for x in TARGETS)
    for i,(pid,url) in enumerate(urls.items(),1):
        try:
            r=client.session.get(url,timeout=30,allow_redirects=True)
            if r.status_code!=200:
                continue
            row=parse_product(r.text,r.url)
            sku=row.get("supplier_sku")
            if sku not in target_skus:
                continue
            soup=BeautifulSoup(r.text,"html.parser")
            results.append({
                "sku":sku,
                "product_id":row.get("source_product_id"),
                "url":r.url,
                "title":row.get("title_original"),
                "color":row.get("color_original"),
                "sizes":sizes_from_page(soup),
            })
            print("FOUND "+sku, flush=True)
            if len(results)>=len(target_skus):
                break
        except Exception as e:
            print("ERR "+url+" "+repr(e), flush=True)
            continue

    print("APPAREL_ALL="+json.dumps(results,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
