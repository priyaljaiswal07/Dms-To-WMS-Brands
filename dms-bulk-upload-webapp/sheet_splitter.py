"""
Utility function to split valid orders into multiple sheets (max 200 orders per sheet)
Ensures complete orders are never split across sheets
"""
import pandas as pd

MAX_ORDERS_PER_SHEET = 200

def split_orders_into_sheets(valid_df):
    """
    Split valid orders dataframe into multiple sheets if > 200 orders.
    Each order stays complete in one sheet.
    
    Returns:
        list of tuples: [(sheet_name, dataframe), ...]
        list of dicts: [{'sheet_name': str, 'order_count': int, 'row_count': int}, ...]
    """
    if valid_df.empty:
        return [], []
    
    unique_orders = valid_df['order_id'].unique()
    total_orders = len(unique_orders)
    
    valid_sheets = []
    sheet_info = []
    
    if total_orders > MAX_ORDERS_PER_SHEET:
        # Split into multiple sheets, ensuring complete orders
        order_groups = []
        current_group = []
        current_count = 0
        
        for order_id in unique_orders:
            order_rows = valid_df[valid_df['order_id'] == order_id]
            order_row_count = len(order_rows)
            
            # If adding this order would exceed limit, start new sheet
            if current_count + 1 > MAX_ORDERS_PER_SHEET and current_group:
                order_groups.append(current_group)
                current_group = [order_id]
                current_count = 1
            else:
                current_group.append(order_id)
                current_count += 1
        
        # Add last group
        if current_group:
            order_groups.append(current_group)
        
        # Create dataframes for each sheet
        for idx, order_list in enumerate(order_groups, 1):
            sheet_df = valid_df[valid_df['order_id'].isin(order_list)].copy()
            valid_sheets.append((f"Sale Order Demo {idx}", sheet_df))
            sheet_info.append({
                'sheet_name': f"Sale Order Demo {idx}",
                'order_count': len(order_list),
                'row_count': len(sheet_df)
            })
    else:
        # Single sheet
        valid_sheets.append(("Sale Order Demo", valid_df))
        sheet_info.append({
            'sheet_name': "Sale Order Demo",
            'order_count': total_orders,
            'row_count': len(valid_df)
        })
    
    return valid_sheets, sheet_info

