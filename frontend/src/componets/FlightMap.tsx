import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { flightPath } from "../data/demo";
import {
  addDronePath,
  clearFlightVisuals,
  drawFlightVisuals,
  focusFlight,
  type FlightVisuals,
} from "../helpers/draw";
import droneModelUrl from "../models/drone.glb?url";
import type { LonLatHeight } from "../types/location";

export type FlightMapHandle = {
  showFlight: (path: LonLatHeight[]) => void;
  focusLocation: (latitude: number, longitude: number) => void;
};

const FlightMap = forwardRef<FlightMapHandle>(function FlightMap(_, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<Cesium.CesiumWidget | null>(null);
  const visualsRef = useRef<FlightVisuals | null>(null);

  useImperativeHandle(ref, () => ({
    showFlight(path) {
      const widget = widgetRef.current;
      if (!widget || path.length === 0) return;
      clearFlightVisuals(widget, visualsRef.current);
      visualsRef.current = drawFlightVisuals(widget, path, droneModelUrl);
      focusFlight(widget, path);
    },
    focusLocation(latitude, longitude) {
      widgetRef.current?.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, 500),
      });
    },
  }), []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN;
    if (ionToken) Cesium.Ion.defaultAccessToken = ionToken;

    const widget = new Cesium.CesiumWidget(container, {
      baseLayer: Cesium.ImageryLayer.fromWorldImagery(
        { style: Cesium.IonWorldImageryStyle.AERIAL_WITH_LABELS } as unknown as Cesium.ImageryLayer.WorldImageryConstructorOptions,
      ),
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      targetFrameRate: 30,
    });
    widgetRef.current = widget;
    visualsRef.current = addDronePath(widget, flightPath, droneModelUrl);
    widget.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(0, 20, 22000000),
    });

    const defaultZoomTimer = window.setTimeout(() => {
      widget.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          flightPath[0].longitude,
          flightPath[0].latitude,
          flightPath[0].height,
        ),
      });
    }, 12000);

    return () => {
      window.clearTimeout(defaultZoomTimer);
      widget.destroy();
      widgetRef.current = null;
      visualsRef.current = null;
    };
  }, []);

  return <div ref={containerRef} className="map-shell" />;
});

export default FlightMap;
