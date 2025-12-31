import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import tempfile

# Import processing functions
from hul_processor_interactive import process_hul_sales_interactive
from unicharm_processor_interactive import process_unicharm_sales_interactive
from britannia_processor_interactive import process_britannia_sales_interactive
from marico_processor_interactive import process_marico_sales_interactive
from collect_questions import collect_all_questions

st.set_page_config(
    page_title="DMS Bulk Upload Processor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DMS Bulk Upload Processor")
st.markdown("Upload your sales file and reference file to process bulk orders")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'output_file' not in st.session_state:
    st.session_state.output_file = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'processing_started' not in st.session_state:
    st.session_state.processing_started = False
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None
if 'processing_cache' not in st.session_state:
    st.session_state.processing_cache = {
        'partial_matches': {},
        'variants': {},
        'related': {}
    }
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = {}
if 'all_questions_collected' not in st.session_state:
    st.session_state.all_questions_collected = False
if 'all_questions' not in st.session_state:
    st.session_state.all_questions = None
if 'processing_progress' not in st.session_state:
    st.session_state.processing_progress = {
        'products_matched': 0,
        'total_products': 0,
        'orders_processed': 0,
        'total_orders': 0
    }
# Column mappings based on brand (from user specification)
BRAND_COLUMN_MAPPINGS = {
    "HUL": {
        "order_id": "Bill Number",
        "dms_invoice": "Bill Number",
        "order_date": "Bill Date",
        "product_name": "Product Description",
        "merchant_name": "Party",
        "quantity": "Units",
        "selling_price": "Net Sales"
    },
    "Britannia": {
        "order_id": "Invoice No",
        "dms_invoice": "Invoice No",
        "order_date": "Invoice Date",
        "product_name": "Material No Desc",
        "merchant_name": "Sold To Party Name",
        "quantity": "Quantity",
        "selling_price": "Net Amount"
    },
    "Marico": {
        "order_id": "Invoice Number",
        "dms_invoice": "Invoice Number",
        "order_date": "Invoice Date",
        "product_name": "Item Description",
        "merchant_name": "Retailer Name",
        "quantity": "Item Qty",
        "selling_price": "Value Incl of Tax"
    },
    "Unicharm": {
        "order_id": "Invoice Number",
        "dms_invoice": "Invoice Number",
        "order_date": "Invoice Date",
        "product_name": "Product Name",
        "merchant_name": "Retailer Name",
        "quantity": "Total Quantity",
        "selling_price": "Product Level NetAmount"
    }
}

# Brand selection
brand = st.selectbox(
    "Select Brand",
    ["HUL", "Unicharm", "Britannia", "Marico"],
    help="Choose the brand for which you want to process the bulk upload",
    key="brand_selection"
)

# File uploads
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Upload Input File")
    input_file = st.file_uploader(
        "Upload your sales/order Excel file",
        type=['xlsx', 'xls'],
        key="input_file"
    )

with col2:
    st.subheader("📁 Upload Reference File")
    reference_file = st.file_uploader(
        "Upload your reference Excel file (with Product Details and merchant_data sheets)",
        type=['xlsx', 'xls'],
        key="reference_file"
    )

