import json
import os
import glob
from collections import defaultdict
from datetime import datetime

def load_latest_json(data_dir="data"):
    files = sorted(glob.glob(os.path.join(data_dir, "latest_cars.json")), reverse=True)
    if not files:
        raise FileNotFoundError("No bilbasen_cars_*.json files found in data directory.")
    return files[0]

def extract_stats(listings):
    stats = []
    model_images = defaultdict(lambda: defaultdict(str))
    for car in listings:
        make = car.get("make", "Unknown")
        model = car.get("model", "Unknown")
        price = car.get("price", {}).get("price", None)
        reg_date = car.get("properties", {}).get("firstregistrationdate", {}).get("displayTextShort", "")
        year = None
        if reg_date:
            year = int(reg_date.split("/")[-1]) if "/" in reg_date else int(reg_date)
        battery = car.get("properties", {}).get("batterycapacity", {}).get("displayTextShort", "")
        battery_kwh = None
        if battery:
            try:
                battery_kwh = float(battery.split()[0].replace(",", "."))
            except Exception:
                battery_kwh = None
        mileage = car.get("properties", {}).get("mileage", {}).get("displayTextShort", "")
        mileage_km = None
        if mileage:
            try:
                mileage_km = int(mileage.replace(" km", "").replace(".", ""))
            except Exception:
                mileage_km = None
        electric_range = car.get("properties", {}).get("electricmotorrange", {}).get("displayTextShort", "")
        range_km = None
        if electric_range:
            try:
                range_km = int(electric_range.replace(" km", "").replace(".", ""))
            except Exception:
                range_km = None
        # Find first image for the model if not already set
        if not model_images[make][model]:
            media = car.get("media", [])
            for m in media:
                if m.get("mediaType") == "Picture":
                    model_images[make][model] = m.get("url")
                    break
        stats.append({
            "make": make,
            "model": model,
            "price": price,
            "year": year,
            "battery_kwh": battery_kwh,
            "mileage_km": mileage_km,
            "range_km": range_km,
            "uri": car.get("uri", ""),
            "img_url": model_images[make][model]
        })
    return stats

def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def generate_html(stats, output_file):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = [f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Bilbasen Car Table Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8f8f8; color: #222; }}
            .container {{ margin: 2em auto; max-width: 1200px; background: #fff; padding: 2em; border-radius: 10px; box-shadow: 0 2px 8px #0002; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 0.5em 0.8em; text-align: left; }}
            th {{ background: #e0e0e0; cursor: pointer; }}
            tr:nth-child(even) {{ background: #f6f6f6; }}
            .photo-col img {{ max-width: 120px; max-height: 80px; border-radius: 4px; background: #fff; }}
            .toggle-btn {{ margin-bottom: 1em; }}
        </style>
        <script>
        // Sort table by column
        function sortTable(n) {{
            var table = document.getElementById("carTable");
            var rows = Array.from(table.rows).slice(1);
            var asc = table.getAttribute('data-sort-col') != n || table.getAttribute('data-sort-dir') == 'desc';
            rows.sort(function(a, b) {{
                var x = a.cells[n].innerText || a.cells[n].textContent;
                var y = b.cells[n].innerText || b.cells[n].textContent;
                var xNum = parseFloat(x.replace(/[^0-9.-]+/g, ''));
                var yNum = parseFloat(y.replace(/[^0-9.-]+/g, ''));
                if (!isNaN(xNum) && !isNaN(yNum)) {{
                    return asc ? xNum - yNum : yNum - xNum;
                }}
                return asc ? x.localeCompare(y) : y.localeCompare(x);
            }});
            for (var i = 0; i < rows.length; i++) table.tBodies[0].appendChild(rows[i]);
            table.setAttribute('data-sort-col', n);
            table.setAttribute('data-sort-dir', asc ? 'asc' : 'desc');
        }}
        // Toggle photo column
        function togglePhoto() {{
            var show = document.getElementById('photoToggle').checked;
            var table = document.getElementById('carTable');
            var idx = 0; // photo is first column
            for (var r of table.rows) {{
                if (r.cells.length > idx) r.cells[idx].style.display = show ? '' : 'none';
            }}
        }}
        </script>
    </head>
    <body>
    <div class="container">
        <h1>Bilbasen Car Table Report</h1>
        <p>Generated: {now}</p>
        <label class="toggle-btn"><input type="checkbox" id="photoToggle" checked onchange="togglePhoto()"> Show Photo</label>
        <table id="carTable" data-sort-col="" data-sort-dir="">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Photo</th>
                    <th onclick="sortTable(1)">Make</th>
                    <th onclick="sortTable(2)">Model</th>
                    <th onclick="sortTable(3)">Year</th>
                    <th onclick="sortTable(4)">Price (kr)</th>
                    <th onclick="sortTable(5)">Battery (kWh)</th>
                    <th onclick="sortTable(6)">Mileage (km)</th>
                    <th onclick="sortTable(7)">Range (km)</th>
                    <th>Listing</th>
                </tr>
            </thead>
            <tbody>
    """]
    for car in stats:
        html.append("<tr>")
        # Photo
        html.append(f'<td class="photo-col"><img src="{html_escape(car["img_url"])}" alt="{html_escape(car["model"])}" /></td>')
        # Make, Model, Year, Price, Battery, Mileage, Range
        html.append(f'<td>{html_escape(car["make"])}</td>')
        html.append(f'<td>{html_escape(car["model"])}</td>')
        html.append(f'<td>{car["year"] if car["year"] is not None else "N/A"}</td>')
        html.append(f'<td>{car["price"]:,} </td>' if car["price"] is not None else '<td>N/A</td>')
        html.append(f'<td>{car["battery_kwh"]}</td>' if car["battery_kwh"] is not None else '<td>N/A</td>')
        html.append(f'<td>{car["mileage_km"]:,}</td>' if car["mileage_km"] is not None else '<td>N/A</td>')
        html.append(f'<td>{car["range_km"]:,}</td>' if car["range_km"] is not None else '<td>N/A</td>')
        html.append(f'<td><a href="{html_escape(car["uri"])}" target="_blank">Listing</a></td>')
        html.append("</tr>")
    html.append("""
            </tbody>
        </table>
    </div>
    <script>togglePhoto();</script>
    </body>
    </html>
    """)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"HTML table report written to {output_file}")

def main():
    json_file = load_latest_json()
    print(f"Loading data from {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    listings = data.get("listings", [])
    stats = extract_stats(listings)
    output_file = "bilbasen_stats_table.html"
    generate_html(stats, output_file)

if __name__ == "__main__":
    main() 