from services.slides import build_slides


def test_slides_use_one_annotated_source_frame_per_affected_frame():
    slides = build_slides([
        {
            "frame": 7,
            "image_url": "/api/v1/images/run/evidence_f000007.jpg",
            "prediction": {"disease": "CMD"},
        },
        {
            "frame": 7,
            "image_url": "/api/v1/images/run/evidence_f000007.jpg",
            "prediction": {"disease": "CMD"},
        },
    ])

    assert slides == [{
        "kind": "image",
        "src": "/api/v1/images/run/evidence_f000007.jpg",
        "caption": "Frame 7 — affected tile heatmap (CMD)",
    }]
