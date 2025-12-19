
import os
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from loaders import get_document_ai_loader

def main():
    print(f"Current LOADER_STRATEGY: {config.LOADER_STRATEGY}")
    
    # Force strategy if not set (for testing purposes only, or rely on env)
    # os.environ["LOADER_STRATEGY"] = "vertex_ai"
    # Reload config? config is already loaded. 
    # Let's assume user/env sets it, or we hack it here:
    config.LOADER_STRATEGY = "vertex_ai"
    print(f"Forced LOADER_STRATEGY: {config.LOADER_STRATEGY}")
    
    loader = get_document_ai_loader()
    print(f"Loader Instance: {type(loader)}")
    
    # We won't actually run a PDF processing job unless there is a dummy PDF available and credentials.
    # This script just verifies instantiation and imports work.
    
    print("Verification Successful: Loader instantiated correctly.")

if __name__ == "__main__":
    main()
