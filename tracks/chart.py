# This was inspired by the work of uhdebbie, who made a similar script
# for plotting older HURDAT data. Thanks Debbie. You rock!
#
# This is VERY much a work in progress, and not pitch-perfect compared
# to the original code.
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.colorbar import ColorbarBase
from matplotlib.patches import FancyArrow
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LongitudeFormatter, LatitudeFormatter
import argparse
import sys
import os
from datetime import datetime

from hurdat2 import read_stormdata_hurdat2

category_colors = {
    'LO': '#BEBEBE',
    'SD': '#808080',
    'TD': '#3258f7',
    'TS': '#64bf4e',
    'C1': '#fbbf31',
    'C2': '#ff6e1c',
    'C3': '#e43b11',
    'C4': '#e81da6',
    'C5': '#bd25f7',
    'EX': 'black',
    'UN': '#BEBEBE'
}

category_labels = {
    'LO': 'LO',
    'SD': 'SD',
    'TD': 'TD',
    'TS': 'TS',
    'C1': 'C1',
    'C2': 'C2',
    'C3': 'C3',
    'C4': 'C4',
    'C5': 'C5',
    'EX': 'EX',
    'UN': 'UN'
}

wind_limits = {
    'TD': 34, 'TS': 64, 'C1': 83, 'C2': 96, 'C3': 113, 'C4': 137
}

def get_category(status, wind_kts):
    status = status.strip() if status else 'UN'

    try:
        wind_kts = float(wind_kts)
    except (ValueError, TypeError):
        wind_kts = 0

    if status in ['LO', 'DB', 'WV']:
        return 'LO'
    if status == 'EX':
        return 'EX'
    if status == 'SD':
        return 'SD'
    if status == 'SS':
        if wind_kts < wind_limits['TD']:
            return 'TD'
        elif wind_kts < wind_limits['TS']:
            return 'TS'
        elif wind_kts < wind_limits['C1']:
            return 'TS'
        elif wind_kts < wind_limits['C2']:
            return 'C1'
        elif wind_kts < wind_limits['C3']:
            return 'C2'
        elif wind_kts < wind_limits['C4']:
            return 'C3'
        elif wind_kts < wind_limits['C5']:
            return 'C4'
        else:
            return 'C5'

    if status in ['TD', 'TS', 'HU']:
        if wind_kts < wind_limits['TD']:
            return 'TD'
        elif wind_kts < wind_limits['TS']:
            return 'TS'
        elif wind_kts < wind_limits['C1']:
            return 'C1'
        elif wind_kts < wind_limits['C2']:
            return 'C2'
        elif wind_kts < wind_limits['C3']:
            return 'C3'
        elif wind_kts < wind_limits['C4']:
            return 'C4'
        else:
            return 'C5'

    if wind_kts > 0:
        if wind_kts < wind_limits['TD']: return 'TD'
        elif wind_kts < wind_limits['TS']: return 'TS'
        elif wind_kts < wind_limits['C1']: return 'C1'
        elif wind_kts < wind_limits['C2']: return 'C2'
        elif wind_kts < wind_limits['C3']: return 'C3'
        elif wind_kts < wind_limits['C4']: return 'C4'
        else: return 'C5'

    return 'UN'

def calculate_ace(positions):
    ace = 0.0
    for i, pos in enumerate(positions):
        status = pos.get('status', 'UN').strip()
        wind_kts_raw = pos.get('wind', -999)
        try:
            if isinstance(wind_kts_raw, str) and not wind_kts_raw.strip():
                 wind_kts = 0.0
            else:
                 wind_kts = float(wind_kts_raw)
        except (ValueError, TypeError):
            wind_kts = 0.0

        if status in ['TD', 'TS', 'HU', 'SS', 'SD'] and wind_kts >= 34:
            ace += (wind_kts ** 2)

    final_ace = round(ace * 1e-4, 2)
    return final_ace

