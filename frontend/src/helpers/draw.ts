import * as Cesium from "cesium";
import type { LonLatHeight } from "../types/location";


export function addPolyline(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  color = "#38bdf8",
  width = 4
): Cesium.Entity {
  return widget.entities.add({
    polyline: {
      positions: points.map((p) =>
        Cesium.Cartesian3.fromDegrees(p.longitude, p.latitude, p.height ?? 14)
      ),
      width,
      material: Cesium.Color.fromCssColorString(color),
      clampToGround: false,
      arcType: Cesium.ArcType.GEODESIC,
    },
  });
}

export function addHeatmap(
  widget: Cesium.CesiumWidget,
  data: { longitude: number; latitude: number; value: number }[],
  radiusPx = 28
): Cesium.PointPrimitiveCollection {
  const collection = new Cesium.PointPrimitiveCollection();

  data.forEach((d) => {
    const t = Math.max(0, Math.min(1, d.value));
    const r = Math.round(255 * t);
    const g = Math.round(255 * (1 - t));
    const b = 0;

    collection.add({
      position: Cesium.Cartesian3.fromDegrees(d.longitude, d.latitude, 0),
      color: Cesium.Color.fromBytes(r, g, b, 180),
      pixelSize: radiusPx * (0.4 + t * 0.6),
      outlineColor: Cesium.Color.fromBytes(r, g, b, 60),
      outlineWidth: 1,
    });
  });

  widget.scene.primitives.add(collection);
  return collection;
}

export function addPolygon(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  color = "#ef4444",
  alpha = 0.3
): Cesium.Entity {
  return widget.entities.add({
    polygon: {
      hierarchy: points.map((p) =>
        Cesium.Cartesian3.fromDegrees(p.longitude, p.latitude, p.height ?? 0)
      ),
      material: Cesium.Color.fromCssColorString(color).withAlpha(alpha),
      outline: true,
      outlineColor: Cesium.Color.fromCssColorString(color),
      outlineWidth: 2,
      height: 0,
    },
  });
}

export function addEllipse(
  widget: Cesium.CesiumWidget,
  longitude: number,
  latitude: number,
  radiusM: number,
  color = "#ef4444",
  alpha = 0.35
): Cesium.Entity {
  return widget.entities.add({
    position: Cesium.Cartesian3.fromDegrees(longitude, latitude),
    ellipse: {
      semiMajorAxis: radiusM,
      semiMinorAxis: radiusM,
      material: Cesium.Color.fromCssColorString(color).withAlpha(alpha),
      height: 0,
    },
  });
}

export function addFlightPoints(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[]
): Cesium.PointPrimitiveCollection {
  const collection = new Cesium.PointPrimitiveCollection();
  const last = points.length - 1;

  points.forEach((point, i) => {
    const isEndpoint = i === 0 || i === last;
    collection.add({
      position: Cesium.Cartesian3.fromDegrees(
        point.longitude,
        point.latitude,
        point.height ?? 0
      ),
      color: isEndpoint
        ? Cesium.Color.WHITE
        : Cesium.Color.fromCssColorString("#7dd3fc"),
      outlineColor: Cesium.Color.fromCssColorString("#0f172a"),
      outlineWidth: 2,
      pixelSize: isEndpoint ? 9 : 7,
    });
  });

  widget.scene.primitives.add(collection);
  return collection;
}


export function addDronePath(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  modelUrl: string,
  color = "#38bdf8",
  width = 3                        // slimmer line
): { path: Cesium.Entity; start: Cesium.Entity; end: Cesium.Entity } {
  const positions = points.map((p) =>
    Cesium.Cartesian3.fromDegrees(p.longitude, p.latitude, p.height ?? 14)
  );

  const path = widget.entities.add({
    polyline: {
      positions,
      width,
      material: Cesium.Color.fromCssColorString(color),
      clampToGround: false,
    },
  });

  const start = addDroneModel(widget, points, modelUrl);
  const end = addDroneModel(widget, [...points].reverse(), modelUrl);

  return { path, start, end };
}

export function addDroneModel(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  modelUrl: string,
  scale = 10.0
): Cesium.Entity {
  const origin = Cesium.Cartesian3.fromDegrees(
    points[0].longitude,
    points[0].latitude,
    points[0].height ?? 14
  );

  const next = Cesium.Cartesian3.fromDegrees(
    points[1].longitude,
    points[1].latitude,
    points[1].height ?? 14
  );

  // Get heading from origin toward next point
  const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
  const diff = Cesium.Cartesian3.subtract(next, origin, new Cesium.Cartesian3());
  const localDir = Cesium.Matrix4.multiplyByPointAsVector(
    Cesium.Matrix4.inverse(transform, new Cesium.Matrix4()),
    diff,
    new Cesium.Cartesian3()
  );

  const heading = Math.atan2(localDir.x, localDir.y); // east/north in local frame

  const hpr = new Cesium.HeadingPitchRoll(heading, 0, 0);
  const orientation = Cesium.Transforms.headingPitchRollQuaternion(origin, hpr);

  return widget.entities.add({
    position: origin,
    orientation,
    model: {
      uri: modelUrl,
      scale,
      minimumPixelSize: 32,
      maximumScale: 200,
    },
  });
}
