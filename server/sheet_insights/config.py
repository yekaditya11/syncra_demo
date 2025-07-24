import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Optimized client with connection pooling and timeouts
client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version="2025-01-01-preview",
    timeout=15.0,  # Reduced timeout for faster failure detection
    max_retries=2   # Reduced retries for faster processing
)

# Note: async_client removed to avoid import issues
# Will use regular client with asyncio.to_thread for async processing

from llama_cloud_services import LlamaParse

# Optimize LlamaParse for maximum speed
parser = LlamaParse(
    api_key=os.getenv("LLAMA_API_KEY"),
    num_workers=8,  # Increased from 4 to 8 for faster parallel processing
    verbose=False,  # Disable verbose for speed
    language="en",
    show_progress=False,  # Disable progress for speed
    fast_mode=True,  # Enable fast mode for quicker processing
    premium_mode=False,  # Disable premium features for speed
    target_pages=None,  # Process all pages
    split_by_page=False,  # Don't split for faster processing
)

