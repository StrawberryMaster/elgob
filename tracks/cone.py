# Taken from https://github.com/Sohum09/Code-for-storms/blob/main/ConeForecast.py
# and adapted here to use hurdat2. All attribution goes to Sohum09 for the original code!
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import argparse
import sys
import os

from hurdat2 import read_stormdata_hurdat2

def generate_cone_radius(num_points):
    base = 0.4
    step = 0.2 if num_points <= 10 else (1.5 / max(1, num_points-1))
    return [base + i*step for i in range(num_points)]

def main():
    parser = argparse.ArgumentParser(description="Generates cone forecast for a cyclone from HURDAT2 data.")
    parser.add_argument("--input", type=str, required=True, help="HURDAT2 input file")
    parser.add_argument("--output", type=str, default="../png/output-cone.png", help="Output PNG file")
    parser.add_argument("--id", type=int, help="Cyclone ID (optional)")
    parser.add_argument("--name", type=str, help="Cyclone name (optional)")
    parser.add_argument("--show", action="store_true", help="Shows the plot instead of saving it")
    parser.add_argument("--start", type=int, default=0, help="First index of the cone point")
    parser.add_argument("--end", type=int, help="Final index of the cone point")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Entry file not found: {args.input}")
        sys.exit(1)

    storms = read_stormdata_hurdat2(args.input)
    if not storms:
        print("No storms found in the provided HURDAT2 file.")
        sys.exit(1)

    storm = None
    if args.id:
        for s in storms:
            if s["id"] == args.id:
                storm = s
                break
    elif args.name:
        for s in storms:
            if s["name"].upper() == args.name.upper():
                storm = s
                break
    else:
        storm = storms[0]

    if not storm:
        print("No cyclone found with the provided ID or name.")
        sys.exit(1)

    positions = storm["positions"][args.start:args.end] if args.end else storm["positions"][args.start:]
    if not positions:
        print("No positions found for the selected storm.")
        sys.exit(1)

    latitudes = [pos["lat"] for pos in positions]
    longitudes = [pos["lon"] for pos in positions]
    forecast_winds = [pos["wind"] for pos in positions]
    num_points = len(latitudes)

    cone_radius = generate_cone_radius(num_points)

    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(12, 10))
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', color='gray')

    plt.plot(longitudes, latitudes, 'w-', label='TC Path')

    count = 9
    dupl = []
    for i in range(num_points):
        wind = forecast_winds[i]
        if wind < 0: #Non-tropical points
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='w', alpha=0.2, transform=ccrs.PlateCarree())
            count = -2
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='w', marker='*', label='Not Tropical')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='w', marker='*')
            ax.add_patch(circle)
        elif wind >= 140: #C5
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='m', alpha=0.2, transform=ccrs.PlateCarree())
            count = 5
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='m', marker='o', label='Category 5')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='m', marker='o')
            ax.add_patch(circle)
        elif wind >= 115: #C4
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='r', alpha=0.2, transform=ccrs.PlateCarree())
            count = 4
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='r', marker='o', label='Category 4')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='r', marker='o')
            ax.add_patch(circle)
        elif wind >= 100: #C3
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='#ff5908', alpha=0.2, transform=ccrs.PlateCarree())
            count = 3
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='#ff5908', marker='o', label='Category 3')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='#ff5908', marker='o')
            ax.add_patch(circle)
        elif wind >= 65: #C1
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='#ffff00', alpha=0.2, transform=ccrs.PlateCarree())
            count = 1
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='#ffff00', marker='o', label='Category 1')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='#ffff00', marker='o')
            ax.add_patch(circle)
        elif wind >= 35: #TS
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='g', alpha=0.2, transform=ccrs.PlateCarree())
            count = 0
            if count not in dupl:
                plt.scatter(longitudes[i], latitudes[i], color='g', marker='o', label='Tropical storm')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='g', marker='o')
            ax.add_patch(circle)
        else: #TD
            circle = plt.Circle((longitudes[i], latitudes[i]), cone_radius[i], color='b', alpha=0.2, transform=ccrs.PlateCarree())
            count = -1
            if count not in dupl: 
                plt.scatter(longitudes[i], latitudes[i], color='b', marker='o', label='Tropical depression')
                dupl.append(count)
            else:
                plt.scatter(longitudes[i], latitudes[i], color='b', marker='o')
            ax.add_patch(circle)

    ax.set_xlim(min(longitudes)-5, max(longitudes)+5)
    ax.set_ylim(min(latitudes)-5, max(latitudes)+5)

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f"Hurricane Forecast Cone: {storm['name']} {storm['year']}")
    plt.legend()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    plt.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"Map generated and saved to {args.output}")

    plt.grid(True)
    if args.show:
        plt.show()
    else:
        plt.close(fig)

if __name__ == "__main__":
    main()