def plot_track(storm, output_file, show_plot=False):
    positions = storm['positions']
    if not positions:
        print(f"No positions found for storm {storm['name']} {storm['year']}.")
        return

    lats = np.array([p['lat'] for p in positions])
    lons = np.array([p['lon'] for p in positions])

    winds_list = []
    for p in positions:
        wind_val = p.get('wind', 0)
        try:
            winds_list.append(float(wind_val))
        except (ValueError, TypeError):
            winds_list.append(0.0)
    winds = np.array(winds_list)

    pressures = np.array([p.get('pressure', -999) for p in positions])
    statuses = [p.get('status', 'UN') for p in positions]
    times = [p.get('time') for p in positions]

    valid_pressures = pressures[pressures > 0]
    min_pressure = np.min(valid_pressures) if valid_pressures.size > 0 else None
    min_pressure_idx = -1
    if min_pressure is not None:
        min_pressure_indices = np.where(pressures == min_pressure)[0]
        if min_pressure_indices.size > 0:
            min_pressure_idx = min_pressure_indices[0]

    ace = calculate_ace(positions)

    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    margin = 3
    lon_min, lon_max = np.min(lons) - margin, np.max(lons) + margin
    lat_min, lat_max = np.min(lats) - margin, np.max(lats) + margin
    lon_min = max(lon_min, -180)
    lon_max = min(lon_max, 180)
    lat_min = max(lat_min, -90)
    lat_max = min(lat_max, 90)
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f0e8d0')
    ax.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#a0c8f0')
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.6, edgecolor='#888888')
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.5, edgecolor='grey')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.5, color='#AAAAAA', linestyle=':')
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}

    last_day = -1
    for i in range(len(positions) - 1):
        cat = get_category(statuses[i], winds[i])
        color = category_colors.get(cat, 'grey')

        ax.plot([lons[i], lons[i+1]], [lats[i], lats[i+1]],
                color=color, linewidth=2.0, transform=ccrs.Geodetic())

        ax.plot(lons[i], lats[i], marker='o', markersize=5, color=color, transform=ccrs.Geodetic())

    last_cat = get_category(statuses[-1], winds[-1])
    last_color = category_colors.get(last_cat, 'grey')
    ax.plot(lons[-1], lats[-1], marker='o', markersize=5, color=last_color, transform=ccrs.Geodetic())

    name_idx = len(lons) - 1
    offset_x = 0.5
    offset_y = 0.5
    ha = 'left'
    va = 'bottom'
    if name_idx > 0:
        if lons[name_idx] < lons[name_idx-1]:
            ha = 'right'
            offset_x = -0.5
        if lats[name_idx] < lats[name_idx-1]:
            va = 'top'
            offset_y = -0.5

    plt.text(lons[name_idx] + offset_x, lats[name_idx] + offset_y, f"{storm['name']} {storm['year']}",
             fontsize=10, fontweight='bold', ha=ha, va=va, transform=ccrs.Geodetic())

    plt.title(f"{storm['name']} {storm['year']}", loc='left', fontsize=12, fontweight='bold')
    plt.title(f"ACE: {ace:.2f}", loc='right', fontsize=10)

    cbar_ax = fig.add_axes([0.92, 0.25, 0.02, 0.5])

    cat_order = ['C5', 'C4', 'C3', 'C2', 'C1', 'TS', 'TD', 'SD', 'LO']
    cmap_colors = [category_colors.get(cat, '#BEBEBE') for cat in cat_order]
    cmap = mcolors.ListedColormap(cmap_colors)
    bounds = np.arange(len(cat_order) + 1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm,
                      boundaries=bounds - 0.5,
                      ticks=np.arange(len(cat_order)),
                      spacing='proportional',
                      orientation='vertical')

    tick_labels = [category_labels.get(cat, cat) for cat in cat_order]
    cb.set_ticks(np.arange(len(cat_order)))
    cb.set_ticklabels(tick_labels)
    cb.ax.tick_params(labelsize=9)

    plt.subplots_adjust(left=0.05, right=0.9, top=0.95, bottom=0.05)

    if show_plot:
        plt.show()
    else:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Map generated and saved to {output_file}.")
        plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Plots the track of a cyclone from HURDAT2 data.")
    parser.add_argument("--input", type=str, default="HURDAT2.txt", help="HURDAT2 input file (default: HURDAT2.txt)")
    parser.add_argument("--output", type=str, default="../png/output-track.png", help="Output PNG file (default: ../png/output-track.png)")
    parser.add_argument("--id", type=str, help="Cyclone ID (e.g., AL012023)")
    parser.add_argument("--name", type=str, help="Storm name (e.g., Ana)")
    parser.add_argument("--year", type=int, help="Storm year (e.g., 2023)")
    parser.add_argument("--show", action="store_true", help="Show the plot instead of saving it")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"No entry file found: {args.input}")
        sys.exit(1)

    storms = read_stormdata_hurdat2(args.input)
    if not storms:
        print("No storms found in the provided HURDAT2 file.")
        sys.exit(1)

    storm_to_plot = None
    if args.id:
        storm_id_upper = args.id.upper()
        for s in storms:
            if s["id"] == storm_id_upper:
                storm_to_plot = s
                break
        if not storm_to_plot:
            print(f"No cyclone found with ID: {args.id}")
            sys.exit(1)
    elif args.name and args.year:
        name_upper = args.name.upper()
        for s in storms:
            if s["name"].strip().upper() == name_upper and s["year"] == args.year:
                storm_to_plot = s
                break
        if not storm_to_plot:
            print(f"No cyclone found with name: {args.name} and year: {args.year}")
            sys.exit(1)
    elif args.name:
         print("Please provide the year along with the name.")
         sys.exit(1)
    else:
        print("No cyclone ID or name provided. Using the first storm in the list.")
        storm_to_plot = storms[0]

    plot_track(storm_to_plot, args.output, args.show)

if __name__ == "__main__":
    main()