# Handle pending question FIRST (before any processing)
# This ensures questions are shown even if processing is running
if st.session_state.pending_question:
    st.markdown("---")
    st.header("❓ Action Required")
    question = st.session_state.pending_question
    
    st.warning("⚠️ **PROCESSING PAUSED** - Please answer the question below to continue:")
    st.markdown("---")
    
    # Always show debug info to help troubleshoot
    with st.expander("🔍 Debug: Question Data (click to expand)", expanded=True):
        st.json(question)
        st.write(f"**Question Type:** {question.get('type', 'NOT SET')}")
        st.write(f"**Has all fields:** {all(k in question for k in ['type', 'cache_key'])}")
    
    # Check if question has required fields
    if not question or 'type' not in question:
        st.error("❌ Question data is incomplete. Please refresh the page and try again.")
        if st.button("🔄 Reset and Start Over"):
            st.session_state.pending_question = None
            st.session_state.processing_started = False
            st.session_state.processing = False
            st.rerun()
    elif question.get('type') == 'partial_match':
        st.markdown(f"**⚠️ PARTIAL MATCH FOUND ({int(question['score'])}% similarity)**")
        st.markdown(f"**Input Product:** `{question['input_product']}`")
        st.markdown(f"**Matched Reference:** `{question['matched_product']}`")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Accept", key="accept_partial", type="primary", use_container_width=True):
                st.session_state.processing_cache['partial_matches'][question['cache_key']] = True
                st.session_state.pending_question = None
                # Continue processing automatically
                st.rerun()
        with col2:
            if st.button("❌ Reject", key="reject_partial", use_container_width=True):
                st.session_state.processing_cache['partial_matches'][question['cache_key']] = False
                st.session_state.pending_question = None
                # Continue processing automatically
                st.rerun()
    
    elif question.get('type') == 'variant':
        st.markdown(f"**⚠️ PRODUCT VARIANT DETECTED (Same Product ID)**")
        st.markdown(f"**Main Product:** `{question['main_product']}` (Available: {int(question['main_stock'])} units)")
        st.markdown(f"**Variant Found:** `{question['variant']}` (Available: {int(question['variant_stock'])} units)")
        st.markdown(f"**Required:** {int(question['required_qty'])} units")
        st.markdown(f"**❓ Can we use inventory from '{question['variant']}' for this order?**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Use Variant", key="use_variant", type="primary", use_container_width=True):
                st.session_state.processing_cache['variants'][question['cache_key']] = True
                st.session_state.pending_question = None
                st.rerun()
        with col2:
            if st.button("❌ Don't Use", key="skip_variant", use_container_width=True):
                st.session_state.processing_cache['variants'][question['cache_key']] = False
                st.session_state.pending_question = None
                st.rerun()
    
    elif question.get('type') == 'related':
        st.markdown(f"**⚠️ INSUFFICIENT STOCK FOR: `{question['main_product']}`**")
        st.markdown(f"**Required:** {int(question['required_qty'])} units")
        st.markdown(f"**Currently available:** {int(question['total_stock'])} units")
        st.markdown(f"**Shortage:** {int(question['required_qty'] - question['total_stock'])} units")
        st.markdown(f"**🔍 Found similar product:** `{question['related_product']}` (Available: {int(question['related_stock'])} units)")
        st.markdown(f"**❓ QUESTION: Are these the SAME product?**")
        st.markdown(f"1. `{question['main_product']}`")
        st.markdown(f"2. `{question['related_product']}`")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Same Product", key="same_product", type="primary", use_container_width=True):
                st.session_state.processing_cache['related'][question['cache_key']] = True
                st.session_state.pending_question = None
                st.rerun()
        with col2:
            if st.button("❌ Different Product", key="different_product", use_container_width=True):
                st.session_state.processing_cache['related'][question['cache_key']] = False
                st.session_state.pending_question = None
                st.rerun()
    else:
        # Unknown question type - show raw data
        st.error(f"❌ Unknown question type: {question.get('type', 'N/A')}")
        st.json(question)
        if st.button("🔄 Clear and Continue"):
            st.session_state.pending_question = None
            st.rerun()
    
    st.markdown("---")

