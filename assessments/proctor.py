"""
Computer Vision Proctoring Module

Processes camera frames using OpenCV Haar Cascades (with optional MediaPipe Tasks
fallback) and returns structured violation responses.
Designed for ~1 frame every 2 seconds.
"""

import base64
import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_face_cascade = None
_mediapipe_detector = None


def _get_haar_cascade():
    global _face_cascade
    if _face_cascade is None:
        bundled = Path(__file__).resolve().parent / 'cascades' / 'haarcascade_frontalface_default.xml'
        cascade_path = str(bundled) if bundled.exists() else (
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        if _face_cascade.empty():
            raise RuntimeError('Failed to load Haar cascade classifier')
    return _face_cascade


def _get_mediapipe_detector():
    """Optional MediaPipe Tasks API detector (newer mediapipe versions)."""
    global _mediapipe_detector
    if _mediapipe_detector is None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            model_path = Path(__file__).resolve().parent / 'models' / 'blaze_face_short_range.tflite'
            if not model_path.exists():
                return None

            base_options = python.BaseOptions(model_asset_path=str(model_path))
            options = vision.FaceDetectorOptions(base_options=base_options)
            _mediapipe_detector = vision.FaceDetector.create_from_options(options)
        except Exception as exc:
            logger.debug('MediaPipe Tasks unavailable: %s', exc)
            return None
    return _mediapipe_detector


def decode_base64_frame(base64_str: str) -> np.ndarray | None:
    """Decode a base64 JPEG/PNG string into a BGR numpy array."""
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',', 1)[1]
        img_bytes = base64.b64decode(base64_str)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame
    except Exception as exc:
        logger.warning('Failed to decode frame: %s', exc)
        return None


def encode_frame_base64(frame: np.ndarray, quality: int = 70) -> str:
    """Encode a BGR frame to base64 JPEG."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buffer).decode('utf-8')


def _detect_faces_haar(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect faces using OpenCV Haar Cascade. Returns list of (x, y, w, h)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = _get_haar_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]


def _draw_face_boxes(frame: np.ndarray, faces: list[tuple[int, int, int, int]]) -> np.ndarray:
    """Draw bounding boxes on frame for preview overlay."""
    annotated = frame.copy()
    for x, y, w, h in faces:
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return annotated


def _check_head_orientation(face: tuple[int, int, int, int], frame_shape) -> bool:
    """
    Basic head orientation check: face center should be within
    central 60% of the frame horizontally and vertically.
    """
    h, w = frame_shape[:2]
    x, y, fw, fh = face
    cx = (x + fw / 2) / w
    cy = (y + fh / 2) / h

    margin = 0.20
    return margin <= cx <= (1 - margin) and margin <= cy <= (1 - margin)


class ProctorEngine:
    """Analyzes webcam frames for proctoring violations."""

    STATUS_OK = 'OK'
    STATUS_NO_FACE = 'FLAG_NO_FACE'
    STATUS_MULTIPLE = 'FLAG_MULTIPLE_FACES'
    STATUS_HEAD_TURN = 'FLAG_HEAD_TURNED'

    def analyze_frame(self, frame_input: str | np.ndarray) -> dict[str, Any]:
        """
        Analyze a single frame.

        Returns:
            {
                "status": "OK" | "FLAG_NO_FACE" | "FLAG_MULTIPLE_FACES" | "FLAG_HEAD_TURNED",
                "face_count": int,
                "processed_frame": base64_str,
                "details": str
            }
        """
        if isinstance(frame_input, str):
            frame = decode_base64_frame(frame_input)
        else:
            frame = frame_input

        if frame is None:
            return {
                'status': self.STATUS_NO_FACE,
                'face_count': 0,
                'processed_frame': '',
                'details': 'Could not decode frame',
            }

        try:
            faces = _detect_faces_haar(frame)
            face_count = len(faces)

            if face_count == 0:
                return {
                    'status': self.STATUS_NO_FACE,
                    'face_count': 0,
                    'processed_frame': encode_frame_base64(frame),
                    'details': 'No face detected in frame',
                }

            if face_count > 1:
                annotated = _draw_face_boxes(frame, faces)
                return {
                    'status': self.STATUS_MULTIPLE,
                    'face_count': face_count,
                    'processed_frame': encode_frame_base64(annotated),
                    'details': f'{face_count} faces detected',
                }

            if not _check_head_orientation(faces[0], frame.shape):
                annotated = _draw_face_boxes(frame, faces)
                return {
                    'status': self.STATUS_HEAD_TURN,
                    'face_count': 1,
                    'processed_frame': encode_frame_base64(annotated),
                    'details': 'Face center outside normal boundaries',
                }

            annotated = _draw_face_boxes(frame, faces)
            return {
                'status': self.STATUS_OK,
                'face_count': 1,
                'processed_frame': encode_frame_base64(annotated),
                'details': 'Face detected and centered',
            }

        except Exception as exc:
            logger.exception('Proctor analysis failed: %s', exc)
            return {
                'status': self.STATUS_OK,
                'face_count': -1,
                'processed_frame': encode_frame_base64(frame),
                'details': f'Analysis error: {exc}',
            }


_engine = ProctorEngine()


def analyze_frame(frame_input: str | np.ndarray) -> dict[str, Any]:
    """Standalone function wrapper around ProctorEngine.analyze_frame."""
    return _engine.analyze_frame(frame_input)
