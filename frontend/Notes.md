# Notes — DJI Drone Map UI
-[X] Use Icons
-[X] Time should be a range
-[X] Fix on hover
-[X] Make the items render in the center.
-[] Make responsive
-[] Make data Pipelines work 
-[] Fix the upload button not working when i type text

## Planned Features

### Flight Picker Menu
- A modal listing all previously uploaded flights, triggered by a toolbar button and `Ctrl + K`.
- Each entry shows: flight name, date, duration.
- Clicking a flight closes the menu and flies the Cesium camera to that flight's bounding
  box, then plots the path.

### Click-to-Focus on Flight Path
- Clicking a flight in the picker (or clicking a polyline directly on the globe) should
  animate the Cesium camera to frame that flight's full path.
- The selected path renders at full opacity; all other paths dim to ~45% opacity.

### Per-Flight Colour Coding
- Each flight path polyline gets a distinct colour drawn from a fixed palette, assigned by
  index and cycling if there are more flights than colours.
- No two currently-visible flights should share the same colour.
- A thin white glow is layered under each polyline for contrast against dark terrain.

### Disease Heatmaps
- Overlay a heatmap on the globe for areas where crop disease has been detected.
- Intensity of the heatmap corresponds to severity / density of detections.
- Heatmap should be toggleable (on/off) independently of flight paths.
- Colour scale: green (low) → yellow (moderate) → red (high severity).

---

## Backlog / Unscoped

- Drone image carousel inside the flight viewer modal (images served from backend).
- Filter flights by date range in the picker.
- Export flight path as KML / GeoJSON.
