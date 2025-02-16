from fastapi import Request
import logging
import time
from datetime import datetime

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logging.info(
        f"[{datetime.now()}] {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Process Time: {process_time:.2f}s"
    )
    
    return response 