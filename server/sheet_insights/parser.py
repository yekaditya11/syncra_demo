import re
from pathlib import Path
import openpyxl
from concurrent.futures import ThreadPoolExecutor
import time

def get_sheet_names(file_path):
    """Extract all sheet names from Excel file with optimized loading"""
    try:
        # Use read_only and data_only for faster loading
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        names = workbook.sheetnames
        workbook.close()
        print(f"📋 Found {len(names)} sheets: {names}")
        return names
    except Exception as e:
        print(f"❌ Failed to load sheet names: {e}")
        return []

def format_metadata(sheet):
    """Extract and format metadata from the top few rows of the Excel sheet"""
    metadata = []
    for row in sheet.iter_rows(min_row=1, max_row=5, values_only=True):
        line = ' '.join([str(cell).strip() for cell in row if cell])
        if line:
            metadata.append(line)
    return metadata

def extract_table(sheet):
    """Extract and format the core table with optimized processing"""
    start_row = 6  # Adjust based on where your actual data starts

    # Limit rows for faster processing - only take first 50 rows of data
    max_rows = start_row + 50
    rows = list(sheet.iter_rows(min_row=start_row, max_row=max_rows, values_only=True))

    # Filter out completely empty rows
    rows = [row for row in rows if any(cell for cell in row)]

    if not rows:
        return ["| No data found |", "| --- |"]

    # Find max number of columns from first few rows for speed
    max_cols = max(len(row) for row in rows[:10] if row)

    # Convert to markdown with optimized processing
    markdown_lines = []
    for i, row in enumerate(rows):
        # Pad row to max_cols length
        padded_row = list(row) + [''] * (max_cols - len(row))

        # Clean and format cells
        cells = []
        for cell in padded_row[:max_cols]:  # Limit columns
            if cell is not None:
                cell_str = str(cell).replace('\n', ' ').replace('|', '').strip()
                # Truncate very long cells for speed
                if len(cell_str) > 50:
                    cell_str = cell_str[:47] + "..."
                cells.append(cell_str)
            else:
                cells.append('')

        line = '| ' + ' | '.join(cells) + ' |'
        markdown_lines.append(line)

        # Add header separator after first row
        if i == 0:
            markdown_lines.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')

    return markdown_lines

def process_single_sheet(args):
    """Process a single sheet - for parallel processing"""
    sheet_name, file_path, output_dir, name_mapping = args
    try:
        # Load workbook for this sheet only
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb[sheet_name]

        clean_sheet_name = re.sub(r'[^\w\-_]', '_', sheet_name.strip())
        clean_sheet_name = re.sub(r'_+', '_', clean_sheet_name).strip('_')

        markdown_path = output_dir / f"{clean_sheet_name}.md"
        counter = 1
        while markdown_path.exists():
            markdown_path = output_dir / f"{clean_sheet_name}_{counter}.md"
            counter += 1

        metadata_lines = format_metadata(sheet)
        table_lines = extract_table(sheet)

        # Write file with minimal content for speed
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(f"## {sheet_name}\n\n")
            # Skip metadata for speed
            for line in table_lines:
                f.write(line + "\n")

        wb.close()
        name_mapping[markdown_path.stem] = sheet_name
        print(f"✅ Processed: {sheet_name}")
        return markdown_path, sheet_name

    except Exception as e:
        print(f"❌ Failed to process {sheet_name}: {e}")
        return None, sheet_name


def extract_markdown(file_path, output_dir, sheets_to_process=None, skip_first_sheet=True):
    """Optimized markdown extraction with parallel processing"""
    start_time = time.time()

    all_sheet_names = get_sheet_names(file_path)
    if not all_sheet_names:
        return [], {}

    if sheets_to_process:
        target_sheets = sheets_to_process
    else:
        target_sheets = all_sheet_names[2:] if skip_first_sheet else all_sheet_names

    print(f"📋 Processing {len(target_sheets)} sheet(s) in parallel: {target_sheets}")

    markdown_paths = []
    name_mapping = {}

    # Prepare arguments for parallel processing
    args_list = [
        (sheet_name, file_path, output_dir, name_mapping)
        for sheet_name in target_sheets
    ]

    # Use parallel processing for sheet extraction
    max_workers = min(len(target_sheets), 6)  # Limit workers to avoid memory issues

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_single_sheet, args_list))

    # Collect successful results
    for markdown_path, sheet_name in results:
        if markdown_path:
            markdown_paths.append(markdown_path)

    processing_time = time.time() - start_time
    print(f"⚡ Markdown extraction completed in {processing_time:.2f}s")

    return markdown_paths, name_mapping
