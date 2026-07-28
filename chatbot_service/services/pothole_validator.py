# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import io
import logging
import os

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None  # type: ignore[assignment]

from PIL import Image

logger = logging.getLogger(__name__)

# Path to YOLO model
MODEL_PATH = os.environ.get("POTHOLE_MODEL_PATH", "../backend/models/pothole.pt")

class PotholeValidator:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is not None:
            return cls._model
        yolo_cls = YOLO
        if yolo_cls is None:
            try:
                from ultralytics import YOLO as yolo_cls  # noqa: N811
            except ImportError:
                msg = "ultralytics is not installed. Install with: pip install ultralytics"
                raise ImportError(msg) from None
        if cls._model is None:
            # Check relative and absolute paths
            paths_to_check = [
                MODEL_PATH,
                "../backend/models/pothole.pt",
                "./models/pothole.pt",
                "models/pothole.pt"
            ]
            selected_path = None
            for p in paths_to_check:
                if os.path.exists(p):
                    selected_path = p
                    break

            if not selected_path:
                logger.error("YOLO model file not found in paths: %s", paths_to_check)
                msg = "YOLO model not found in target directories."
                raise FileNotFoundError(msg)

            logger.info("Loading YOLOv8 pothole model from %s", selected_path)
            cls._model = yolo_cls(selected_path)
        return cls._model

    @classmethod
    def validate_image(cls, image_bytes: bytes) -> dict:
        """
        Validate if pothole or road anomaly is present in the image.
        Returns a dict with:
        - anomaly_detected: bool
        - confidence: float (0.0 to 1.0)
        - boxes: list of bounding boxes
        """
        try:
            model = cls.get_model()
            image = Image.open(io.BytesIO(image_bytes))
            results = model(image)

            anomaly_detected = False
            max_confidence = 0.0
            boxes_data = []

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = model.names[cls_id]

                    # Accept any anomaly detection above threshold
                    if conf > 0.25:
                        anomaly_detected = True
                        if conf > max_confidence:  # pragma: no branch
                            max_confidence = conf

                        xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], 'tolist') else list(box.xyxy[0])
                        boxes_data.append({
                            "class": class_name,
                            "confidence": conf,
                            "box": xyxy
                        })

            return {
                "anomaly_detected": anomaly_detected,
                "confidence": max_confidence,
                "boxes": boxes_data,
                "success": True
            }
        except Exception as e:
            logger.exception("Failed to run YOLO pothole model")
            return {
                "anomaly_detected": False,
                "confidence": 0.0,
                "boxes": [],
                "success": False,
                "error": str(e)
            }
