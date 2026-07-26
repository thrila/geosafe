def build_slides(per_frame: list[dict]) -> list[dict]:
    """Extract diseased frames into slide dicts with kind/src/caption."""
    slides = []
    for f in per_frame:
        url = f.get("image_url")
        if url:
            disease = f.get("prediction", {}).get("disease", "Unknown")
            slides.append({
                "kind": "image",
                "src": url,
                "caption": f"Frame {f.get('frame', 0)} — {disease}",
            })
    return slides
