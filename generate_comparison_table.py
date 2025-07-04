import json
import os
import glob
from collections import defaultdict, Counter
from datetime import datetime

def load_latest_json(data_dir="data"):
    files = sorted(glob.glob(os.path.join(data_dir, "latest_cars.json")), reverse=True)
    if not files:
        raise FileNotFoundError("No bilbasen_cars_*.json files found in data directory.")
    return files[0]

def extract_relevant_specs(listings):
    # Most relevant fields for electric cars
    cars = []
    for car in listings:
        make = car.get("make", "Unknown")
        model = car.get("model", "Unknown")
        variant = car.get("variant", "")
        price = car.get("price", {}).get("price", None)
        reg_date = car.get("properties", {}).get("firstregistrationdate", {}).get("displayTextShort", "")
        year = None
        if reg_date:
            try:
                year = int(reg_date.split("/")[-1]) if "/" in reg_date else int(reg_date)
            except Exception:
                year = None
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
        doors = car.get("doors", None)
        power = car.get("properties", {}).get("hk", {}).get("displayTextShort", "")
        power_hk = None
        if power:
            try:
                power_hk = int(power.split()[0])
            except Exception:
                power_hk = None
        gear = car.get("properties", {}).get("geartype", {}).get("displayTextShort", "")
        fuel = car.get("properties", {}).get("fueltype", {}).get("displayTextShort", "")
        uri = car.get("uri", "")
        cars.append({
            "make": make,
            "model": model,
            "variant": variant,
            "battery_kwh": battery_kwh,
            "power_hk": power_hk,
            "range_km": range_km,
            "doors": doors,
            "gear": gear,
            "fuel": fuel,
            "price": price,
            "year": year,
            "mileage_km": mileage_km,
            "uri": uri
        })
    return cars

def group_cars(cars):
    # Group by all fields except price, year, mileage, uri
    groups = defaultdict(list)
    for car in cars:
        key = (
            car["make"], car["model"], car["variant"], car["battery_kwh"],
            car["power_hk"], car["range_km"], car["doors"], car["gear"], car["fuel"]
        )
        groups[key].append(car)
    return groups

def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def generate_html(groups, output_file, all_cars):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = [f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Bilbasen Car Comparison Table</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8f8f8; color: #222; }}
            .container {{ margin: 2em auto; max-width: 98vw; background: #fff; padding: 2em; border-radius: 10px; box-shadow: 0 2px 8px #0002; }}
            table {{ border-collapse: collapse; width: 100%; min-width: 1200px; }}
            th, td {{ border: 1px solid #ccc; padding: 0.5em 0.8em; text-align: left; }}
            th {{ background: #e0e0e0; cursor: pointer; }}
            tr:nth-child(even) {{ background: #f6f6f6; }}
            .listing-links a {{ margin-right: 0.5em; }}
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
        </script>
    </head>
    <body>
    <div class="container">
        <h1>Bilbasen Car Comparison Table</h1>
        <p>Generated: {now}</p>
        <table id="carTable" data-sort-col="" data-sort-dir="">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Make</th>
                    <th onclick="sortTable(1)">Model</th>
                    <th onclick="sortTable(2)">Variant</th>
                    <th onclick="sortTable(3)">Battery (kWh)</th>
                    <th onclick="sortTable(4)">Power (hk)</th>
                    <th onclick="sortTable(5)">Range (km)</th>
                    <th onclick="sortTable(6)">Doors</th>
                    <th onclick="sortTable(7)">Gear</th>
                    <th onclick="sortTable(8)">Fuel</th>
                    <th onclick="sortTable(9)">Price (kr)</th>
                    <th onclick="sortTable(10)">Year</th>
                    <th onclick="sortTable(11)">Mileage (km)</th>
                    <th>Listings</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    """]
    for key, cars in groups.items():
        prices = [c["price"] for c in cars if c["price"] is not None]
        years = [c["year"] for c in cars if c["year"] is not None]
        mileages = [c["mileage_km"] for c in cars if c["mileage_km"] is not None]
        html.append("<tr>")
        for v in key:
            html.append(f'<td>{html_escape(v) if v is not None else "N/A"}</td>')
        # Price range
        if prices:
            html.append(f'<td>{min(prices):,} - {max(prices):,}</td>' if min(prices)!=max(prices) else f'<td>{min(prices):,}</td>')
        else:
            html.append('<td>N/A</td>')
        # Year range
        if years:
            html.append(f'<td>{min(years)} - {max(years)}</td>' if min(years)!=max(years) else f'<td>{min(years)}</td>')
        else:
            html.append('<td>N/A</td>')
        # Mileage range
        if mileages:
            html.append(f'<td>{min(mileages):,} - {max(mileages):,}</td>' if min(mileages)!=max(mileages) else f'<td>{min(mileages):,}</td>')
        else:
            html.append('<td>N/A</td>')
        # Listing links
        html.append('<td class="listing-links">' + ' '.join(f'<a href="{html_escape(c["uri"])}" target="_blank">Link</a>' for c in cars) + '</td>')
        # Count
        html.append(f'<td>{len(cars)}</td>')
        html.append("</tr>")
    html.append("""
            </tbody>
        </table>
    </div>
    """)
    # Recommend other specs if they have high variability
    # Find all possible extra fields
    extra_fields = [
        "description", "location", "trailer", "moth", "kmt", "features"
    ]
    # Count how many unique values for each extra field
    field_counts = {}
    for field in extra_fields:
        values = set()
        for car in all_cars:
            val = car.get(field)
            if isinstance(val, dict):
                val = tuple(val.items())
            if isinstance(val, list):
                val = tuple(val)
            if val:
                values.add(val)
        field_counts[field] = len(values)
    html.append("<div style='margin-top:2em;'><h2>Recommendation</h2><ul>")
    for field, count in field_counts.items():
        if count > 1:
            html.append(f"<li>Consider adding <b>{field}</b> (has {count} unique values)</li>")
    html.append("</ul></div>")
    html.append("</body></html>")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"Comparison table written to {output_file}")

def main():
    json_file = load_latest_json()
    print(f"Loading data from {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    listings = data.get("listings", [])
    cars = extract_relevant_specs(listings)
    groups = group_cars(cars)
    output_file = "bilbasen_comparison_table.html"
    generate_html(groups, output_file, listings)

if __name__ == "__main__":
    main() 