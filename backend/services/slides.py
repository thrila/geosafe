def build_slides(per_frame: list[dict]) -> list[dict]:
    """Return one annotated full-frame slide for each affected source frame."""
    slides = []
    seen_urls = set()
    for f in per_frame:
        url = f.get("image_url")
        disease = f.get("prediction", {}).get("disease", "Unknown")
        if (
            url
            and url not in seen_urls
            and disease.lower() not in ("not detected", "healthy")
        ):
            seen_urls.add(url)
            slides.append({
                "kind": "image",
                "src": url,
                "caption": f"Frame {f.get('frame', 0)} — affected tile heatmap ({disease})",
            })
    return slides
