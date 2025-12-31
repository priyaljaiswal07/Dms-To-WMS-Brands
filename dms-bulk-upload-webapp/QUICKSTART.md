# Quick Start Guide

## Installation

1. Navigate to the project directory:
```bash
cd dms-bulk-upload-webapp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the App

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Steps

1. **Select Brand**: Choose from dropdown (HUL, Unicharm, Britannia, Marico)

2. **Upload Files**:
   - **Input File**: Your sales/order Excel file
   - **Reference File**: Excel file with "Product Details" and "merchant_data" sheets

3. **Configure**:
   - Select state from dropdown
   - For Unicharm: Enter warehouse name, low price reason, buyer branch ID (optional)

4. **Process**: Click "🚀 Process Files" button

5. **Download**: Once processing is complete, download the output file

## Output File Structure

The output Excel file contains:
- **Sale Order Demo**: Valid orders (100% match) - Ready to use
- **Partially Matched**: Orders with 70-99% match - Review needed (Yellow highlight)
- **Error Rows**: Orders with errors - Requires correction (Red highlight)
- **Sales Return Sheet**: Negative quantity orders
- **Product Details**: Reference product data
- **merchant_data**: Reference merchant data

## Notes

- Original scripts in `../scripts/` are not modified
- Processing may take a few minutes for large files
- Progress bars show matching and batch allocation progress
- All brand-specific column mappings are auto-detected


