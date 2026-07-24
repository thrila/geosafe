import { useEffect, useRef, useState, useCallback } from "react";
import * as Cesium from "cesium";
import { Map, Upload, Navigation2, Camera } from "react-feather";
import { FlightMenuModal } from "./componets/FlightMenuModal";
import type { FlightMenuStatus } from "./componets/FlightMenuModal";
import { flightPath } from "./data/demo";
import type { FlightOption } from "./types/modal";
import { UploadForm as UploadDataForm } from "./componets/UploadForm";
import { useUploadForm } from "./hooks/useUploadform";
import { FlightResult } from "./componets/FlightResult";
import type { FlightResultStatus } from "./componets/FlightResult";
import type { FlightResultProps } from "./types/result";
import type { TelemetryItem } from "./types/data";
import type { TelemetryStatus } from "./types/data";
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
import { ImageUploadForm } from "./componets/ImageUploadForm";
import { ImageResult } from "./componets/ImageResult";
import { useImageUpload } from "./hooks/useImageUpload";

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<Cesium.CesiumWidget | null>(null);
  const flightVisualsRef = useRef<FlightVisuals | null>(null);

  // ── Modal open/close ──
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isResultsOpen, setIsResultsOpen] = useState(false);
  const [isFlightMenuOpen, setIsFlightMenuOpen] = useState(false);
  const [isImageOpen, setIsImageOpen] = useState(false);
  const [isImageResultOpen, setIsImageResultOpen] = useState(false);

  // ── Flight data state ──
  const [activeFlightId, setActiveFlightId] = useState<string | null>(null);
  const [flights, setFlights] = useState<FlightOption[]>([]);
  const [flightsStatus, setFlightsStatus] = useState<FlightMenuStatus>("loading");
  const [flightsError, setFlightsError] = useState("");

  const [flightResultData, setFlightResultData] = useState<FlightResultProps | null>(null);
  const [flightResultStatus, setFlightResultStatus] = useState<FlightResultStatus>("empty");
  const [flightResultError, setFlightResultError] = useState("");

  const [telemetryCards, setTelemetryCards] = useState<TelemetryItem[]>(demoTelemetryCards);
  const [telemetryStatus, setTelemetryStatus] = useState<TelemetryStatus>("empty");
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setShowWelcome(false), 5000);
    return () => clearTimeout(t);
  }, []);

  const hasData = flightResultData !== null;
  const hasFlights = flights.length > 0;

  // ── Image upload state ──
  const handleImageUploadSuccess = useCallback(() => {
    setIsImageOpen(false);
    setIsImageResultOpen(true);
  }, []);

  const imageUpload = useImageUpload(handleImageUploadSuccess);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageErrors, setImageErrors] = useState<{ imageFile?: string }>({});

  const handleImageSubmit = useCallback((file: File) => {
    setImageErrors({});
    imageUpload.classify(file);
  }, [imageUpload]);

  const handleImageReset = useCallback(() => {
    imageUpload.reset();
    setImageFile(null);
    setIsImageResultOpen(false);
    setIsImageOpen(true);
  }, [imageUpload]);

  // ── Flight upload success ──
  const handleUploadSuccess = useCallback((data: unknown) => {
    const res = data as {
      flight?: FlightOption;
      path?: { longitude: number; latitude: number; height?: number }[];
      telemetry?: { dateTime?: string; cards?: TelemetryItem[] };
      result?: FlightResultProps;
    } & Record<string, unknown>;

    if (res.result) {
      setFlightResultData(res.result);
      setFlightResultStatus("success");
      setFlightResultError("");
    } else {
      setFlightResultData(data as FlightResultProps);
      setFlightResultStatus("success");
      setFlightResultError("");
    }

    if (res.flight) {
      setFlights((prev) => [...prev, res.flight!]);
      setActiveFlightId(res.flight.id);
      setFlightsStatus("success");
    }

    if (res.telemetry?.cards) {
      setTelemetryCards(enrichTelemetryCards(res.telemetry.cards));
      setTelemetryStatus("success");
    }

    if (res.path?.length && widgetRef.current) {
      clearFlightVisuals(widgetRef.current, flightVisualsRef.current);
      flightVisualsRef.current = drawFlightVisuals(widgetRef.current, res.path, droneModelUrl);
    }
  }, []);

  // ── Flight select from menu ──
  const handleFlightSelect = useCallback(async (flight: FlightOption) => {
    setActiveFlightId(flight.id);
    setFlightResultStatus("loading");
    setFlightResultError("");
    setTelemetryStatus("loading");

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
        setFlightResultStatus("success");
      }
      if (data.telemetry?.cards) {
        setTelemetryCards(enrichTelemetryCards(data.telemetry.cards));
        setTelemetryStatus("success");
      }
      if (data.path?.length && widgetRef.current) {
        clearFlightVisuals(widgetRef.current, flightVisualsRef.current);
        flightVisualsRef.current = drawFlightVisuals(widgetRef.current, data.path, droneModelUrl);
      }
    } catch (e) {
      setFlightResultStatus("error");
      setFlightResultError(e instanceof Error ? e.message : "Failed to load flight data.");
      setTelemetryStatus("error");
    }
  }, []);

  const uploadForm = useUploadForm(handleUploadSuccess);

  // ── Cesium init ──
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

  // ── Fetch flights on mount ──
  useEffect(() => {
    ExternalEndpoints.getFlights()
      .then((data) => {
        if (Array.isArray(data)) {
          setFlights(data);
          setFlightsStatus(data.length > 0 ? "success" : "empty");
        } else {
          setFlightsStatus("empty");
        }
      })
      .catch((e) => {
        setFlightsStatus("error");
        setFlightsError(e instanceof Error ? e.message : "Failed to load flights.");
      });
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

      <TelemetryHud
        cards={telemetryCards}
        stopTime={telemetrySample.dateTime}
        startTime={telemetrySample.dateTime}
        status={telemetryStatus}
      />

      {/* ── Upload modal ── */}
      <Modal
        isOpen={isUploadOpen}
        title="Upload Flight Data"
        onClose={() => setIsUploadOpen(false)}
      >
        <UploadDataForm form={uploadForm} />
      </Modal>

      {/* ── Image classify modal ── */}
      <Modal
        isOpen={isImageOpen}
        title="Classify Image"
        onClose={() => setIsImageOpen(false)}
      >
        <ImageUploadForm
          imageFile={imageFile}
          setImageFile={setImageFile}
          status={imageUpload.status}
          errorMessage={imageUpload.errorMessage}
          onSubmit={handleImageSubmit}
          onCancel={imageUpload.cancel}
          onReset={handleImageReset}
          errors={imageErrors}
        />
      </Modal>

      {/* ── Image result modal ── */}
      <Modal
        isOpen={isImageResultOpen}
        title="Image Result"
        onClose={() => setIsImageResultOpen(false)}
      >
        <ImageResult
          status={imageUpload.status}
          result={imageUpload.result}
          previewUrl={imageUpload.previewUrl}
          errorMessage={imageUpload.errorMessage}
          onClassifyAnother={handleImageReset}
        />
      </Modal>

      {/* ── Trigger buttons ── */}
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
        className="image-trigger"
        onClick={() => {
          if (imageUpload.status === "success") {
            setIsImageResultOpen(true);
          } else {
            setIsImageOpen((c) => !c);
          }
        }}
        aria-label="Classify image"
      >
        <Camera size={ICON_SIZE} />
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
        aria-label="Flight results"
        onClick={() => setIsResultsOpen((current) => !current)}
      >
        <Navigation2 size={ICON_SIZE} />
      </button>

      {/* ── Flight results modal ── */}
      <Modal
        isOpen={isResultsOpen}
        title="Flight Results"
        onClose={() => setIsResultsOpen(false)}
      >
        <FlightResult
          {...(flightResultData ?? demoFlightResult)}
          status={flightResultStatus}
          errorMessage={flightResultError}
        />
      </Modal>

      {/* ── Flight menu modal ── */}
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
          status={flightsStatus}
          errorMessage={flightsError}
        />
      </Modal>

      {/* ── Welcome toast ── */}
      {showWelcome && (
        <div className="welcome-toast" role="status">
          <span className="welcome-toast-text">
            Detects diseases on cassava and plantain plants via aerial view
          </span>
        </div>
      )}
    </div>
  );
}
