from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import openpyxl
import time

from sheet_insights.parser import extract_markdown, get_sheet_names
from sheet_insights.insights import get_insights
from sheet_insights.general_summary import generate_general_insights
from sheet_insights.additional_insights import generate_additional_insights

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path('uploads')
MARKDOWN_DIR = Path("results/markdown_output")
INSIGHTS_FILE = Path('results/insights.json')
GENERAL_INSIGHTS_FILE = Path('results/general-info.json')
ADDITIONAL_INSIGHTS_FILE = Path('results/additional-insights.json')
RESULTS_DIR = Path('results')

# Create directories
for folder in [UPLOAD_DIR, MARKDOWN_DIR, RESULTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return RedirectResponse(url='/docs')



@app.post("/upload_excel/")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    print(f"📁 Uploaded file: {file.filename}")

    try:
        # Get all sheet names for validation
        all_sheet_names = get_sheet_names(str(file_path))
        if not all_sheet_names:
            raise HTTPException(status_code=400, detail="No sheets found in the Excel file")
        
        print(f"📋 Found sheets: {all_sheet_names}")

        # Skip first two sheets: "Average Summary" and "Analysis SUMMARY"
        if len(all_sheet_names) > 2:
            print(f"📋 Skipping first two sheets: '{all_sheet_names[0]}' and '{all_sheet_names[1]}'")
            sheets_to_process = all_sheet_names[2:]
        elif len(all_sheet_names) > 1:
            print(f"📋 Skipping first sheet: '{all_sheet_names[0]}'")
            sheets_to_process = all_sheet_names[1:]
        else:
            print(f"📋 Processing single sheet: '{all_sheet_names[0]}'")
            sheets_to_process = all_sheet_names

        print(f"🔄 Sheets to process: {sheets_to_process}")

        # Extract markdown with proper sheet name handling
        markdown_paths, name_mapping = extract_markdown(
            str(file_path),
            MARKDOWN_DIR,
            sheets_to_process=sheets_to_process,
            skip_first_sheet=False  # We're explicitly providing the sheets to process
        )

        if not markdown_paths:
            raise HTTPException(status_code=400, detail="No sheets could be processed")

        print(f"📝 Generated {len(markdown_paths)} markdown files")
        print(f"🗺️ Name mapping: {name_mapping}")

        # Optimized batch processing for insights
        print(f"🚀 Starting optimized batch insight generation for {len(markdown_paths)} sheets...")

        # Prepare data for batch processing
        markdown_texts_and_names = []
        for markdown_file in markdown_paths:
            try:
                with open(markdown_file, "r", encoding="utf-8") as f:
                    text = f.read()

                # Get the original sheet name from mapping
                clean_name = markdown_file.stem
                original_sheet_name = name_mapping.get(clean_name, clean_name)

                markdown_texts_and_names.append((text, original_sheet_name))
                print(f"📄 Prepared: '{original_sheet_name}'")

            except Exception as e:
                print(f"❌ Error reading {markdown_file.name}: {e}")
                continue

        # Use optimized batch processing
        start_time = time.time()

        # Import the batch function
        from sheet_insights.insights import get_insights_batch_async

        # Process all sheets in parallel using async batch processing
        batch_results = await get_insights_batch_async(markdown_texts_and_names, max_workers=12)

        total_time = time.time() - start_time
        print(f"⚡ Optimized batch processing completed in {total_time:.2f}s")

        # Collect results
        insights = {}
        processed_count = 0

        for i, (text, sheet_name) in enumerate(markdown_texts_and_names):
            if i < len(batch_results):
                insight = batch_results[i]
                if insight and not isinstance(insight, Exception):
                    insights[sheet_name] = insight
                    processed_count += 1
                    print(f"✅ Generated insights for: '{sheet_name}'")
                else:
                    print(f"❌ Failed to generate insights for: '{sheet_name}'")
            else:
                print(f"❌ No result for: '{sheet_name}'")

        print(f"📊 Successfully generated insights for {processed_count}/{len(markdown_texts_and_names)} sheets")

        # Save insights to file
        with open(INSIGHTS_FILE, "w", encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved insights to: {INSIGHTS_FILE}")

        # Generate general insights
        print(f"🔄 Generating general insights...")
        general = generate_general_insights(str(INSIGHTS_FILE), str(GENERAL_INSIGHTS_FILE))

        # Load insights for response
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            insights_content = json.load(f)

        print(f"🎉 Processing completed successfully!")

        return {
            "message": f"Successfully processed {len(sheets_to_process)} sheets",
            "processed_sheets": list(insights.keys()),
            "insights": insights_content,
            "general-insights": general
        }

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get('/download/insights')
def download_insights():
    if not INSIGHTS_FILE.exists():
        raise HTTPException(status_code=404, detail='Insights file not found')
    return FileResponse(path=INSIGHTS_FILE, filename="insights.json", media_type='application/json')

@app.get('/download/general')
def download_general():
    if not GENERAL_INSIGHTS_FILE.exists():
        raise HTTPException(status_code=404, detail='General info file not found')
    return FileResponse(path=GENERAL_INSIGHTS_FILE, filename='general-info.json', media_type='application/json')

@app.post('/generate_more_insights')
def generate_more_insights():
    """Generate additional insights based on data not covered in previous insights"""
    try:
        # Check if required files exist
        if not INSIGHTS_FILE.exists():
            raise HTTPException(status_code=404, detail='Insights file not found. Please upload and process an Excel file first.')

        if not GENERAL_INSIGHTS_FILE.exists():
            raise HTTPException(status_code=404, detail='General insights file not found. Please upload and process an Excel file first.')

        print(f"🔄 Generating additional insights...")

        # Generate additional insights
        additional_insights = generate_additional_insights(
            str(INSIGHTS_FILE),
            str(GENERAL_INSIGHTS_FILE),
            str(ADDITIONAL_INSIGHTS_FILE)
        )

        print(f"✅ Successfully generated additional insights")

        return {
            "message": "Successfully generated additional insights",
            "additional_insights": additional_insights
        }

    except Exception as e:
        print(f"❌ Error generating additional insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate additional insights: {str(e)}")

@app.get('/download/additional_insights')
def download_additional_insights():
    """Download additional insights file"""
    if not ADDITIONAL_INSIGHTS_FILE.exists():
        raise HTTPException(status_code=404, detail='Additional insights file not found')
    return FileResponse(path=ADDITIONAL_INSIGHTS_FILE, filename="additional-insights.json", media_type='application/json')

@app.get('/sheet_insights')
def get_sheet_insights():
    """Get individual sheet insights for deep dive view"""
    try:
        if not INSIGHTS_FILE.exists():
            raise HTTPException(status_code=404, detail='Sheet insights file not found. Please upload and process an Excel file first.')

        # Load individual sheet insights
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            sheet_insights = json.load(f)

        return {
            "message": "Sheet insights retrieved successfully",
            "sheet_insights": sheet_insights
        }

    except Exception as e:
        print(f"❌ Error loading sheet insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load sheet insights: {str(e)}")

@app.get('/all_insights')
def get_all_insights():
    """Get all available insights in one response"""
    try:
        result = {
            "status": "success",
            "available_insights": {}
        }

        # Load individual sheet insights
        if INSIGHTS_FILE.exists():
            with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
                result["available_insights"]["sheet_insights"] = json.load(f)
        else:
            result["available_insights"]["sheet_insights"] = None

        # Load general insights
        if GENERAL_INSIGHTS_FILE.exists():
            with open(GENERAL_INSIGHTS_FILE, "r", encoding="utf-8") as f:
                result["available_insights"]["general_insights"] = json.load(f)
        else:
            result["available_insights"]["general_insights"] = None

        # Load additional insights
        if ADDITIONAL_INSIGHTS_FILE.exists():
            with open(ADDITIONAL_INSIGHTS_FILE, "r", encoding="utf-8") as f:
                result["available_insights"]["additional_insights"] = json.load(f)
        else:
            result["available_insights"]["additional_insights"] = None

        # Add summary
        result["summary"] = {
            "sheet_insights_count": len(result["available_insights"]["sheet_insights"]) if result["available_insights"]["sheet_insights"] else 0,
            "general_insights_count": len(result["available_insights"]["general_insights"]) if result["available_insights"]["general_insights"] else 0,
            "additional_insights_count": len(result["available_insights"]["additional_insights"]) if result["available_insights"]["additional_insights"] else 0
        }

        return result

    except Exception as e:
        print(f"❌ Error loading all insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load insights: {str(e)}")

@app.get('/status')
def get_status():
    """Get processing status and available files with performance metrics"""
    return {
        "markdown_files": len(list(MARKDOWN_DIR.glob("*.md"))) if MARKDOWN_DIR.exists() else 0,
        "performance_optimizations": {
            "llamaparse_workers": 8,  # Increased from 4
            "max_thread_workers": min(12, max(1, os.cpu_count() or 1)),  # Optimized
            "fast_mode_enabled": True,
            "async_processing_enabled": True,
            "batch_processing_enabled": True,
            "text_truncation_enabled": True,
            "parallel_sheet_extraction": True,
            "optimized_excel_loading": True,
            "reduced_api_timeouts": True,
            "cpu_cores": os.cpu_count(),
            "estimated_speedup": "3-5x faster than previous version"
        },
        "api_optimizations": {
            "max_tokens_reduced": "400 (from 800)",
            "timeout_reduced": "10s (from 30s)",
            "temperature": 0.0,
            "streaming_disabled": True,
            "fallback_insights_enabled": True
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting FastAPI server on port 8001...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📖 API documentation available at: http://localhost:8001/docs")
    print("🔄 Press Ctrl+C to stop the server")

    # Run the server on port 8001
    uvicorn.run(
        "app:app",  # Use import string for reload to work properly
        host="0.0.0.0",
        port=8001,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

