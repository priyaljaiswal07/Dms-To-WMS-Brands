"""
Base processor module with Streamlit-compatible functions.
This module provides utility functions and a framework for processing
that works with Streamlit widgets instead of CLI input().
"""
import pandas as pd
import numpy as np
from fuzzywuzzy import process, fuzz
import os
import streamlit as st
from tqdm import tqdm

def normalize_name(name):
    """Normalize name by trimming spaces and cleaning whitespace."""
    if pd.isna(name):
        return ""
    cleaned = " ".join(str(name).strip().split())
    return cleaned

def fuzzy_match_name(name, choices, min_score=0):
    """Return best match and score (0-100). Only returns match if score >= min_score."""
    normalized_input = normalize_name(name)
    if not normalized_input:
        return "", 0
    
    normalized_choices = {normalize_name(c): c for c in choices if normalize_name(c)}
    normalized_choice_list = list(normalized_choices.keys())
    
    result = process.extractOne(normalized_input, normalized_choice_list, scorer=fuzz.token_sort_ratio)
    if result:
        match_normalized, score = result
        match = normalized_choices.get(match_normalized, match_normalized)
        if score >= min_score:
            return match, score
        else:
            return "", 0
    return "", 0

def exact_match_name(name, choices):
    """Return exact match only (case-insensitive, whitespace normalized)."""
    normalized_input = normalize_name(name).lower()
    if not normalized_input:
        return "", 0
    
    for choice in choices:
        normalized_choice = normalize_name(choice).lower()
        if normalized_input == normalized_choice:
            return choice, 100
    return "", 0

def safe_read_excel(file_path, **kwargs):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".xls":
        return pd.read_excel(file_path, engine="xlrd", **kwargs)
    elif ext == ".xlsx":
        return pd.read_excel(file_path, engine="openpyxl", **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def get_column_mapping_streamlit(df, expected, optional_columns=None):
    """
    Get column mapping using Streamlit widgets.
    
    Args:
        df: DataFrame with columns to map
        expected: Dict of {key: default_column_name}
        optional_columns: List of optional column keys
    
    Returns:
        Dict of {key: selected_column_name}
    """
    if optional_columns is None:
        optional_columns = []
    
    mapping = {}
    columns_list = df.columns.tolist()
    
    # Create a form for column mapping
    with st.form("column_mapping_form"):
        st.subheader("📋 Column Mapping")
        st.info("Map your input file columns to the required fields")
        
        for key, default in expected.items():
            if key in optional_columns:
                # Optional column
                if default in columns_list:
                    default_idx = columns_list.index(default)
                    selected = st.selectbox(
                        f"{key} (Optional)",
                        columns_list,
                        index=default_idx,
                        key=f"col_{key}",
                        help=f"Default: {default}"
                    )
                    mapping[key] = selected
                else:
                    st.info(f"⚠️ {key} column not found. Will use default value or leave blank.")
                    mapping[key] = None
            else:
                # Required column
                if default in columns_list:
                    default_idx = columns_list.index(default)
                    selected = st.selectbox(
                        f"{key} *",
                        columns_list,
                        index=default_idx,
                        key=f"col_{key}",
                        help=f"Default: {default}"
                    )
                    mapping[key] = selected
                else:
                    st.warning(f"⚠️ Default column '{default}' not found for {key}. Please select manually.")
                    selected = st.selectbox(
                        f"{key} *",
                        columns_list,
                        key=f"col_{key}"
                    )
                    mapping[key] = selected
        
        submitted = st.form_submit_button("✅ Confirm Column Mapping")
    
    if not submitted:
        st.stop()
    
    return mapping

def get_state_selection_streamlit(merchant_df):
    """Get state selection using Streamlit widget."""
    unique_states = merchant_df["shop_state"].dropna().unique().tolist()
    if not unique_states:
        raise RuntimeError("No states found in merchant_data.shop_state")
    
    selected_state = st.selectbox(
        "Select State",
        unique_states,
        key="state_selection",
        help="Select the state to filter merchants"
    )
    
    return selected_state

def handle_partial_match_confirmation_streamlit(prod, match, score, cache_key, partial_matches_cache):
    """
    Handle partial match confirmation using Streamlit.
    Returns (match, score, user_confirmed) tuple.
    """
    if cache_key in partial_matches_cache:
        cached_match, cached_score, cached_decision = partial_matches_cache[cache_key]
        return cached_match, cached_score, cached_decision
    
    # Store in session state for confirmation
    if 'pending_confirmations' not in st.session_state:
        st.session_state.pending_confirmations = {}
    
    st.session_state.pending_confirmations[cache_key] = {
        'prod': prod,
        'match': match,
        'score': score
    }
    
    # Return False for now, will be confirmed later
    return match, score, False

def handle_variant_confirmation_streamlit(pname, variant, variant_stock, current_stock, qty, cache_key, variant_confirmation_cache):
    """Handle product variant confirmation using Streamlit."""
    if cache_key in variant_confirmation_cache:
        return variant_confirmation_cache[cache_key]
    
    # Store in session state
    if 'pending_variants' not in st.session_state:
        st.session_state.pending_variants = {}
    
    st.session_state.pending_variants[cache_key] = {
        'pname': pname,
        'variant': variant,
        'variant_stock': variant_stock,
        'current_stock': current_stock,
        'qty': qty
    }
    
    return None  # Will be confirmed later

def handle_related_product_confirmation_streamlit(pname, rp, rp_stock, total_stock, qty, related_product_cache):
    """Handle related product confirmation using Streamlit."""
    if pname in related_product_cache:
        return related_product_cache[pname]
    
    # Store in session state
    if 'pending_related' not in st.session_state:
        st.session_state.pending_related = {}
    
    key = f"{pname}|{rp}"
    st.session_state.pending_related[key] = {
        'pname': pname,
        'rp': rp,
        'rp_stock': rp_stock,
        'total_stock': total_stock,
        'qty': qty
    }
    
    return None


