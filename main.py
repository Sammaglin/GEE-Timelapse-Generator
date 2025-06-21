Stoic Otaku, [6/21/2025 10:05 PM]
 # File: gee_timelapse_web.py
# Run: http://127.0.0.1:5000
#http://192.168.1.5:5000 - lan share
 
import ee
import folium
from folium.plugins import Draw
from flask import Flask, render_template_string, request
from datetime import datetime
import os
import imageio
import tempfile
from PIL import Image
import requests
import shutil
import json
 
# Initialize Earth Engine
try:
    ee.Initialize(project='ee-sammaglin1971')
except Exception:
    # If not authenticated, start login
    ee.Authenticate()
    ee.Initialize()
 
app = Flask(name)
 
#Browser format
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GEE Timelapse Generator</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
   
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <!-- Leaflet Draw CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css" />
    <!-- Flatpickr -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"> (https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css%22>)
 
    <style>
        #map { height: 500px; }
        body { font-family: sans-serif; padding: 20px; }
    </style>
</head>
<body>
    <h2>GEE Timelapse Generator</h2>
    <form method="POST" onsubmit="showProgressBar()">
        <label>Select Date Range:</label><br>
        <input type="text" id="date_range" name="date_range" placeholder="YYYY-MM-DD to YYYY-MM-DD" required><br><br>
 
        <label>Imagery Type:</label><br>
        <select name="image_type">
            <option>True Color</option>
            <option>NDVI</option>
        </select><br><br>
 
        <label>Output Format:</label><br>
        <select name="format">
            <option>GIF</option>
            <option>MP4</option>
        </select><br><br>
 
        <label>Output File Name:</label><br>
        <input type="text" name="filename" value="timelapse_output"><br><br>
 
        <input type="hidden" name="drawn_geojson" id="drawn_geojson">
        <input type="submit" value="Generate Timelapse">
    </form>
 
    <div id="progressBarContainer" style="display:none;">
        <p>Generating timelapse... Please wait.</p>
        <progress id="progressBar" value="0" max="100" style="width:100%"></progress>
    </div>
 
    {% if message %}<p><strong>{{ message }}</strong></p>{% endif %}
    {% if download_link %}
        <a href="{{ download_link }}" download>Download Output</a>
    {% endif %}
 
    <div id="map"></div>
 
    <!-- Scripts -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
 
    <script>
        // Flatpickr for date range
        flatpickr("#date_range", { mode: "range", dateFormat: "Y-m-d" });
 
        // Leaflet map setup
        var map = L.map('map').setView([12.9716, 77.5946], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
 
        // Draw control
        var drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        var drawControl = new L.Control.Draw({
            edit: { featureGroup: drawnItems },
            draw: {
                polygon: true,
                polyline: false,
                rectangle: false,
                circle: false,
                marker: false,
                circlemarker: false
            }
        });
        map.addControl(drawControl);
 
        map.on(L.Draw.Event.CREATED, function (e) {
            drawnItems.clearLayers();
            var layer = e.layer;
            drawnItems.addLayer(layer);

Stoic Otaku, [6/21/2025 10:05 PM]
            var geojson = layer.toGeoJSON();
            document.getElementById('drawn_geojson').value = JSON.stringify(geojson);
        });
 
        function showProgressBar() {
            document.getElementById('progressBarContainer').style.display = 'block';
            let progress = document.getElementById('progressBar');
            let count = 0;
            let interval = setInterval(() => {
                count = Math.min(count + 5, 95);
                progress.value = count;
                if (count >= 95) clearInterval(interval);
            }, 500);
        }
    </script>
</body>
</html>
"""
# --- helper functions ---
def get_composite_image(aoi, start_date, end_date, image_type):
    def maskL8sr(image):
        cloudShadowBitMask = (1 << 3)
        cloudsBitMask = (1 << 5)
        qa = image.select('QA_PIXEL')
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(
               qa.bitwiseAnd(cloudsBitMask).eq(0))
        return image.updateMask(mask)
 
    if image_type == "True Color":
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .map(maskL8sr)
 
        image = collection.median()
        vis = {
            "bands": ["SR_B4", "SR_B3", "SR_B2"],
            "min": 0,
            "max": 30000,
            "gamma": 1.2
        }
        return image, vis
 
    elif image_type == "NDVI":
        def addNDVI(image):
            ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
            return image.addBands(ndvi)
 
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .map(maskL8sr) \
            .map(addNDVI)
 
        image = collection.median().select("NDVI")
        vis = {
    "min": -0.2,
    "max": 0.8,
    "palette": [
        'FFFFFF',  # white (no data / low NDVI)
        'CE7E45',  # brown
        'DF923D',  # tan
        'F1B555',  # yellow
        'FCD163',  # light yellow
        '99B718',  # light green
        '74A901',  # green
        '66A000',  # darker green
        '529400',  # even darker
        '3E8601',  # deep green
        '207401',  # very dense vegetation
        '056201',  # almost black-green
        '004C00',  # darker
        '023B01',  # nearly black
        '012E01'   # very dense
        ]
    }
        return image, vis
 
    else:
        raise ValueError("Unsupported imagery type")
 
 
def generate_frames(aoi, start_date, end_date, image_type, temp_dir):
    frames = []
    start_year = datetime.strptime(start_date, "%Y-%m-%d").year
    end_year = datetime.strptime(end_date, "%Y-%m-%d").year
    for year in range(start_year, end_year + 1):
        try:
            y_start = f"{year}-01-01"
            y_end = f"{year}-12-31"
            img, vis = get_composite_image(aoi, y_start, y_end, image_type)
            path = os.path.join(temp_dir, f"frame_{year}.png")
 
            thumb_url = img.getThumbURL({
                "region": aoi,
                "dimensions": 512,
                **vis
            })
 
            response = requests.get(thumb_url)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                frames.append(path)
            else:
                print(f"Thumbnail error {year}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Failed {year}: {str(e)}")
    return frames
 
def create_timelapse(frames, output_path, format):
    images = [Image.open(f) for f in frames]
    if format == "GIF":
        images[0].save(output_path, save_all=True, append_images=images[1:], duration=500, loop=0)

Stoic Otaku, [6/21/2025 10:05 PM]
    elif format == "MP4":
        imageio.mimsave(output_path, images, fps=2)
    return output_path
 
# --- Flask route ---
@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    download_link = ""
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=6)
    Draw(export=True).add_to(m)
 
    if request.method == 'POST':
        drawn_geojson = request.form.get("drawn_geojson", "")
        if not drawn_geojson:
            message = "Please draw a region on the map."
            return render_template_string(HTML_TEMPLATE, folium_map=m._repr_html_(), message=message)
 
        try:
            geojson_obj = json.loads(drawn_geojson)
            geom_type = geojson_obj['geometry']['type']
            coords = geojson_obj['geometry']['coordinates']
 
            if geom_type == 'Polygon':
                aoi = ee.Geometry.Polygon(coords)
            elif geom_type == 'MultiPolygon':
                aoi = ee.Geometry.MultiPolygon(coords)
            elif geom_type == 'Point':
                aoi = ee.Geometry.Point(coords).buffer(1000).bounds()
            elif geom_type == 'LineString':
                aoi = ee.Geometry.LineString(coords).buffer(1000).bounds()
            else:
                message = f"Unsupported geometry type: {geom_type}"
                return render_template_string(HTML_TEMPLATE, folium_map=m._repr_html_(), message=message)
 
        except Exception as e:
            message = f"Failed to parse geometry: {str(e)}"
            return render_template_string(HTML_TEMPLATE, folium_map=m._repr_html_(), message=message)
 
        try:
            date_range = request.form['date_range'].split(' to ')
            if len(date_range) != 2:
                raise ValueError("Invalid date range format.")
            start_date, end_date = date_range
        except Exception as e:
            message = f"Invalid date range: {str(e)}"
            return render_template_string(HTML_TEMPLATE, folium_map=m._repr_html_(), message=message)
 
        image_type = request.form['image_type']
        out_format = request.form['format']
        filename = request.form['filename']
 
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = generate_frames(aoi, start_date, end_date, image_type, tmpdir)
            if frames:
                output_ext = "gif" if out_format == "GIF" else "mp4"
                output_path = os.path.join(tmpdir, f"{filename}.{output_ext}")
                create_timelapse(frames, output_path, out_format)
 
                if not os.path.exists("static"):
                    os.makedirs("static")
                dest_path = os.path.join("static", f"{filename}.{output_ext}")
                shutil.move(output_path, dest_path)
 
                download_link = f"/static/{filename}.{output_ext}"
                message = "Success! Download below."
            else:
                message = "No frames generated. Check input or date range."
 
    return render_template_string(HTML_TEMPLATE,
                                  folium_map=m._repr_html_(),
                                  message=message,
                                  download_link=download_link)
 
if name == "main":
    import webbrowser
    import time
 
    # Optional delay to allow Flask server to start before browser opens
    time.sleep(1)
 
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
