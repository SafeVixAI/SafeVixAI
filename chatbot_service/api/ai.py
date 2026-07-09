# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request

logger = logging.getLogger(__name__)

from services.pothole_validator import PotholeValidator
from api.chat import verify_internal_auth
from limiter import limiter

router = APIRouter(prefix='/api/v1/ai', tags=['AI'])

MAX_IMAGE_BYTES = 5 * 1024 * 1024

@router.post('/validate-image')
@limiter.limit("10/minute")
async def validate_image(
    request: Request,
    file: UploadFile = File(...),
    _auth: None = Depends(verify_internal_auth),
):
    """
    Validate uploaded image using YOLOv8 pothole/road distress model.
    """
    try:
        content_type = (file.content_type or '').lower()
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed.")
        
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        if len(contents) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail=f"Image too large (max {MAX_IMAGE_BYTES // 1024 // 1024} MB).")
            
        result = PotholeValidator.validate_image(contents)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image validation endpoint failed")
        raise HTTPException(status_code=500, detail=str(e))

