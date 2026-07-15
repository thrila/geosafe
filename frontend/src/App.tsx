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
import { addDronePath, drawFlightVisuals, clearFlightVisuals } from "./helpers/draw";
import type { FlightVisuals } from "./helpers/draw";
import droneModelUrl from "./models/drone.glb?url";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import "./App.css";
import { TelemetryHud } from "./componets/telementryHud";
import { telemetryCards as demoTelemetryCards, telemetrySample, enrichTelemetryCards } from "./data/telementary";
import { Modal } from "./componets/Modal";
import { ICON_SIZE } from "./data/telementary";
import { demoFlightResult } from "./data/demoData";
import { ExternalEndpoints } from "./service/api";

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<Cesium.CesiumWidget | null>(null);
  const flightVisualsRef = useRef<FlightVisuals | null>(null);
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
      path?: { longitude: number; latitude: number; height?: number }[];
      telemetry?: { dateTime?: string; cards?: TelemetryItem[] };
      result?: FlightResultProps;
    } & Record<string, unknown>;
    if (res.result) {
      setFlightResultData(res.result);
    } else {
      setFlightResultData(data as FlightResultProps);
    }
    if (res.flight) {
      setFlights((prev) => [...prev, res.flight!]);
      setActiveFlightId(res.flight.id);
    }
    if (res.telemetry?.cards) {
      setTelemetryCards(enrichTelemetryCards(res.telemetry.cards));
    }
    if (res.path?.length && widgetRef.current) {
      clearFlightVisuals(widgetRef.current, flightVisualsRef.current);
      flightVisualsRef.current = drawFlightVisuals(widgetRef.current, res.path, droneModelUrl);
    }
  }, []);

  const handleFlightSelect = useCallback(async (flight: FlightOption) => {
    setActiveFlightId(flight.id);
    const [lat, lon] = flight.location.split(",").map((s) => parseFloat(s.trim()));
    if (!isNaN(lat) && !isNaN(lon)) {
      widgetRef.current?.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 500),
      });
    }

    try {
      const data = await ExternalEndpoints.getFlight(flight.id);
      if (data.result) {
        setFlightResultData(data.result);
      }
      if (data.telemetry?.cards) {
        setTelemetryCards(enrichTelemetryCards(data.telemetry.cards));
      }
      if (data.path?.length && widgetRef.current) {
        clearFlightVisuals(widgetRef.current, flightVisualsRef.current);
        flightVisualsRef.current = drawFlightVisuals(widgetRef.current, data.path, droneModelUrl);
      }
    } catch {
      // silently fail — map still flies to location
    }
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

  useEffect(() => {
    ExternalEndpoints.getFlights()
      .then((data) => {
        if (Array.isArray(data)) {
          setFlights(data);
        }
      })
      .catch(() => {});
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
