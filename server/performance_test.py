#!/usr/bin/env python3
"""
Performance testing script for the optimized Excel processing system.
Run this to verify the speed improvements.
"""

import time
import requests
import json
from pathlib import Path

API_URL = "http://localhost:8001"

def test_api_health():
    """Test if the API is running"""
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API is running")
            print(f"📊 Performance optimizations: {data.get('performance_optimizations', {})}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def test_file_processing(file_path):
    """Test file processing speed"""
    if not Path(file_path).exists():
        print(f"❌ Test file not found: {file_path}")
        return None
    
    print(f"🚀 Testing file processing with: {file_path}")
    start_time = time.time()
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_URL}/upload_excel/",
                files=files,
                timeout=120  # 2 minute timeout
            )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            sheets_processed = len(data.get('processed_sheets', []))
            insights_count = len(data.get('general-insights', []))
            
            print(f"✅ Processing completed successfully!")
            print(f"⏱️  Total time: {processing_time:.2f} seconds")
            print(f"📋 Sheets processed: {sheets_processed}")
            print(f"💡 Insights generated: {insights_count}")
            print(f"⚡ Average time per sheet: {processing_time/max(sheets_processed, 1):.2f}s")
            
            return {
                'success': True,
                'processing_time': processing_time,
                'sheets_processed': sheets_processed,
                'insights_count': insights_count,
                'time_per_sheet': processing_time/max(sheets_processed, 1)
            }
        else:
            print(f"❌ Processing failed with status: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Processing failed after {processing_time:.2f}s: {e}")
        return None

def main():
    """Run performance tests"""
    print("🔬 Starting Performance Tests")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ Cannot proceed - API is not running")
        return
    
    print("\n" + "=" * 50)
    
    # Look for test files in uploads directory
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        excel_files = list(uploads_dir.glob("*.xlsx"))
        if excel_files:
            print(f"📁 Found {len(excel_files)} Excel files for testing")
            
            for file_path in excel_files[:1]:  # Test with first file only
                print(f"\n📊 Testing with: {file_path.name}")
                result = test_file_processing(file_path)
                
                if result:
                    print(f"\n🎯 Performance Summary:")
                    print(f"   • Total processing time: {result['processing_time']:.2f}s")
                    print(f"   • Sheets processed: {result['sheets_processed']}")
                    print(f"   • Time per sheet: {result['time_per_sheet']:.2f}s")
                    
                    # Performance benchmarks
                    if result['time_per_sheet'] < 5:
                        print("   🚀 EXCELLENT: Very fast processing!")
                    elif result['time_per_sheet'] < 10:
                        print("   ✅ GOOD: Fast processing")
                    elif result['time_per_sheet'] < 20:
                        print("   ⚠️  MODERATE: Acceptable speed")
                    else:
                        print("   🐌 SLOW: Consider further optimization")
                
                break
        else:
            print("❌ No Excel files found in uploads directory")
            print("💡 Please upload an Excel file first to test performance")
    else:
        print("❌ Uploads directory not found")
    
    print("\n" + "=" * 50)
    print("🏁 Performance testing completed")

if __name__ == "__main__":
    main()
