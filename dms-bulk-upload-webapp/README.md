# DMS Bulk Upload Web App

A Streamlit web application for processing bulk sales order uploads for multiple brands (HUL, Unicharm, Britannia, Marico).

## Features

- 📊 Upload input sales files and reference files
- 🔄 Automatic product and merchant matching
- 📦 Batch allocation with inventory management
- ✅ Categorization of orders (Valid, Partial, Error)
- 📥 Download processed Excel files with multiple sheets

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

## Usage

1. **Select Brand**: Choose from HUL, Unicharm, Britannia, or Marico
2. **Upload Input File**: Upload your sales/order Excel file
3. **Upload Reference File**: Upload reference file with:
   - Product Details sheet
   - merchant_data sheet
4. **Configure**: Select state and any brand-specific settings
5. **Process**: Click "Process Files" button
6. **Download**: Download the processed output file

## Output Sheets

- **Sale Order Demo**: Valid orders (100% match)
- **Partially Matched**: Orders needing review (70-99% match) - Yellow highlight
- **Error Rows**: Orders with errors (<70% match) - Red highlight
- **Sales Return Sheet**: Negative quantity orders

## Notes

- The original processing scripts in the `scripts/` directory are not modified
- This web app uses adapted processor functions that work with Streamlit
- Interactive confirmations are simplified for web use (auto-accept 100% matches, mark partials for review)


