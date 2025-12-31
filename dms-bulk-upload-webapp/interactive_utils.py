"""
Shared utility functions for interactive processors
"""
import streamlit as st

def ask_user_question_streamlit(question_type, question_data, processing_cache):
    """
    Ask user a question using Streamlit and return the answer.
    This function sets pending_question in session state.
    
    Returns: True/False (from cache) or None if waiting for user input
    """
    cache_key = question_data['cache_key']
    
    # Check cache first
    if question_type == 'partial_match':
        if cache_key in processing_cache['partial_matches']:
            return processing_cache['partial_matches'][cache_key]
    elif question_type == 'variant':
        if cache_key in processing_cache['variants']:
            return processing_cache['variants'][cache_key]
    elif question_type == 'related':
        if cache_key in processing_cache['related']:
            return processing_cache['related'][cache_key]
    
    # Not in cache - need to ask user
    # Set pending question in session state (will be handled by app.py)
    if st:
        st.session_state.pending_question = {
            'type': question_type,
            'cache_key': cache_key,
            **question_data
        }
        # Return None to indicate waiting for answer
        # app.py will show the question and handle the rerun
        return None
    
    # This should not be reached, but return False as default
    return False


