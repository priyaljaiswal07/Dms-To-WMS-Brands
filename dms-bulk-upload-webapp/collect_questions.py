"""
Function to collect all questions upfront before processing
"""
import pandas as pd
import numpy as np
import copy
from fuzzywuzzy import process, fuzz
from hul_processor import normalize_name, fuzzy_match_name, exact_match_name, safe_read_excel

def collect_all_questions(input_file, reference_file, column_mapping=None, selected_state=None,
                         warehouse_name="", low_price_reason="low price", buyer_branch_id="",
                         brand="HUL"):
    """
    Collect all questions (partial matches, variants, related products) upfront.
    Returns a dictionary with all questions grouped by type.
    """
    PARTIAL_MATCH_MIN_SCORE = 70
    
    questions = {
        'partial_matches': [],
        'variants': [],
        'related': []
    }
    
    # Load files based on brand
    if brand == "Unicharm":
        from datetime import timedelta
        df = safe_read_excel(input_file, header=[6,7,8])
        
        def combine_multiindex_column(col):
            if isinstance(col, tuple):
                values = [str(x).strip() for x in col if str(x).strip().lower() not in ['nan', 'none', '']]
                seen = set()
                unique_values = []
                for v in values:
                    if v not in seen:
                        seen.add(v)
                        unique_values.append(v)
                return " ".join(unique_values).strip()
            return str(col).strip()
        
        df.columns = [combine_multiindex_column(col) for col in df.columns.values]
        
        if column_mapping is None:
            # Use exact mappings from user specification
            expected = {
                "order_id": "Invoice Number",
                "dms_invoice": "Invoice Number",
                "order_date": "Invoice Date",
                "product_name": "Product Name",
                "merchant_name": "Retailer Name",
                "quantity": "Total Quantity",
                "selling_price": "Product Level NetAmount"
            }
            mapping = {}
            for key, expected_col in expected.items():
                if expected_col in df.columns:
                    mapping[key] = expected_col
                else:
                    # Try fuzzy match
                    found = None
                    for col in df.columns:
                        if expected_col.lower() in str(col).lower() or str(col).lower() in expected_col.lower():
                            found = col
                            break
                    mapping[key] = found if found else df.columns[0] if len(df.columns) > 0 else None
        else:
            mapping = column_mapping
        
        def parse_date(date_series):
            parsed = pd.to_datetime(date_series, dayfirst=True, errors="coerce")
            if parsed.isna().any():
                mask = parsed.isna()
                parsed_alt = pd.to_datetime(date_series[mask], errors="coerce")
                parsed = parsed.fillna(parsed_alt)
            return parsed
        
        order_date_parsed = parse_date(df[mapping["order_date"]])
        sale_order_df = pd.DataFrame({
            "order_id": df[mapping["order_id"]],
            "dms_invoice": df[mapping["dms_invoice"]],
            "order_date": order_date_parsed.dt.strftime("%d/%m/%Y"),
            "product_name": df[mapping["product_name"]].astype(str).str.strip(),
            "merchant_name": df[mapping["merchant_name"]].astype(str).str.strip(),
            "quantity": pd.to_numeric(df[mapping["quantity"]], errors="coerce"),
            "net_sales": pd.to_numeric(df[mapping["selling_price"]], errors="coerce"),
        })
        sale_order_df["due_date"] = (order_date_parsed + timedelta(days=10)).dt.strftime("%d/%m/%Y")
    else:
        # HUL, Britannia, Marico
        df = safe_read_excel(input_file)
        
        if column_mapping is None:
            # Use exact mappings from user specification based on brand
            if brand == "Britannia":
                expected = {
                    "order_id": "Invoice No",
                    "dms_invoice": "Invoice No",
                    "order_date": "Invoice Date",
                    "product_name": "Material No Desc",
                    "merchant_name": "Sold To Party Name",
                    "quantity": "Quantity",
                    "selling_price": "Net Amount"
                }
            elif brand == "Marico":
                expected = {
                    "order_id": "Invoice Number",
                    "dms_invoice": "Invoice Number",
                    "order_date": "Invoice Date",
                    "product_name": "Item Description",
                    "merchant_name": "Retailer Name",
                    "quantity": "Item Qty",
                    "selling_price": "Value Incl of Tax"
                }
            else:  # HUL
                expected = {
                    "order_id": "Bill Number",
                    "dms_invoice": "Bill Number",
                    "order_date": "Bill Date",
                    "product_name": "Product Description",
                    "merchant_name": "Party",
                    "quantity": "Units",
                    "selling_price": "Net Sales"
                }
            mapping = {}
            for key, expected_col in expected.items():
                if expected_col in df.columns:
                    mapping[key] = expected_col
                else:
                    # Try fuzzy match
                    found = None
                    for col in df.columns:
                        if expected_col.lower() in str(col).lower() or str(col).lower() in expected_col.lower():
                            found = col
                            break
                    mapping[key] = found if found else df.columns[0] if len(df.columns) > 0 else None
        else:
            mapping = column_mapping
        
        if brand in ["Britannia", "Marico"]:
            def parse_date(date_series):
                parsed = pd.to_datetime(date_series, dayfirst=True, errors="coerce")
                if parsed.isna().any():
                    mask = parsed.isna()
                    parsed_alt = pd.to_datetime(date_series[mask], errors="coerce")
                    parsed = parsed.fillna(parsed_alt)
                return parsed
            order_date_parsed = parse_date(df[mapping["order_date"]])
            sale_order_df = pd.DataFrame({
                "order_id": df[mapping["order_id"]],
                "dms_invoice": df[mapping["dms_invoice"]],
                "order_date": order_date_parsed.dt.strftime("%d/%m/%Y"),
                "product_name": df[mapping["product_name"]].astype(str).str.strip(),
                "merchant_name": df[mapping["merchant_name"]].astype(str).str.strip(),
                "quantity": pd.to_numeric(df[mapping["quantity"]], errors="coerce"),
                "net_sales": pd.to_numeric(df[mapping["selling_price"]], errors="coerce"),
            })
        else:
            sale_order_df = pd.DataFrame({
                "order_id": df[mapping["order_id"]],
                "dms_invoice": df[mapping["dms_invoice"]],
                "order_date": pd.to_datetime(df[mapping["order_date"]], errors="coerce").dt.strftime("%d/%m/%Y"),
                "product_name": df[mapping["product_name"]].astype(str).str.strip(),
                "merchant_name": df[mapping["merchant_name"]].astype(str).str.strip(),
                "quantity": pd.to_numeric(df[mapping["quantity"]], errors="coerce"),
                "net_sales": pd.to_numeric(df[mapping["selling_price"]], errors="coerce"),
            })
    
    sale_order_df = sale_order_df.dropna(subset=["order_id", "order_date", "product_name", "merchant_name"])
    
    # Load reference
    product_df = safe_read_excel(reference_file, sheet_name="Product Details", dtype={"batch_id": str})
    merchant_df = safe_read_excel(reference_file, sheet_name="merchant_data")
    
    if "batch_id" in product_df.columns:
        product_df["batch_id"] = product_df["batch_id"].apply(lambda x: str(x).split(".")[0] if pd.notna(x) else "")
    
    if selected_state:
        merchant_df = merchant_df[merchant_df["shop_state"] == selected_state].copy()
    
    # Collect partial match questions
    product_names = product_df["product_name"].dropna().astype(str).str.strip().tolist()
    seen_partial = set()
    
    for prod in sale_order_df["product_name"]:
        match, score = fuzzy_match_name(prod, product_names, min_score=0)
        if match and 70 <= score < 100:
            cache_key = f"{prod}|{match}"
            if cache_key not in seen_partial:
                seen_partial.add(cache_key)
                questions['partial_matches'].append({
                    'cache_key': cache_key,
                    'input_product': prod,
                    'matched_product': match,
                    'score': score
                })
    
    # Build batch inventory and product variants
    # IMPORTANT: Create a deep copy so we can simulate stock consumption during collection
    # This ensures we collect questions based on what stock will actually be available
    # when each order is processed (accounting for earlier orders consuming stock)
    batch_inventory = {}
    product_id_groups = {}
    
    for _, r in product_df.iterrows():
        pname = str(r["product_name"]).strip()
        pid = str(r.get("product_id", ""))
        
        batch_inventory.setdefault(pname, []).append({
            "batch_id": str(r.get("batch_id", "")),
            "available_stock": float(r.get("available_stock", np.inf)) if pd.notna(r.get("available_stock", np.nan)) else np.inf,
            "product_id": pid,
        })
        
        if pid:
            product_id_groups.setdefault(pid, []).append(pname)
    
    product_variants = {}
    for pid, names in product_id_groups.items():
        if len(names) > 1:
            unique_names = list(set(names))
            if len(unique_names) > 1:
                unique_names.sort()
                main_product = unique_names[0]
                variants = unique_names[1:]
                product_variants[main_product] = variants
    
    for pname in batch_inventory:
        batch_inventory[pname] = sorted(batch_inventory[pname], key=lambda x: -x["available_stock"])
    
    # Create a working copy for simulation during collection
    working_batch_inventory = copy.deepcopy(batch_inventory)
    
    # First, match all products
    matched_products = []
    for prod in sale_order_df["product_name"]:
        match, score = fuzzy_match_name(prod, product_names, min_score=0)
        matched_products.append(match if match else "")
    sale_order_df["matched_product_name"] = matched_products
    
    # Collect variant and related product questions
    # Process orders in date order and simulate stock consumption to match actual processing
    sale_order_df = sale_order_df.sort_values(by="order_date").reset_index(drop=True)
    seen_variants = set()
    seen_related = set()
    
    for idx, row in sale_order_df.iterrows():
        pname = row.get("matched_product_name", "")
        
        if not pname or pname not in working_batch_inventory:
            continue
        
        qty = row["quantity"] if not pd.isna(row["quantity"]) else 0
        if qty <= 0:
            # For negative quantities (returns), add stock back
            if qty < 0 and pname in working_batch_inventory:
                if working_batch_inventory[pname]:
                    working_batch_inventory[pname][0]["available_stock"] += abs(qty)
            continue
        
        # Calculate current stock from working inventory (accounts for previous orders)
        current_stock = sum(b["available_stock"] for b in working_batch_inventory[pname])
        
        # Check variants
        if current_stock < qty:
            variants_to_check = []
            if pname in product_variants:
                variants_to_check = product_variants[pname]
            else:
                for main_prod, variants in product_variants.items():
                    if pname in variants:
                        variants_to_check = [main_prod] + [v for v in variants if v != pname]
                        break
            
            for variant in variants_to_check:
                if variant in working_batch_inventory:
                    variant_stock = sum(b["available_stock"] for b in working_batch_inventory[variant])
                    if variant_stock > 0:
                        cache_key = f"{pname}|{variant}"
                        if cache_key not in seen_variants:
                            seen_variants.add(cache_key)
                            questions['variants'].append({
                                'cache_key': cache_key,
                                'main_product': pname,
                                'variant': variant,
                                'main_stock': current_stock,
                                'variant_stock': variant_stock,
                                'required_qty': qty
                            })
            
            # Check related products - need to account for variants that might be used
            # For collection, we'll assume variants might be used (we'll ask about them)
            # So calculate total_stock including all potential variant stock
            total_stock = current_stock
            for variant in variants_to_check:
                if variant in working_batch_inventory:
                    variant_stock = sum(b["available_stock"] for b in working_batch_inventory[variant])
                    total_stock += variant_stock  # Include all variant stock for collection phase
            
            if total_stock < qty:
                pname_lower = pname.lower().strip()
                for prod_key in working_batch_inventory.keys():
                    if prod_key == pname or prod_key in variants_to_check:
                        continue
                    prod_lower = prod_key.lower().strip()
                    similarity = fuzz.ratio(pname_lower, prod_lower)
                    
                    is_potentially_related = False
                    if len(pname_lower) >= 10 and len(prod_lower) >= 10:
                        if (pname_lower in prod_lower) or (prod_lower in pname_lower):
                            is_potentially_related = True
                    if not is_potentially_related and similarity >= 80:
                        is_potentially_related = True
                    
                    if is_potentially_related:
                        rp_stock = sum(b["available_stock"] for b in working_batch_inventory[prod_key])
                        if rp_stock > 0:
                            cache_key = f"{pname}|{prod_key}"
                            if cache_key not in seen_related:
                                seen_related.add(cache_key)
                                questions['related'].append({
                                    'cache_key': cache_key,
                                    'main_product': pname,
                                    'related_product': prod_key,
                                    'main_stock': current_stock,
                                    'related_stock': rp_stock,
                                    'required_qty': qty,
                                    'total_stock': total_stock
                                })
        
        # Simulate stock consumption for this order (like actual processing does)
        # This ensures later orders see reduced stock, matching actual processing behavior
        if pname in working_batch_inventory and qty > 0:
            remaining_qty = qty
            # Allocate from batches (simplified - just consume stock, don't track batch IDs)
            for batch in working_batch_inventory[pname]:
                if remaining_qty <= 0:
                    break
                if batch["available_stock"] > 0:
                    qty_from_batch = min(batch["available_stock"], remaining_qty)
                    batch["available_stock"] -= qty_from_batch
                    remaining_qty -= qty_from_batch
    
    return questions

