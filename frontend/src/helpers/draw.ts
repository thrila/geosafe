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
): { route: Cesium.Entity; direction: Cesium.Entity; start: Cesium.Entity; end: Cesium.Entity; drone: Cesium.Entity } {
  if (points.length === 0) {
    throw new Error("A flight path requires at least one location.");
  }

  const positions = points.map((p) =>
    Cesium.Cartesian3.fromDegrees(p.longitude, p.latitude, p.height ?? 14)
  );

  const route = widget.entities.add({
    polyline: {
      positions,
      width: 10,
      material: new Cesium.PolylineGlowMaterialProperty({
        glowPower: 0.18,
        color: Cesium.Color.fromCssColorString(color).withAlpha(0.72),
      }),
      clampToGround: false,
      arcType: Cesium.ArcType.GEODESIC,
    },
  });

  const direction = widget.entities.add({
    polyline: {
      positions,
      width: 3,
      material: new Cesium.PolylineArrowMaterialProperty(Cesium.Color.WHITE.withAlpha(0.9)),
      clampToGround: false,
      arcType: Cesium.ArcType.GEODESIC,
    },
  });

  const start = addFlightEndpoint(widget, points[0], "START", Cesium.Color.LIME);
  const end = addFlightEndpoint(widget, points.at(-1)!, "END", Cesium.Color.RED);
  const dronePoints = points.length > 1 ? points.slice(-2) : points;
  const drone = addDroneModel(widget, dronePoints, modelUrl);

  return { route, direction, start, end, drone };
}

function addFlightEndpoint(
  widget: Cesium.CesiumWidget,
  point: LonLatHeight,
  label: string,
  color: Cesium.Color,
): Cesium.Entity {
  return widget.entities.add({
    position: Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.height ?? 14),
    point: {
      color,
      pixelSize: 12,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: label,
      font: "600 12px JetBrains Mono",
      fillColor: color,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      pixelOffset: new Cesium.Cartesian2(0, -22),
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
    },
  });
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

  let orientation: Cesium.Quaternion | undefined;
  if (points.length > 1) {
    const next = Cesium.Cartesian3.fromDegrees(
      points[1].longitude,
      points[1].latitude,
      points[1].height ?? 14
    );
    const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
    const diff = Cesium.Cartesian3.subtract(next, origin, new Cesium.Cartesian3());
    const localDir = Cesium.Matrix4.multiplyByPointAsVector(
      Cesium.Matrix4.inverse(transform, new Cesium.Matrix4()),
      diff,
      new Cesium.Cartesian3()
    );
    const heading = Math.atan2(localDir.x, localDir.y);
    orientation = Cesium.Transforms.headingPitchRollQuaternion(
      origin, new Cesium.HeadingPitchRoll(heading, 0, 0)
    );
  }

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

export function addFlightBoundary(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  color = "#f59e0b",
  alpha = 0.12,
  paddingDeg = 0.0003
): Cesium.Entity {
  if (points.length < 2) return widget.entities.add({});

  const lats = points.map((p) => p.latitude);
  const lons = points.map((p) => p.longitude);
  const minLat = Math.min(...lats) - paddingDeg;
  const maxLat = Math.max(...lats) + paddingDeg;
  const minLon = Math.min(...lons) - paddingDeg;
  const maxLon = Math.max(...lons) + paddingDeg;

  return widget.entities.add({
    polygon: {
      hierarchy: [
        Cesium.Cartesian3.fromDegrees(minLon, minLat),
        Cesium.Cartesian3.fromDegrees(maxLon, minLat),
        Cesium.Cartesian3.fromDegrees(maxLon, maxLat),
        Cesium.Cartesian3.fromDegrees(minLon, maxLat),
      ],
      material: Cesium.Color.fromCssColorString(color).withAlpha(alpha),
      outline: true,
      outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.4),
      outlineWidth: 2,
      height: 0,
    },
  });
}

export type FlightVisuals = {
  route: Cesium.Entity;
  direction: Cesium.Entity;
  start: Cesium.Entity;
  end: Cesium.Entity;
  drone: Cesium.Entity;
};

export function drawFlightVisuals(
  widget: Cesium.CesiumWidget,
  points: LonLatHeight[],
  modelUrl: string
): FlightVisuals {
  return addDronePath(widget, points, modelUrl);
}

export function focusFlight(widget: Cesium.CesiumWidget, points: LonLatHeight[]) {
  if (points.length === 0) return;
  const positions = points.map((point) =>
    Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.height ?? 14)
  );
  const bounds = Cesium.BoundingSphere.fromPoints(positions);
  widget.camera.flyToBoundingSphere(bounds, {
    duration: 1.4,
    offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-48), Math.max(bounds.radius * 3, 180)),
  });
}

export function clearFlightVisuals(
  widget: Cesium.CesiumWidget,
  visuals: FlightVisuals | null
) {
  if (!visuals) return;
  widget.entities.remove(visuals.route);
  widget.entities.remove(visuals.direction);
  widget.entities.remove(visuals.start);
  widget.entities.remove(visuals.end);
  widget.entities.remove(visuals.drone);
}
