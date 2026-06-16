from __future__ import annotations
from core.config import settings
import time
from pathlib import Path
import cv2



def is_blurry(frame, threshold: float = settings.BLUR_THRESHOLD):
    """Return True when a frame does not have enough sharpness."""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold, variance


def preprocess(frame, size: int = settings.IMAGE_SIZE):
    """Center-crop the frame to a square and resize it to 224x224."""

    h, w = frame.shape[:2]
    min_dim = min(h, w)
    top = (h - min_dim) // 2
    left = (w - min_dim) // 2
    cropped = frame[top : top + min_dim, left : left + min_dim]
    resized = cv2.resize(cropped, (size, size), interpolation=cv2.INTER_AREA)
    return resized


def extract_clear_frames(
    video_source: str | Path,
    output_dir: str | Path = settings.DEFAULT_OUTPUT_DIR,
    interval_seconds: float = settings.INTERVAL_SECONDS,
    blur_threshold: float = settings.BLUR_THRESHOLD,
    size: int = settings.IMAGE_SIZE,
) -> list[Path]:
    """Extract clear frames from a video at fixed intervals."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_source))
    if not cap.isOpened():
        raise ValueError(f"Could not open video source: {video_source}")

    saved_frames: list[Path] = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_step = max(1, int(round(fps * interval_seconds))) if fps and fps > 0 else None
    next_capture_ms = 0.0
    frame_index = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_step is not None:
                should_sample = frame_index % frame_step == 0
            else:
                current_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                should_sample = current_ms >= next_capture_ms

            if should_sample:
                blurry, _variance = is_blurry(frame, threshold=blur_threshold)
                if not blurry:
                    processed = preprocess(frame, size=size)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = output_path / f"frame_{timestamp}_{len(saved_frames):04d}.jpg"
                    if not cv2.imwrite(str(filename), processed):
                        raise IOError(f"Failed to write frame to {filename}")
                    saved_frames.append(filename)

                if frame_step is None:
                    next_capture_ms += interval_seconds * 1000

            frame_index += 1
    finally:
        cap.release()

    return saved_frames


def main(video_source: str | Path = settings.DEFAULT_VIDEO_SOURCE, output_dir: str | Path = settings.DEFAULT_OUTPUT_DIR) -> None:
    try:
        frames = extract_clear_frames(video_source, output_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return

    print(f"Saved {len(frames)} clear frame(s) to '{Path(output_dir)}'.")


if __name__ == "__main__":
    main()
