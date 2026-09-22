import json, re, time
from bs4 import BeautifulSoup
from config import settings
from supplier_client import FjordNansenClient

TARGETS=[["ss12497","https://b2b.fjordnansen.com/product-eng-51008-SKOG-WOMEN-t-shirt.html"],["ss9243","https://b2b.fjordnansen.com/product-eng-44378-SKOG-WOMEN-emerald-t-shirt.html"],["ss9242","https://b2b.fjordnansen.com/product-eng-44376-NORTH-CAPE-WOMEN-denim-t-shirt.html"],["ss9138","https://b2b.fjordnansen.com/product-eng-44149-RIX-PRINT-UNISEX-HOODED-T-Shirt.html"],["ss9136","https://b2b.fjordnansen.com/product-eng-44145-RIX-UNISEX-Hooded.html"],["ss8708","https://b2b.fjordnansen.com/product-eng-43000-VIK-HOODED-UNISEX-sweatshirt.html"],["ss8707","https://b2b.fjordnansen.com/product-eng-42998-VIK-HOODED-UNISEX-sweatshirt.html"],["ss8706","https://b2b.fjordnansen.com/product-eng-42997-VIK-FULL-ZIP-WOMEN-Sweatshirt.html"],["ss8704","https://b2b.fjordnansen.com/product-eng-42995-VIK-FULL-ZIP-WOMEN-Sweatshirt.html"],["ss8699","https://b2b.fjordnansen.com/product-eng-42988-VIK-1-4-ZIP-WOMEN-Sweatshirt.html"],["ss8698","https://b2b.fjordnansen.com/product-eng-42987-VIK-1-4-ZIP-WOMEN-Sweatshirt.html"],["ss8697","https://b2b.fjordnansen.com/product-eng-42983-VIK-1-4-ZIP-WOMEN-Sweatshirt.html"],["ss8047","https://b2b.fjordnansen.com/product-eng-41354-RIX-UNISEX-SLEEVELESS-T-Shirt.html"],["ss8045","https://b2b.fjordnansen.com/product-eng-41352-RIX-SPORTS-SLEEVELESS-WOMEN-T-Shirt.html"],["ss8044","https://b2b.fjordnansen.com/product-eng-41351-RIX-SPORTS-SLEEVELESS-WOMEN-T-Shirt.html"],["ss8043","https://b2b.fjordnansen.com/product-eng-41350-RIX-SPORTS-SLEEVELESS-WOMEN-T-Shirt.html"],["ss8039","https://b2b.fjordnansen.com/product-eng-41332-RIX-UNISEX-HOODED-T-Shirt.html"],["ss8038","https://b2b.fjordnansen.com/product-eng-41330-RIX-UNISEX-HOODED-T-Shirt.html"],["ss8010","https://b2b.fjordnansen.com/product-eng-41216-RIX-PRINT-T-SHIRT-WOMEN-T-Shirt.html"],["ss8009","https://b2b.fjordnansen.com/product-eng-41212-RIX-PRINT-T-SHIRT-WOMEN-T-Shirt.html"],["ss7910","https://b2b.fjordnansen.com/product-eng-40860-RIX-T-SHIRT-WOMEN-T-Shirt.html"],["ss7909","https://b2b.fjordnansen.com/product-eng-40857-RIX-T-SHIRT-WOMEN-T-Shirt.html"],["ss7908","https://b2b.fjordnansen.com/product-eng-40855-RIX-T-SHIRT-WOMEN-T-Shirt.html"],["ss7907","https://b2b.fjordnansen.com/product-eng-40851-RIX-T-SHIRT-WOMEN-T-Shirt.html"],["ss7906","https://b2b.fjordnansen.com/product-eng-40849-RIX-LONGSLEEVE-WOMEN-T-Shirt.html"],["ss7905","https://b2b.fjordnansen.com/product-eng-40847-RIX-LONGSLEEVE-WOMEN-T-Shirt.html"],["ss7904","https://b2b.fjordnansen.com/product-eng-40846-RIX-LONGSLEEVE-WOMEN-T-Shirt.html"],["ss7903","https://b2b.fjordnansen.com/product-eng-40845-RIX-LONGSLEEVE-WOMEN-T-Shirt.html"],["ss7887","https://b2b.fjordnansen.com/product-eng-40744-CHILO-LONGSLEEVE-WOMEN-T-Shirt.html"],["ss4421","https://b2b.fjordnansen.com/product-eng-31155-HASVIK-WIND-WOMEN-Sweatshirt.html"],["ss4295","https://b2b.fjordnansen.com/product-eng-30353-HASVIK-WIND-WOMEN-Sweatshirt.html"]]

def clean(v):
    return re.sub(r"\s+"," ",str(v or "")).strip()

def parse_sizes(html):
    soup=BeautifulSoup(html,"html.parser")
    rows=[]
    for block in soup.select(".projector_versions__size"):
        text=clean(" ".join(block.stripped_strings))
        if not text: continue
        qty=block.select_one(".projector_versions__quantity[data-amount]")
        name=qty.get("name") if qty else ""
        m=re.search(r"set_quantity\[(\d+)\]",name or "")
        vid=m.group(1) if m else ""
        raw=clean(qty.get("data-amount")) if qty else ""
        q=int(raw) if raw.isdigit() else None
        unavailable=block.select_one(".projector_versions__tell_availability") is not None
        label=text.split(" ")[0]
        if re.match(r"^(XS|S|M|L|XL|XXL|2XL|3XL|4XL|XXXL)$",label,re.I):
            rows.append({"size":label.upper().replace("XXL","2XL").replace("XXXL","3XL"),"variant_id":vid,"quantity":0 if unavailable and q is None else q,"unavailable":unavailable})
    return rows

def main():
    cfg=settings()
    client=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
    auth_ok=False
    for attempt in range(4):
        response,auth=client._authenticate()
        if response is not None and auth.get("authenticated"):
            auth_ok=True; break
        print("AUTH_RETRY "+str(attempt+1)+" "+str(auth.get("reason")),flush=True)
        time.sleep(4*(attempt+1))
    if not auth_ok:
        raise RuntimeError("B2B authentication failed")

    results=[]
    for sku,url in TARGETS:
        r=None
        for attempt in range(4):
            r=client.session.get(url,timeout=30,allow_redirects=True)
            if r.status_code==200: break
            print(f"FETCH_RETRY {sku} {r.status_code} {attempt+1}",flush=True)
            time.sleep(3*(attempt+1))
        if r is None or r.status_code!=200:
            results.append({"sku":sku,"url":url,"error":None if r is None else r.status_code})
            continue
        sizes=parse_sizes(r.text)
        results.append({"sku":sku,"url":r.url,"sizes":sizes})
        print("FOUND "+sku+" "+json.dumps(sizes,ensure_ascii=False),flush=True)
        time.sleep(1.2)
    print("APPAREL_ALL="+json.dumps(results,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
