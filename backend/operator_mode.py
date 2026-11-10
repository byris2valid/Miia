


def low_stock(catalog: dict[str, dict], threshold: int = 3) -> list[dict]:
    low_stock_items = []
    for slot, info in catalog.items():
       if info["stock"] <= threshold:
           low_stock_items.append({"slot": slot, "name": info["name"], "stock": info["stock"]})
    return low_stock_items

if __name__ == "__main__":
    from cli import load_catalog
    print(low_stock(load_catalog()))
    print(low_stock(load_catalog(), threshold=6))