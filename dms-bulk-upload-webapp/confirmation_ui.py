"""
UI components for collecting user confirmations for partial matches,
product variants, and related products.
"""
import streamlit as st
from typing import Dict, List, Tuple

def display_partial_matches_ui(partial_matches: List[Dict]) -> Dict[str, bool]:
    """
    Display partial product matches for user confirmation.
    
    Args:
        partial_matches: List of dicts with keys: 'input_product', 'matched_product', 'score', 'cache_key'
    
    Returns:
        Dict mapping cache_key to True/False (accepted/rejected)
    """
    if not partial_matches:
        return {}
    
    st.subheader("⚠️ Partial Product Matches (70-99% similarity)")
    st.info("Please review and confirm or reject each partial match. These are products with 70-99% similarity.")
    
    decisions = {}
    
    for idx, match in enumerate(partial_matches):
        cache_key = match['cache_key']
        input_prod = match['input_product']
        matched_prod = match['matched_product']
        score = match['score']
        
        # Initialize in session state if not exists
        if f"partial_match_{cache_key}" not in st.session_state:
            st.session_state[f"partial_match_{cache_key}"] = None
        
        col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
        
        with col1:
            st.markdown(f"**Input:** `{input_prod}`")
        with col2:
            st.markdown(f"**Matched:** `{matched_prod}`")
        with col3:
            st.metric("Score", f"{int(score)}%")
        with col4:
            # Buttons
            if st.button("✅ Accept", key=f"accept_{cache_key}", type="primary"):
                st.session_state[f"partial_match_{cache_key}"] = True
                st.rerun()
            if st.button("❌ Reject", key=f"reject_{cache_key}"):
                st.session_state[f"partial_match_{cache_key}"] = False
                st.rerun()
        
        # Show current decision
        current_decision = st.session_state.get(f"partial_match_{cache_key}")
        if current_decision is True:
            st.success(f"✅ ACCEPTED: '{input_prod}' → '{matched_prod}'")
        elif current_decision is False:
            st.error(f"❌ REJECTED: '{input_prod}' → '{matched_prod}'")
        
        # Store decision (default to None if not set)
        decisions[cache_key] = current_decision if current_decision is not None else None
        st.divider()
    
    return decisions

def display_variant_confirmations_ui(variants: List[Dict]) -> Dict[str, bool]:
    """
    Display product variant confirmations for user approval.
    
    Args:
        variants: List of dicts with keys: 'main_product', 'variant', 'main_stock', 'variant_stock', 'required_qty', 'cache_key'
    
    Returns:
        Dict mapping cache_key to True/False
    """
    if not variants:
        return {}
    
    st.subheader("🔄 Product Variants (Same Product ID)")
    st.info("These are products with the same Product ID but different names. Should we use inventory from variants?")
    
    decisions = {}
    
    for idx, variant_info in enumerate(variants):
        cache_key = variant_info['cache_key']
        main_prod = variant_info['main_product']
        variant_prod = variant_info['variant']
        main_stock = variant_info['main_stock']
        variant_stock = variant_info['variant_stock']
        required_qty = variant_info['required_qty']
        
        if f"variant_{cache_key}" not in st.session_state:
            st.session_state[f"variant_{cache_key}"] = None
        
        st.markdown(f"**Main Product:** `{main_prod}` (Available: {int(main_stock)} units)")
        st.markdown(f"**Variant:** `{variant_prod}` (Available: {int(variant_stock)} units)")
        st.markdown(f"**Required:** {int(required_qty)} units")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Use Variant", key=f"use_variant_{cache_key}", type="primary"):
                st.session_state[f"variant_{cache_key}"] = True
                st.rerun()
        with col2:
            if st.button("❌ Don't Use", key=f"skip_variant_{cache_key}"):
                st.session_state[f"variant_{cache_key}"] = False
                st.rerun()
        
        current_decision = st.session_state.get(f"variant_{cache_key}")
        if current_decision is True:
            st.success(f"✅ Will use inventory from '{variant_prod}' for '{main_prod}'")
        elif current_decision is False:
            st.error(f"❌ Will NOT use inventory from '{variant_prod}'")
        
        decisions[cache_key] = current_decision if current_decision is not None else None
        st.divider()
    
    return decisions

def display_related_products_ui(related_products: List[Dict]) -> Dict[str, bool]:
    """
    Display related product confirmations (for insufficient stock scenarios).
    
    Args:
        related_products: List of dicts with keys: 'main_product', 'related_product', 'main_stock', 'related_stock', 'required_qty', 'total_stock', 'cache_key'
    
    Returns:
        Dict mapping cache_key to True/False
    """
    if not related_products:
        return {}
    
    st.subheader("🔍 Related Products (Insufficient Stock)")
    st.warning("Stock is insufficient. Found similar products. Are these the SAME product?")
    
    decisions = {}
    
    for idx, rel_info in enumerate(related_products):
        cache_key = rel_info['cache_key']
        main_prod = rel_info['main_product']
        related_prod = rel_info['related_product']
        main_stock = rel_info['main_stock']
        related_stock = rel_info['related_stock']
        required_qty = rel_info['required_qty']
        total_stock = rel_info['total_stock']
        shortage = required_qty - total_stock
        
        if f"related_{cache_key}" not in st.session_state:
            st.session_state[f"related_{cache_key}"] = None
        
        st.markdown(f"**Product:** `{main_prod}`")
        st.markdown(f"**Required:** {int(required_qty)} units | **Available:** {int(total_stock)} units | **Shortage:** {int(shortage)} units")
        st.markdown(f"**Similar Product:** `{related_prod}` (Available: {int(related_stock)} units)")
        st.markdown("**Question:** Are these the SAME product?")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Same Product", key=f"same_{cache_key}", type="primary"):
                st.session_state[f"related_{cache_key}"] = True
                st.rerun()
        with col2:
            if st.button("❌ Different Product", key=f"different_{cache_key}"):
                st.session_state[f"related_{cache_key}"] = False
                st.rerun()
        
        current_decision = st.session_state.get(f"related_{cache_key}")
        if current_decision is True:
            st.success(f"✅ Will use stock from '{related_prod}' for '{main_prod}'")
        elif current_decision is False:
            st.error(f"❌ Will NOT use stock from '{related_prod}'")
        
        decisions[cache_key] = current_decision if current_decision is not None else None
        st.divider()
    
    return decisions

def check_all_confirmations_complete(
    partial_decisions: Dict,
    variant_decisions: Dict,
    related_decisions: Dict
) -> bool:
    """Check if all confirmations have been made."""
    all_partial = all(v is not None for v in partial_decisions.values())
    all_variants = all(v is not None for v in variant_decisions.values())
    all_related = all(v is not None for v in related_decisions.values())
    
    return all_partial and all_variants and all_related

