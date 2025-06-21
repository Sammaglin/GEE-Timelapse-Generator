🌍 GEE Timelapse Generator
A Flask web application to generate Landsat-based timelapse GIFs or MP4s using Google Earth Engine (GEE). Draw an Area of Interest (AOI) on the map, select the date range, and download your custom timelapse.

📌 Features
🗺️ Interactive Map using Leaflet

🖌️ Draw polygon AOI directly on the map

📅 Select date range with a date picker

🖼️ Choose imagery type:

True Color

NDVI

🎞️ Output formats: GIF or MP4

📥 Download generated timelapse

🚀 Installation & Setup
1️⃣ Clone the repository
bash
Copy
Edit
git clone https://github.com/your-username/gee-timelapse-generator.git
cd gee-timelapse-generator
2️⃣ Install dependencies
bash
Copy
Edit
pip install flask earthengine-api folium pillow imageio requests
3️⃣ Authenticate with Google Earth Engine
bash
Copy
Edit
earthengine authenticate
Or let the application prompt you.

4️⃣ Run the Flask server
bash
Copy
Edit
python gee_timelapse_web.py
Open in browser: http://127.0.0.1:5000

⚙️ Project Structure
php
Copy
Edit
├── gee_timelapse_web.py   # Main application
├── static/                # Generated output files (GIFs / MP4s)
└── README.md
🖥️ Usage
Open the web interface.

Draw your Area of Interest (Polygon recommended).

Select date range (e.g., 2015-01-01 to 2023-12-31).

Choose Imagery Type (True Color / NDVI).

Select Output Format (GIF / MP4).

Click Generate Timelapse.

Download the result once generated.

📷 Example Output
True Color (GIF)

NDVI (MP4)

❗ Known Issues
No progress tracking for frame generation (progress bar is simulated).

Limited imagery availability for small AOIs or short date ranges.

Long timelapse generation for large areas or long periods.

📦 Requirements
Python 3.7+

Google Earth Engine account

📃 License
MIT License