# If files are uploaded, show configuration
if input_file is not None and reference_file is not None:
    # Load files to get column info
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, input_file.name)
            reference_path = os.path.join(temp_dir, reference_file.name)
            
            with open(input_path, "wb") as f:
                f.write(input_file.getbuffer())
            with open(reference_path, "wb") as f:
                f.write(reference_file.getbuffer())
            
            # Read input file
            ext = os.path.splitext(input_file.name)[-1].lower()
            if ext == ".xls":
                df = pd.read_excel(input_path, engine="xlrd")
            else:
                if brand == "Unicharm":
                    df = pd.read_excel(input_path, engine="openpyxl", header=[6,7,8])
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
                else:
                    df = pd.read_excel(input_path, engine="openpyxl")
            
            # Read reference file to get states
            merchant_df = pd.read_excel(reference_path, sheet_name="merchant_data", engine="openpyxl")
            unique_states = merchant_df["shop_state"].dropna().unique().tolist()
            
            st.success("✅ Files loaded successfully!")
            
            # Configuration
            st.subheader("⚙️ Configuration")
            
            # State selection
            if unique_states:
                selected_state = st.selectbox(
                    "Select State",
                    unique_states,
                    key="state_selection",
                    help="Select the state to filter merchants"
                )
            else:
                selected_state = None
                st.warning("No states found in merchant_data")
            
            # Brand-specific inputs
            if brand == "Unicharm":
                warehouse_name = st.text_input("Warehouse Name (optional)", key="warehouse_name")
                low_price_reason = st.text_input("Low Price Reason (optional)", value="low price", key="low_price_reason")
                buyer_branch_id = st.text_input("Buyer Branch ID (optional)", key="buyer_branch_id")
            else:
                warehouse_name = ""
                low_price_reason = "low price"
                buyer_branch_id = ""
            
            # Save temp file paths for processing
            if 'input_path' not in st.session_state.temp_files or 'reference_path' not in st.session_state.temp_files:
                # Save files to persistent temp location
                import tempfile as tf
                temp_base = tf.gettempdir()
                input_path_saved = os.path.join(temp_base, f"dms_input_{id(input_file)}.xlsx")
                reference_path_saved = os.path.join(temp_base, f"dms_ref_{id(reference_file)}.xlsx")
                
                with open(input_path_saved, "wb") as f:
                    f.write(input_file.getbuffer())
                with open(reference_path_saved, "wb") as f:
                    f.write(reference_file.getbuffer())
                
                st.session_state.temp_files = {
                    'input_path': input_path_saved,
                    'reference_path': reference_path_saved
                }
            
            # Auto-detect column mapping using brand-specific mappings
            available_columns = df.columns.tolist()
            brand_mapping = BRAND_COLUMN_MAPPINGS.get(brand, {})
            column_mapping = {}
            
            # Map required fields
            for key, expected_col in brand_mapping.items():
                if expected_col in available_columns:
                    column_mapping[key] = expected_col
                else:
                    # Try fuzzy match as fallback
                    found = False
                    for col in available_columns:
                        if expected_col.lower() in str(col).lower() or str(col).lower() in expected_col.lower():
                            column_mapping[key] = col
                            found = True
                            break
                    if not found:
                        st.error(f"❌ Required column '{expected_col}' not found in file. Available columns: {', '.join(available_columns)}")
                        st.stop()
            
            # Optional fields (check if they exist)
            optional_fields = ["low_price_reason", "buyer_branch_id", "warehouse_name"]
            for opt_field in optional_fields:
                # Try common names
                possible_names = ["Low Price Reason", "Branch ID", "Buyer Branch ID", "Warehouse Name"]
                for name in possible_names:
                    if name in available_columns:
                        column_mapping[opt_field] = name
                        break
            
            # Store mapping in session state
            st.session_state.column_mapping = column_mapping
            
            # New flow: Collect all questions first, then process
            if not st.session_state.all_questions_collected:
                if st.button("📋 Collect All Questions", type="primary"):
                    with st.spinner("🔍 Scanning files and collecting questions..."):
                        try:
                            questions = collect_all_questions(
                                st.session_state.temp_files['input_path'],
                                st.session_state.temp_files['reference_path'],
                                selected_state=selected_state,
                                warehouse_name=warehouse_name if brand == "Unicharm" else "",
                                low_price_reason=low_price_reason if brand == "Unicharm" else "low price",
                                buyer_branch_id=buyer_branch_id if brand == "Unicharm" else "",
                                brand=brand,
                                column_mapping=column_mapping
                            )
                            st.session_state.all_questions = questions
                            st.session_state.all_questions_collected = True
                            st.session_state.processing_cache = {
                                'partial_matches': {},
                                'variants': {},
                                'related': {}
                            }
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error collecting questions: {str(e)}")
                            st.exception(e)
            
            # Show all questions at once
            if st.session_state.all_questions_collected and st.session_state.all_questions:
                questions = st.session_state.all_questions
                
                st.markdown("---")
                st.header("❓ Please Answer All Questions")
                st.info(f"📊 Found {len(questions['partial_matches'])} partial matches, {len(questions['variants'])} variants, and {len(questions['related'])} related products to review.")
                
                # Show ALL questions in one view - no loops
                # Group 1: Partial Matches
                if questions['partial_matches']:
                    st.markdown("### ⚠️ Partial Matches (70-99% similarity) - Product Matching")
                    unanswered_partial = [q for q in questions['partial_matches'] if q['cache_key'] not in st.session_state.processing_cache['partial_matches']]
                    answered_partial = [q for q in questions['partial_matches'] if q['cache_key'] in st.session_state.processing_cache['partial_matches']]
                    
                    if unanswered_partial:
                        for i, q in enumerate(unanswered_partial):
                            cache_key = q['cache_key']
                            st.markdown(f"**{i+1}. Match {int(q['score'])}% similarity**")
                            st.markdown(f"   - Input: `{q['input_product']}`")
                            st.markdown(f"   - Matched: `{q['matched_product']}`")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"✅ Accept", key=f"accept_partial_{cache_key}", type="primary", use_container_width=True):
                                    st.session_state.processing_cache['partial_matches'][cache_key] = True
                                    st.rerun()
                            with col2:
                                if st.button(f"❌ Reject", key=f"reject_partial_{cache_key}", use_container_width=True):
                                    st.session_state.processing_cache['partial_matches'][cache_key] = False
                                    st.rerun()
                            st.markdown("---")
                    else:
                        st.success(f"✅ All {len(answered_partial)} partial matches answered!")
                
                # Group 2: Variants (Batch Allocation)
                if questions['variants']:
                    st.markdown("### 🔄 Product Variants (Same Product ID) - Batch Allocation")
                    unanswered_variants = [q for q in questions['variants'] if q['cache_key'] not in st.session_state.processing_cache['variants']]
                    answered_variants = [q for q in questions['variants'] if q['cache_key'] in st.session_state.processing_cache['variants']]
                    
                    if unanswered_variants:
                        for i, q in enumerate(unanswered_variants):
                            cache_key = q['cache_key']
                            st.markdown(f"**{i+1}. Variant Question**")
                            st.markdown(f"   - Main Product: `{q['main_product']}` (Available: {int(q['main_stock'])} units)")
                            st.markdown(f"   - Variant: `{q['variant']}` (Available: {int(q['variant_stock'])} units)")
                            st.markdown(f"   - Required: {int(q['required_qty'])} units")
                            st.markdown(f"   - **Can we use inventory from '{q['variant']}'?**")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"✅ Use Variant", key=f"use_variant_{cache_key}", type="primary", use_container_width=True):
                                    st.session_state.processing_cache['variants'][cache_key] = True
                                    st.rerun()
                            with col2:
                                if st.button(f"❌ Don't Use", key=f"skip_variant_{cache_key}", use_container_width=True):
                                    st.session_state.processing_cache['variants'][cache_key] = False
                                    st.rerun()
                            st.markdown("---")
                    else:
                        st.success(f"✅ All {len(answered_variants)} variant questions answered!")
                
                # Group 3: Related Products (Batch Allocation)
                if questions['related']:
                    st.markdown("### 🔍 Related Products (Similar names) - Batch Allocation")
                    unanswered_related = [q for q in questions['related'] if q['cache_key'] not in st.session_state.processing_cache['related']]
                    answered_related = [q for q in questions['related'] if q['cache_key'] in st.session_state.processing_cache['related']]
                    
                    if unanswered_related:
                        for i, q in enumerate(unanswered_related):
                            cache_key = q['cache_key']
                            st.markdown(f"**{i+1}. Related Product Question**")
                            st.markdown(f"   - Main Product: `{q['main_product']}` (Available: {int(q['main_stock'])} units)")
                            st.markdown(f"   - Required: {int(q['required_qty'])} units, Currently available: {int(q['total_stock'])} units")
                            st.markdown(f"   - Found similar: `{q['related_product']}` (Available: {int(q['related_stock'])} units)")
                            st.markdown(f"   - **Are these the SAME product?**")
                            st.markdown(f"     1. `{q['main_product']}`")
                            st.markdown(f"     2. `{q['related_product']}`")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"✅ Same Product", key=f"same_product_{cache_key}", type="primary", use_container_width=True):
                                    st.session_state.processing_cache['related'][cache_key] = True
                                    st.rerun()
                            with col2:
                                if st.button(f"❌ Different Product", key=f"different_product_{cache_key}", use_container_width=True):
                                    st.session_state.processing_cache['related'][cache_key] = False
                                    st.rerun()
                            st.markdown("---")
                    else:
                        st.success(f"✅ All {len(answered_related)} related product questions answered!")
                
                # Check if all questions answered
                all_answered = True
                for q in questions['partial_matches']:
                    if q['cache_key'] not in st.session_state.processing_cache['partial_matches']:
                        all_answered = False
                        break
                if all_answered:
                    for q in questions['variants']:
                        if q['cache_key'] not in st.session_state.processing_cache['variants']:
                            all_answered = False
                            break
                if all_answered:
                    for q in questions['related']:
                        if q['cache_key'] not in st.session_state.processing_cache['related']:
                            all_answered = False
                            break
                
                if all_answered:
                    st.success("✅ All questions answered! Click below to process.")
                    if st.button("🚀 Process with Answers", type="primary", use_container_width=True):
                        st.session_state.processing_started = True
                        st.session_state.processing = True
                        st.rerun()
                else:
                    remaining = sum([
                        len([q for q in questions['partial_matches'] if q['cache_key'] not in st.session_state.processing_cache['partial_matches']]),
                        len([q for q in questions['variants'] if q['cache_key'] not in st.session_state.processing_cache['variants']]),
                        len([q for q in questions['related'] if q['cache_key'] not in st.session_state.processing_cache['related']])
                    ])
                    st.warning(f"⚠️ Please answer {remaining} remaining question(s) above.")
            
            # Process after all questions answered
            if st.session_state.processing_started and st.session_state.all_questions_collected:
                try:
                    output_path = os.path.join(tempfile.gettempdir(), f"dms_output_{id(input_file)}.xlsx")
                    
                    with st.spinner("🔄 Processing files with your answers..."):
                        if brand == "HUL":
                            result = process_hul_sales_interactive(
                                st.session_state.temp_files['input_path'],
                                st.session_state.temp_files['reference_path'],
                                output_path,
                                column_mapping=column_mapping,
                                selected_state=selected_state,
                                processing_cache=st.session_state.processing_cache
                            )
                        elif brand == "Unicharm":
                            result = process_unicharm_sales_interactive(
                                st.session_state.temp_files['input_path'],
                                st.session_state.temp_files['reference_path'],
                                output_path,
                                column_mapping=column_mapping,
                                selected_state=selected_state,
                                warehouse_name=warehouse_name,
                                low_price_reason=low_price_reason,
                                buyer_branch_id=buyer_branch_id,
                                processing_cache=st.session_state.processing_cache
                            )
                        elif brand == "Britannia":
                            result = process_britannia_sales_interactive(
                                st.session_state.temp_files['input_path'],
                                st.session_state.temp_files['reference_path'],
                                output_path,
                                column_mapping=column_mapping,
                                selected_state=selected_state,
                                processing_cache=st.session_state.processing_cache
                            )
                        elif brand == "Marico":
                            result = process_marico_sales_interactive(
                                st.session_state.temp_files['input_path'],
                                st.session_state.temp_files['reference_path'],
                                output_path,
                                column_mapping=column_mapping,
                                selected_state=selected_state,
                                processing_cache=st.session_state.processing_cache
                            )
                    
                    if result and os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            st.session_state.output_file = f.read()
                        st.session_state.processing_complete = True
                        st.session_state.processing = False
                        st.session_state.processing_started = False
                        st.session_state.all_questions_collected = False
                        st.session_state.all_questions = None
                        st.success("✅ Processing complete! Download your file below.")
                        st.rerun()
                    else:
                        st.error("Processing did not complete successfully.")
                        st.session_state.processing = False
                        st.session_state.processing_started = False
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                    st.exception(e)
                    st.session_state.processing = False
                    st.session_state.processing_started = False
                if not st.session_state.processing_started:
                    if st.button("🚀 Start Processing", type="primary"):
                        # Reset cache and progress when starting fresh
                        st.session_state.processing_cache = {
                            'partial_matches': {},
                            'variants': {},
                            'related': {}
                        }
                        if 'matched_products_data' in st.session_state:
                            del st.session_state.matched_products_data
                        if 'processing_phase' in st.session_state:
                            del st.session_state.processing_phase
                        st.session_state.processing_started = True
                        st.session_state.processing = True
                        st.rerun()
                
                if st.session_state.processing_started:
                    if st.button("🚀 Process Files", type="primary", disabled=st.session_state.processing):
                        st.session_state.processing = True
                        st.session_state.processing_complete = False
                    
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir2:
                            input_path2 = os.path.join(temp_dir2, input_file.name)
                            reference_path2 = os.path.join(temp_dir2, reference_file.name)
                            output_path = os.path.join(temp_dir2, f"output_{brand}.xlsx")
                            
                            with open(input_path2, "wb") as f:
                                f.write(input_file.getbuffer())
                            with open(reference_path2, "wb") as f:
                                f.write(reference_file.getbuffer())
                            
                            with st.spinner(f"Processing {brand} files... This may take a few minutes."):
                                if brand == "Unicharm":
                                    result = process_unicharm_sales_interactive(
                                        input_path2, reference_path2, output_path, 
                                        selected_state=selected_state,
                                        warehouse_name=warehouse_name,
                                        low_price_reason=low_price_reason,
                                        buyer_branch_id=buyer_branch_id,
                                        processing_cache=st.session_state.processing_cache
                                    )
                                elif brand == "Britannia":
                                    result = process_britannia_sales_interactive(
                                        input_path2, reference_path2, output_path, 
                                        selected_state=selected_state,
                                        processing_cache=st.session_state.processing_cache
                                    )
                                elif brand == "Marico":
                                    result = process_marico_sales_interactive(
                                        input_path2, reference_path2, output_path, 
                                        selected_state=selected_state,
                                        processing_cache=st.session_state.processing_cache
                                    )
                                elif brand == "HUL":
                                    result = process_hul_sales_interactive(
                                        input_path2, reference_path2, output_path, 
                                        selected_state=selected_state,
                                        processing_cache=st.session_state.processing_cache
                                    )
                                
                                # If result is None, processing paused for user input
                                if result is None:
                                    st.stop()
                            
                            if os.path.exists(output_path):
                                with open(output_path, "rb") as f:
                                    st.session_state.output_file = f.read()
                                st.session_state.processing_complete = True
                                st.success("✅ Processing complete! Download your file below.")
                            else:
                                st.error("Output file was not created.")
                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")
                        st.exception(e)
                    finally:
                        st.session_state.processing = False
                    
    except Exception as e:
        st.error(f"Error loading files: {str(e)}")
        st.exception(e)

# Download button
if st.session_state.processing_complete and st.session_state.output_file:
    st.download_button(
        label="📥 Download Processed File",
        data=st.session_state.output_file,
        file_name=f"processed_{brand}_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Instructions
with st.expander("ℹ️ Instructions"):
    st.markdown("""
    ### How to use:
    1. **Select Brand**: Choose the brand (HUL, Unicharm, Britannia, or Marico)
    2. **Upload Input File**: Upload your sales/order Excel file
    3. **Upload Reference File**: Upload your reference file containing:
       - Product Details sheet
       - merchant_data sheet
    4. **Select State**: Choose the state to filter merchants
    5. **Start Processing**: Click "Start Processing" button
    6. **Answer Questions**: As processing runs, you'll be asked to confirm matches (Use/Discard buttons)
    7. **Download**: Download the processed output file
    
    ### Output Sheets:
    - **Sale Order Demo**: Valid orders (100% match)
    - **Partially Matched**: Orders needing review (70-99% match)
    - **Error Rows**: Orders with errors (<70% match)
    - **Sales Return Sheet**: Negative quantity orders
    """)
