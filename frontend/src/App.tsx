import { useEffect, useRef, useState, useCallback } from "react";
import * as Cesium from "cesium";
import { Map, Upload, Navigation2 } from "react-feather";
import { FlightMenuModal } from "./componets/FlightMenuModal";
import { flightPath } from "./data/demo";
import type { FlightOption } from "./types/modal";
import { UploadForm as UploadDataForm } from "./componets/UploadForm";
import { useUploadForm } from "./hooks/useUploadform";
import { FlightResult } from "./componets/FlightResult";
import type { FlightResultProps } from "./types/result";
import type { TelemetryItem } from "./types/data";
import { addDronePath, addPolygon, addHeatmap } from "./helpers/draw";
import { heatmapArea, heatmapData } from "./data/demo";
import droneModelUrl from "./models/drone.glb?url";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import "./App.css";
import { TelemetryHud } from "./componets/telementryHud";
import { telemetryCards as demoTelemetryCards, telemetrySample } from "./data/telementary";
import { Modal } from "./componets/Modal";
import { ICON_SIZE } from "./data/telementary";
import { demoFlightResult } from "./data/demoData";

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<Cesium.CesiumWidget | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isResultsOpen, setIsResultsOpen] = useState(false);
  const [isFlightMenuOpen, setIsFlightMenuOpen] = useState(false);
  const [activeFlightId, setActiveFlightId] = useState<string | null>(null);
  const [flights, setFlights] = useState<FlightOption[]>([]);
  const [flightResultData, setFlightResultData] = useState<FlightResultProps | null>(null);
  const [telemetryCards, setTelemetryCards] = useState<TelemetryItem[]>(demoTelemetryCards);
  const hasData = flightResultData !== null;
  const hasFlights = flights.length > 0;

  const handleUploadSuccess = useCallback((data: unknown) => {
    const res = data as {
      flight?: FlightOption;
      telemetry?: { dateTime?: string; cards?: TelemetryItem[] };
    } & Record<string, unknown>;
    setFlightResultData(data as FlightResultProps);
    if (res.flight) {
      setFlights((prev) => [...prev, res.flight!]);
      setActiveFlightId(res.flight.id);
    }
    if (res.telemetry?.cards) {
      setTelemetryCards(res.telemetry.cards);
    }
  }, []);

  const handleFlightSelect = useCallback((flight: FlightOption) => {
    setActiveFlightId(flight.id);
    widgetRef.current?.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        flight.longitude,
        flight.latitude,
        500,
      ),
    });
  }, []);

  const uploadForm = useUploadForm(handleUploadSuccess);

  useEffect(() => {
    if (!containerRef.current) return;

    const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN;
    if (ionToken) {
      Cesium.Ion.defaultAccessToken = ionToken;
    }

    const widget = new Cesium.CesiumWidget(containerRef.current, {
      baseLayer: Cesium.ImageryLayer.fromWorldImagery(
        { style: Cesium.IonWorldImageryStyle.AERIAL_WITH_LABELS } as unknown as Cesium.ImageryLayer.WorldImageryConstructorOptions
      ),
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      targetFrameRate: 30,
    });

    widgetRef.current = widget;

    addDronePath(widget, flightPath, droneModelUrl);
    addPolygon(widget, heatmapArea, "#f59e0b", 0.15);
    addHeatmap(widget, heatmapData);

    widget.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(0, 20, 22000000),
    });

    let cancelled = false;
    const defaultZoomTimer = window.setTimeout(() => {
      if (cancelled) return;

      widget.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          flightPath[0].longitude,
          flightPath[0].latitude,
          flightPath[0].height,
        ),
      });
    }, 12000);

    return () => {
      cancelled = true;
      window.clearTimeout(defaultZoomTimer);
      widget.destroy();
      widgetRef.current = null;
    };
  }, []);

  useKeyboardShortcuts([
    {
      key: "k",
      modifiers: ["ctrlOrMeta"],
      action: () => setIsFlightMenuOpen((c) => !c),
    },
    {
      key: "Escape",
      action: () => setIsFlightMenuOpen(false),
    },
  ]);


  return (
    <div className="app-shell">
      <div ref={containerRef} className="map-shell" />

      <TelemetryHud cards={telemetryCards} stopTime={telemetrySample.dateTime} startTime={telemetrySample.dateTime} />
      {/*NOTE: The first modal for the upload*/}
      <Modal
        isOpen={isUploadOpen}
        title="Upload Flight Data"
        onClose={() => setIsUploadOpen(false)}
      >
        <UploadDataForm
          form={uploadForm}
        />
      </Modal>

      <button
        type="button"
        className="upload-trigger"
        onClick={() => setIsUploadOpen((current) => !current)}
        aria-label="Upload"
      >
        <Upload size={ICON_SIZE} />
      </button>

      <button
        type="button"
        className={`flights-trigger${hasFlights ? "" : " flights-trigger--empty"}`}
        aria-label="Locations"
        onClick={() => setIsFlightMenuOpen((current) => !current)}
      >
        <Map size={ICON_SIZE} />
      </button>


      <button
        type="button"
        className={`results-trigger${hasData ? "" : " results-trigger--empty"}`}
        aria-label="Previous Locations"
        onClick={() => setIsResultsOpen((current) => !current)}
      >
        <Navigation2 size={ICON_SIZE} />
      </button>

      <Modal
        isOpen={isResultsOpen}
        title="Flight Results"
        onClose={() => setIsResultsOpen(false)}
      >
        <FlightResult
          {...(flightResultData ?? demoFlightResult)}
          isLoading={!hasData}
        />
      </Modal>


      <Modal
        isOpen={isFlightMenuOpen}
        title="Previous Flights"
        onClose={() => setIsFlightMenuOpen(false)}
      >
        <FlightMenuModal
          onClose={() => setIsFlightMenuOpen(false)}
          activeFlightId={activeFlightId}
          onSelect={handleFlightSelect}
          flights={flights}
          isLoading={!hasFlights}
        />
      </Modal>

    </div>
  );
}
