import pandas as pd
import folium

# 1. Load your CSV file
df = pd.read_csv('./flight_raw_records/FlightRecord_2026-04-28_[18-43-18].txt')  # <-- Change this to your actual file name

# 2. Clean up the data (remove the placeholder 1970 row and bad GPS)
df = df[df['dateTime'] != '1970-01-01T00:00:00Z']  # Remove placeholder
df = df[df['latitude'] != 0]                       # Remove zeros before GPS lock
df = df.dropna(subset=['latitude', 'longitude'])   # Remove any missing coordinates

# 3. Create the map centered on the average flight position
center_lat = df['latitude'].mean()
center_lon = df['longitude'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=17, tiles='OpenStreetMap')

# 4. Draw the full flight path as a red line
points = list(zip(df['latitude'], df['longitude']))
folium.PolyLine(points, color='red', weight=3, opacity=0.8, tooltip='Flight Path').add_to(m)

# 5. Add clickable markers every 10 rows (to avoid overcrowding)
#    Change the step size: step=1 for every point, step=20 for fewer points.
step_size = 10  
for i in range(0, len(df), step_size):
    row = df.iloc[i]
    
    # Build a detailed popup with ALL the telemetry you want
    popup_html = f"""
    <div style="font-family: Arial; font-size: 12px; width: 250px;">
        <b>🕒 Time:</b> {row['dateTime']}<br>
        <b>📍 Altitude (MSL):</b> {row['altitude']:.2f} m<br>
        <b>📏 Height (AGL):</b> {row['height']:.2f} m<br>
        <hr>
        <b>➡️ X-Speed:</b> {row['xSpeed']:.2f} m/s<br>
        <b>⬆️ Y-Speed:</b> {row['ySpeed']:.2f} m/s<br>
        <b>↕️ Z-Speed:</b> {row['zSpeed']:.2f} m/s<br>
        <hr>
        <b>📷 Gimbal Pitch:</b> {row['gimbalPitch']:.1f}°<br>
        <b>📷 Gimbal Roll:</b> {row['gimbalRoll']:.1f}°<br>
        <b>📷 Gimbal Yaw:</b> {row['gimbalYaw']:.1f}°<br>
        <hr>
        <b>🔋 Battery Level:</b> {row['batteryLevel']}%<br>
        <b>⚡ Battery Voltage:</b> {row['batteryVoltage']:.2f} V<br>
        <b>🔄 Pitch:</b> {row['pitch']:.1f}°<br>
        <b>🔄 Roll:</b> {row['roll']:.1f}°<br>
        <b>🧭 Yaw:</b> {row['yaw']:.1f}°<br>
    </div>
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3,                     # Size of the dot
        color='blue',
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Time: {row['dateTime']}"  # Shows when you hover
    ).add_to(m)

# 6. Save the map to an HTML file
m.save('flight_path_with_telemetry.html')
print("✅ Map saved! Open 'flight_path_with_telemetry.html' in your browser.")
