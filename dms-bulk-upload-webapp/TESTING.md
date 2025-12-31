# Testing Guide for DMS Bulk Upload Web App

## Step 1: Install Dependencies

First, make sure all required packages are installed:

```bash
cd /Users/priyaljaiswal/Desktop/Code/dms-bulk-upload-webapp
pip install -r requirements.txt
```

If you encounter any issues, install packages individually:
```bash
pip install streamlit pandas numpy fuzzywuzzy python-Levenshtein openpyxl xlrd tqdm
```

## Step 2: Run the Streamlit App

Start the web application:

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

If it doesn't open automatically, you can manually navigate to that URL.

## Step 3: Test the Application

### Test Scenario 1: Basic File Upload

1. **Select Brand**: Choose "HUL" from the dropdown
2. **Upload Input File**: 
   - Use a test Excel file (you can use one of your existing files from `/Users/priyaljaiswal/Downloads/dms/`)
   - Or create a simple test file with columns: Bill Number, Bill Date, Product Description, Party, Units, Net Sales
3. **Upload Reference File**: 
   - Upload your reference file with "Product Details" and "merchant_data" sheets
4. **Select State**: Choose a state from the dropdown
5. **Click "Process Files"**: Wait for processing to complete
6. **Download**: Click the download button to get the processed file

### Test Scenario 2: Test All Brands

Repeat the above steps for each brand:
- HUL
- Unicharm (requires warehouse_name, low_price_reason, buyer_branch_id inputs)
- Britannia
- Marico

### Test Scenario 3: Error Handling

1. Try uploading without selecting files - should show error
2. Try uploading wrong file format - should show error
3. Try processing with missing columns - should show appropriate error messages

## Step 4: Verify Output

Check the downloaded Excel file has these sheets:
- ✅ Sale Order Demo (valid orders)
- ⚠️ Partially Matched (if any partial matches)
- ❌ Error Rows (if any errors)
- 🔄 Sales Return Sheet (if negative quantities)
- Product Details
- merchant_data

## Troubleshooting

### Issue: Module not found errors
**Solution**: Make sure you're in the correct directory and all dependencies are installed:
```bash
cd /Users/priyaljaiswal/Desktop/Code/dms-bulk-upload-webapp
pip install -r requirements.txt
```

### Issue: Streamlit not found
**Solution**: Install streamlit:
```bash
pip install streamlit
```

### Issue: Port already in use
**Solution**: Use a different port:
```bash
streamlit run app.py --server.port 8502
```

### Issue: Processing fails
**Solution**: 
- Check that your input file has the expected columns
- Check that your reference file has "Product Details" and "merchant_data" sheets
- Check the error message in the Streamlit app for details

## Quick Test Command

You can also test if the processors work directly:

```python
# Test HUL processor
from hul_processor import process_hul_sales
process_hul_sales(
    input_file="/path/to/input.xlsx",
    reference_file="/path/to/reference.xlsx",
    output_file="/path/to/output.xlsx",
    selected_state="Your State"
)
```

## Expected Behavior

✅ **Success Indicators:**
- Files upload successfully
- State selection works
- Processing shows progress bars
- Output file is generated
- Download button appears after processing

❌ **Error Indicators:**
- Red error messages in the app
- Processing fails with exception
- No output file generated


