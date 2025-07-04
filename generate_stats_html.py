import json
import os
import glob
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def load_latest_json(data_dir="data"):
    files = sorted(glob.glob(os.path.join(data_dir, "latest_cars.json")), reverse=True)
    if not files:
        raise FileNotFoundError("No bilbasen_cars_*.json files found in data directory.")
    return files[0]

def extract_stats(listings):
    stats = defaultdict(lambda: defaultdict(list))
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
        stats[make][model].append({
            "price": price,
            "year": year,
            "battery_kwh": battery_kwh,
            "mileage_km": mileage_km,
            "range_km": range_km,
            "uri": car.get("uri", "")
        })
    return stats, model_images

def compute_ranges(values):
    values = [v for v in values if v is not None]
    if not values:
        return (None, None)
    return (min(values), max(values))

def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def generate_html(stats, model_images, output_file):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = [f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Bilbasen Car Statistics</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8f8f8; color: #222; }}
            .brand {{ margin: 1em 0; padding: 1em; background: #fff; border-radius: 8px; box-shadow: 0 2px 6px #0001; }}
            .model-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1em; margin: 1em 0; }}
            .model-card {{ background: #f0f0f0; border-radius: 6px; padding: 0.5em; text-align: center; box-shadow: 0 1px 3px #0001; cursor: pointer; transition: box-shadow 0.2s; }}
            .model-card:hover {{ box-shadow: 0 4px 12px #0002; }}
            .model-card img {{ max-width: 100%; max-height: 280px; border-radius: 4px; margin-bottom: 0.5em; object-fit: cover; background: #fff; }}
            .model-card .model-title {{ font-weight: bold; font-size: 1.1em; margin-bottom: 0.2em; }}
            .model-card .model-count {{ color: #666; font-size: 0.95em; margin-bottom: 0.2em; }}
            .model-details {{ display: none; margin-top: 0.5em; }}
            .model-card.active .model-details {{ display: block; }}
            .stat-table {{ border-collapse: collapse; width: 100%; margin-top: 0.5em; }}
            .stat-table th, .stat-table td {{ border: 1px solid #ccc; padding: 0.3em 0.7em; text-align: left; }}
            .stat-table th {{ background: #e0e0e0; }}
        </style>
        <script>
        function toggleModelDetails(id) {{
            var el = document.getElementById(id);
            if (el.classList.contains('active')) {{
                el.classList.remove('active');
            }} else {{
                el.classList.add('active');
            }}
        }}
        </script>
    </head>
    <body>
        <h1>Bilbasen Car Statistics</h1>
        <p>Generated: {now}</p>
    """]
    for make in sorted(stats.keys()):
        html.append(f'<details class="brand" open><summary>{html_escape(make)} ({sum(len(stats[make][m]) for m in stats[make])} cars)</summary>')
        html.append('<div class="model-grid">')
        for idx, model in enumerate(sorted(stats[make].keys())):
            cars = stats[make][model]
            img_url = model_images[make][model]
            model_id = f"{make}_{model}".replace(" ", "_").replace("/", "_")
            prices = [c["price"] for c in cars]
            years = [c["year"] for c in cars]
            batteries = [c["battery_kwh"] for c in cars]
            price_min, price_max = compute_ranges(prices)
            year_min, year_max = compute_ranges(years)
            battery_min, battery_max = compute_ranges(batteries)
            html.append(f'''<div class="model-card" id="{model_id}" onclick="toggleModelDetails('{model_id}')">
                <div class="model-title">{html_escape(model)}</div>
                <div class="model-count">{len(cars)} cars</div>
                <img src="{html_escape(img_url)}" alt="{html_escape(model)}" />
                <div class="model-preview" style="font-size:0.97em; color:#444; margin:0.3em 0 0.2em 0;">
                    <div>Min price: {price_min:,} kr</div>
                    <div>Max year: {year_max if year_max is not None else 'N/A'}</div>
                    <div>Max battery: {battery_max if battery_max is not None else 'N/A'} kWh</div>
                </div>
                <div class="model-details">
            ''')
            mileages = [c["mileage_km"] for c in cars]
            ranges = [c["range_km"] for c in cars]
            mileage_min, mileage_max = compute_ranges(mileages)
            range_min, range_max = compute_ranges(ranges)
            html.append('<table class="stat-table">')
            html.append('<tr><th>Attribute</th><th>Min</th><th>Max</th></tr>')
            html.append(f'<tr><td>Price (kr)</td><td>{price_min:,} </td><td>{price_max:,} </td></tr>' if price_min is not None else '<tr><td>Price (kr)</td><td colspan=2>N/A</td></tr>')
            html.append(f'<tr><td>Year</td><td>{year_min}</td><td>{year_max}</td></tr>' if year_min is not None else '<tr><td>Year</td><td colspan=2>N/A</td></tr>')
            html.append(f'<tr><td>Battery (kWh)</td><td>{battery_min}</td><td>{battery_max}</td></tr>' if battery_min is not None else '<tr><td>Battery (kWh)</td><td colspan=2>N/A</td></tr>')
            html.append(f'<tr><td>Mileage (km)</td><td>{mileage_min:,}</td><td>{mileage_max:,}</td></tr>' if mileage_min is not None else '<tr><td>Mileage (km)</td><td colspan=2>N/A</td></tr>')
            html.append(f'<tr><td>Range (km)</td><td>{range_min:,}</td><td>{range_max:,}</td></tr>' if range_min is not None else '<tr><td>Range (km)</td><td colspan=2>N/A</td></tr>')
            html.append('</table>')
            html.append('<ul>')
            for c in cars:
                html.append(f'<li><a href="{html_escape(c["uri"])}" target="_blank">Listing</a></li>')
            html.append('</ul>')
            html.append('</div></div>')
        html.append('</div>')
        html.append('</details>')
    html.append("</body></html>")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"HTML statistics written to {output_file}")

def main():
    json_file = load_latest_json()
    print(f"Loading data from {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    listings = data.get("listings", [])
    stats, model_images = extract_stats(listings)
    output_file = "bilbasen_stats.html"
    generate_html(stats, model_images, output_file)

if __name__ == "__main__":
    main() 