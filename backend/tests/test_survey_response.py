from pathlib import Path
from types import SimpleNamespace

import pytest

from services.survey_response import build_survey_response


def _summary_for(diseases: list[str]) -> dict:
    telemetry = SimpleNamespace(
        route_distance_km=0, max_speed=0, max_height=0, battery_drained=0,
        max_battery_temp=0, avg_gps=0,
    )
    rows = [
        {
            "frame": i,
            "tile": 0,
            "prediction": {
                "plant_type": "not detected" if disease == "not detected" else "cassava",
                "disease": disease,
                "disease_confidence": 0.8,
            },
        }
        for i, disease in enumerate(diseases)
    ]
    response = build_survey_response(
        video_result={"per_frame_results": rows},
        name="Field",
        flight_id=1,
        artifact_id="run-1",
        flight_info={},
        telemetry=telemetry,
        telemetry_rows=[],
        pipeline_config=None,
    )
    return response["summary"], response["observations"]


@pytest.mark.parametrize(
    ("diseases", "conclusion"),
    [
        (["Healthy", "Healthy"], "healthy"),
        (["Healthy", "not detected"], "healthy"),
        (["Healthy", "Cassava mosaic disease"], "findings"),
        (["Inconclusive", "Cassava mosaic disease"], "findings"),
        (["Healthy", "Inconclusive"], "inconclusive"),
        (["Inconclusive"], "inconclusive"),
        (["not detected"], "inconclusive"),
    ],
)
def test_survey_is_only_healthy_when_assessed_tiles_all_agree(diseases, conclusion):
    summary, _ = _summary_for(diseases)

    assert summary["conclusion"] == conclusion


def test_survey_counts_how_each_tile_was_assessed():
    summary, observations = _summary_for(
        ["Healthy", "Inconclusive", "not detected", "not detected", "Cassava mosaic disease"]
    )

    assert summary["tileAssessment"] == {
        "affected": 1, "healthy": 1, "inconclusive": 1, "unrecognized": 2,
    }
    assert len(observations) == 1
    assert observations[0]["condition"]["name"] == "Cassava mosaic disease"
    assert summary["conditions"][0]["observationCount"] == 1


def test_survey_warns_about_tiles_it_could_not_assess():
    summary, _ = _summary_for(["Healthy", "Inconclusive", "not detected"])

    warnings = summary["dataQuality"]["warnings"]
    assert "1 tiles could not be assessed, so problems there may be missed." in warnings
    assert "1 tiles showed no recognized crop and were not assessed." in warnings


def test_survey_response_exposes_reviewable_findings_without_claiming_plant_gps(tmp_path: Path):
    pipeline_config = SimpleNamespace(
        plant_onnx_path=tmp_path / "plant.onnx",
        disease_onnx_path=lambda plant: tmp_path / f"{plant}.onnx",
        fps=2.0,
    )
    telemetry = SimpleNamespace(
        track_pts=[{"latitude": 4.8, "longitude": 6.3, "height": 40}],
        route_distance_km=1.25,
        max_speed=8.0,
        max_height=45.0,
        battery_drained=10.0,
        max_battery_temp=39.0,
        avg_gps=13,
    )
    response = build_survey_response(
        video_result={
            "frames_rejected": 1,
            "per_frame_results": [{
                "frame": 4,
                "tile": 2,
                "timestamp": 2.0,
                "prediction": {
                    "plant_type": "cassava",
                    "plant_confidence": 0.93,
                    "disease": "Cassava mosaic disease",
                    "disease_confidence": 0.84,
                    "all_probabilities": {
                        "Cassava mosaic disease": 0.84,
                        "Healthy": 0.16,
                    },
                },
                "tile_region": {
                    "x": 640, "y": 0, "width": 640, "height": 640,
                    "imageWidth": 1920, "imageHeight": 1080,
                },
                "image_url": "/api/v1/images/run/evidence_f000004.jpg",
            }],
        },
        name="North field",
        flight_id=8,
        artifact_id="run-1",
        flight_info={"id": 8, "name": "North field", "start_ts": 1_800_000_000_000, "end_ts": 1_800_000_010_000},
        telemetry=telemetry,
        telemetry_rows=[{
            "ts": 1_800_000_000_000,
            "latitude": 4.8,
            "longitude": 6.3,
            "height": 40,
            "altitude": 42,
            "yaw": 90,
            "gimbal_pitch": -90,
            "gimbal_roll": 0,
            "gimbal_yaw": 0,
        }],
        pipeline_config=pipeline_config,
    )

    finding = response["observations"][0]
    assert response["schemaVersion"] == "1.0"
    assert response["summary"]["observationCounts"]["unit"] == "tile_frame_observation"
    assert response["summary"]["coverage"]["tilesAnalyzed"] == 1
    assert response["summary"]["coverage"]["framesSampled"] == 2
    assert finding["condition"]["confidenceMeaning"] == "model_score"
    assert finding["location"]["latitude"] is None
    assert finding["location"]["method"] == "unavailable"
    assert finding["evidence"]["region"]["x"] == 640
    assert response["flight"]["track"]["samples"][0]["yawDegrees"] == 90
    assert "routeDistanceMeters" not in response["summary"]["coverage"]
    assert "trackSamples" not in response["flight"]
