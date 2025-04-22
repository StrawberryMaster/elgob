import argparse
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.colors import to_rgba
import matplotlib.patheffects as path_effects
from atcf import read_stormdata_atcf
from hurdat import read_stormdata_hurdat
from hurdat2 import read_stormdata_hurdat2
from jma import read_stormdata_jma
from md import read_stormdata_md
from tcr import read_stormdata_tcr
from scales import SSHWS_ENTRIES, AUS_ENTRIES, IMD_ENTRIES, JMA_ENTRIES, MFR_ENTRIES, JMADOM_ENTRIES

def get_color_from_wind(wind, scale="SSHWS"):
    if scale == "AUS":
        entries = AUS_ENTRIES
    elif scale == "IMD":
        entries = IMD_ENTRIES
    elif scale == "JMA":
        entries = JMA_ENTRIES
    elif scale == "MFR":
        entries = MFR_ENTRIES
    elif scale == "JMADOM":
        entries = JMADOM_ENTRIES
    else:
        entries = SSHWS_ENTRIES
    
    if wind == 0:
        return (0.75, 0.75, 0.75)
    
    for i in range(len(entries) - 1):
        if wind < entries[i + 1].wind:
            return entries[i].value
    
    return entries[-2].value

def parse_args():
    parser = argparse.ArgumentParser(description="Create hurricane track maps")
    parser.add_argument("--year", type=int, help="Select tropical cyclones from a specific year")
    parser.add_argument("--name", type=str, help="Select tropical cyclones with a specific name")
    parser.add_argument("--input", type=str, help="Use a text file to create tracking map")
    parser.add_argument("--id", type=int, help="Storm ID number in its year")
    parser.add_argument("--format", type=str, choices=["hurdat", "tcr", "atcf", "md", "tab", "jma", "hurdat2"], help="Set format for input files")
    parser.add_argument("--negx", type=int, default=1, help="Set to non-zero value for longitude west of the prime meridian")
    parser.add_argument("--negy", type=int, default=0, help="Set to non-zero value for latitude south of the equator")
    parser.add_argument("--wind", type=int, help="Look for storms with at least this wind")
    parser.add_argument("--next", action="store_true", help="Add on another storm")
    parser.add_argument("--res", type=int, default=1024, help="Set the horizontal resolution of output image")
    parser.add_argument("--bg", type=str, default="../data/bg8192.png", help="Set the map to use for background")
    parser.add_argument("--output", type=str, default="../png/output.png", help="Set the output file")
    parser.add_argument("--template", type=int, default=1, help="Set to non-zero to pre-fill {{WPTC track map}}")
    parser.add_argument("--alpha", type=float, default=1.0, help="Set transparency for storm tracks")
    parser.add_argument("--noextra", action="store_true", help="Skip extratropical portion of the tracks when specified")
    parser.add_argument("--dots", type=float, default=0.3, help="Set size of dots, in degrees")
    parser.add_argument("--lines", type=float, default=0.075, help="Set size of lines, in degrees")
    parser.add_argument("--scale", type=str, default="SSHWS", choices=["SSHWS", "AUS", "IMD", "JMA", "MFR", "JMADOM"], help="Set the TC classification scale to use for this map")
    parser.add_argument("--useoldcolorkey", type=int, default=0, help="Use the legacy color key when useoldcolorkey!=0")
    parser.add_argument("--skipasynoptic", type=int, default=1, help="Set to 0 to not have the maker skip asynoptic points")
    parser.add_argument("--inferoutputlocation", type=int, default=0, help="Automatically infer the file name when inferoutputlocation!=0")
    parser.add_argument("--xmin", type=float, help="Minimum longitude")
    parser.add_argument("--xmax", type=float, help="Maximum longitude")
    parser.add_argument("--ymin", type=float, help="Minimum latitude")
    parser.add_argument("--ymax", type=float, help="Maximum latitude")
    parser.add_argument("--show_names", action="store_true", help="Display storm names on the map")
    parser.add_argument("--show_legend", action="store_true", help="Display a color legend for storm categories")
    return parser.parse_args()

def circular_mean(angles_deg):
    """Calculates the circular mean of a list of angles in degrees."""
    if not angles_deg:
        return 0.0
    angles_rad = np.deg2rad(angles_deg)
    mean_sin = np.mean(np.sin(angles_rad))
    mean_cos = np.mean(np.cos(angles_rad))
    mean_angle_rad = np.arctan2(mean_sin, mean_cos)
    mean_angle_deg = np.rad2deg(mean_angle_rad)
    return (mean_angle_deg + 360) % 360

def circular_distance(angle1_deg, angle2_deg):
    """Calculates the circular distance between two angles in degrees."""
    diff = abs(angle1_deg - angle2_deg)
    return min(diff, 360 - diff)

def read_storm_data(args):
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return []
    
    storms = []
    try:
        if args.format == "hurdat":
            storms = read_stormdata_hurdat(args.input)
        elif args.format == "atcf":
            storms = read_stormdata_atcf(args.input, args.skipasynoptic)
        elif args.format == "jma":
            storms = read_stormdata_jma(args.input, args.skipasynoptic)
        elif args.format == "hurdat2":
            storms = read_stormdata_hurdat2(args.input, args.skipasynoptic)
        elif args.format == "md":
            storms = read_stormdata_md(args.input)
        elif args.format == "tcr":
            storms = read_stormdata_tcr(args.input)
    except Exception as e:
        print(f"Error reading file '{args.input}': {str(e)}")
        return []
    
    if not storms:
        print(f"No storms found in {args.input}. Check the file format and content.")
        return []
    
    filtered_storms = []
    for storm in storms:
        if args.year and storm["year"] != args.year:
            continue
        if args.name and storm["name"].upper() != args.name.upper():
            continue
        if args.id and storm["id"] != args.id:
            continue
        if args.wind:
            max_wind = max([pos["wind"] for pos in storm["positions"]], default=0)
            if max_wind < args.wind:
                continue
        filtered_storms.append(storm)
    
    if not filtered_storms:
        print("No system found with the specified parameters. Check the filters.")
        return []

    lat_positions = [pos["lat"] for storm in filtered_storms for pos in storm["positions"]]
    if lat_positions:
        min_lat = min(lat_positions)
        max_lat = max(lat_positions)
        padding_lat = 10.0
        args.ymin = min_lat - padding_lat if args.ymin is None else args.ymin
        args.ymax = max_lat + padding_lat if args.ymax is None else args.ymax
    else:
        args.ymin = -90 if args.ymin is None else args.ymin
        args.ymax = 90 if args.ymax is None else args.ymax

    lon_positions = [pos["lon"] for storm in filtered_storms for pos in storm["positions"]]
    padding_lon = 10.0
    if lon_positions:
        lons_360 = [(lon + 360) % 360 for lon in lon_positions]
        
        center_lon_360 = circular_mean(lons_360)
        distances = [circular_distance(lon, center_lon_360) for lon in lons_360]
        max_dist = max(distances) if distances else 0
        
        view_span = min(360.0, (2 * max_dist) + (2 * padding_lon))
        
        view_lon_min = center_lon_360 - view_span / 2
        view_lon_max = center_lon_360 + view_span / 2

        args.view_lon_min = view_lon_min if args.xmin is None else args.xmin
        args.view_lon_max = view_lon_max if args.xmax is None else args.xmax

        if args.xmin is None: args.xmin = wrap_longitude(view_lon_min)
        if args.xmax is None: args.xmax = wrap_longitude(view_lon_max)

    else:
        args.view_lon_min = -180.0 if args.xmin is None else args.xmin
        args.view_lon_max = 180.0 if args.xmax is None else args.xmax
        if args.xmin is None: args.xmin = -180.0
        if args.xmax is None: args.xmax = 180.0

    initial_view_lon_min = args.view_lon_min
    initial_view_lon_max = args.view_lon_max
    initial_ymin = args.ymin
    initial_ymax = args.ymax

    center_lon_initial = (initial_view_lon_min + initial_view_lon_max) / 2
    center_lat_initial = (initial_ymin + initial_ymax) / 2

    lon_span_initial = initial_view_lon_max - initial_view_lon_min
    lat_span_initial = initial_ymax - initial_ymin
    if lat_span_initial <= 0: lat_span_initial = 1
    
    target_ratio = 16 / 9
    current_ratio = lon_span_initial / lat_span_initial

    if abs(current_ratio - target_ratio) > 1e-6:
        if current_ratio < target_ratio:
            target_lon_span = target_ratio * lat_span_initial
            args.view_lon_min = center_lon_initial - target_lon_span / 2
            args.view_lon_max = center_lon_initial + target_lon_span / 2

            args.ymin = initial_ymin
            args.ymax = initial_ymax
        else: # current_ratio > target_ratio
            target_lat_span = lon_span_initial / target_ratio
            args.ymin = center_lat_initial - target_lat_span / 2
            args.ymax = center_lat_initial + target_lat_span / 2

            args.view_lon_min = initial_view_lon_min
            args.view_lon_max = initial_view_lon_max
    else:
         args.view_lon_min = initial_view_lon_min
         args.view_lon_max = initial_view_lon_max
         args.ymin = initial_ymin
         args.ymax = initial_ymax

    args.xmin = wrap_longitude(args.view_lon_min)
    args.xmax = wrap_longitude(args.view_lon_max)

    return filtered_storms

def wrap_longitude(lon):
    """Wraps longitude to the range [-180, 180]."""
    lon = lon % 360
    if lon > 180:
        lon -= 360
    return lon

def adjust_longitude_for_view(lon, center_lon):
    """Adjusts longitude to fit within the view range centered around center_lon."""
    while lon < center_lon - 180:
        lon += 360
    while lon > center_lon + 180:
        lon -= 360
    return lon

def calculate_dimensions(width, height, args):
    """Calculate image dimensions maintaining target ratio and resolution."""
    X_RATIO = 1.618033988749894
    Y_RATIO = 1.0
    
    lon_span = width
    lat_span = height
    
    if lat_span > lon_span / X_RATIO:
        lon_span = lat_span * X_RATIO
    elif lat_span < lon_span / Y_RATIO:
        lat_span = lon_span / Y_RATIO
        
    if lat_span > lon_span:
        yres = args.res
        xres = int(yres * lon_span / lat_span + 0.5)
    else:
        xres = args.res
        yres = int(xres * lat_span / lon_span + 0.5)
        
    return xres, yres

def generate_track_map(storms, args):
    print(f"Loading background image: {args.bg}")

    EXTRA_SPACE = 5.0
    MIN_DIM = 45.0

    lon_span = args.view_lon_max - args.view_lon_min
    lat_span = args.ymax - args.ymin

    if lon_span < MIN_DIM:
        diff = MIN_DIM - lon_span
        lon_span = MIN_DIM
        args.view_lon_min -= diff / 2
        args.view_lon_max += diff / 2

    width, height = calculate_dimensions(lon_span, lat_span, args)

    dpi = 100
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi, facecolor='black')
    ax = fig.add_subplot(111)

    try:
        bg_img = mpimg.imread(args.bg)
        full_height, full_width = bg_img.shape[:2]
    except FileNotFoundError:
        print(f"Background image not found: {args.bg}")
        print("Using solid black background instead")
        bg_img = None
        full_height, full_width = 1800, 3600

    view_lon_min = args.view_lon_min
    view_lon_max = args.view_lon_max
    view_lat_min = args.ymin
    view_lat_max = args.ymax
    center_lon_view = (view_lon_min + view_lon_max) / 2

    if bg_img is not None:
        print("Tiling background...")
        base_lon_min = -180
        base_lon_max = 180
        base_lon_span = base_lon_max - base_lon_min # 360

        start_tile_index = math.floor((view_lon_min - base_lon_max) / base_lon_span)
        end_tile_index = math.ceil((view_lon_max - base_lon_min) / base_lon_span)

        for i in range(start_tile_index, end_tile_index + 1):
            tile_lon_min = base_lon_min + i * base_lon_span
            tile_lon_max = base_lon_max + i * base_lon_span
            
            img_x_min = 0
            img_x_max = full_width
            img_y_min = (90 - view_lat_max) * (full_height / 180.0)
            img_y_max = (90 - view_lat_min) * (full_height / 180.0)

            img_y_min = max(0, int(img_y_min))
            img_y_max = min(full_height, int(img_y_max))
            
            if img_y_min >= img_y_max: continue

            cropped_bg = bg_img[img_y_min:img_y_max, img_x_min:img_x_max]
            
            ax.imshow(cropped_bg, 
                      extent=[tile_lon_min, tile_lon_max, view_lat_min, view_lat_max], 
                      interpolation='lanczos', aspect='auto')
    else:
        ax.set_facecolor('black')

    def calculate_line_width(lines_param, width, lon_span):
        return max(1, lines_param / max(1e-6, lon_span) * width)

    line_width = calculate_line_width(args.lines, width, lon_span)

    def calculate_dot_area(dots_param, width, lon_span, scale=1.8):
        diameter = scale * dots_param / max(1e-6, lon_span) * width
        area = (diameter / 2) ** 2 * math.pi
        return max(10, area)

    dot_area = calculate_dot_area(args.dots, width, lon_span)

    for storm in storms:
        adjusted_positions = []
        for pos in storm["positions"]:
            if args.noextra and pos.get("type") == "EXTRATROPICAL":
                continue
            adj_pos = pos.copy()
            adj_pos["lon"] = adjust_longitude_for_view(pos["lon"], center_lon_view)
            adjusted_positions.append(adj_pos)

        if not adjusted_positions: continue

        if hasattr(args, 'show_names') and args.show_names:
            label_pos = adjusted_positions[0]
            offset_y = (view_lat_max - view_lat_min) * 0.05
            label_text = ax.text(label_pos["lon"], label_pos["lat"] - offset_y,
                               storm["name"],
                               color='white', fontsize=8, fontweight='bold',
                               ha='center', va='top', zorder=30)
            label_text.set_path_effects([
                path_effects.Stroke(linewidth=2, foreground='black'),
                path_effects.Normal()
            ])

        if len(adjusted_positions) > 1:
            lons = [pos["lon"] for pos in adjusted_positions]
            lats = [pos["lat"] for pos in adjusted_positions]
            ax.plot(lons, lats, color=(1, 1, 1, args.alpha), linewidth=line_width, zorder=10)

        lons = []
        lats = []
        colors = []
        sizes = []
        markers = []
        for pos in adjusted_positions:
            lons.append(pos["lon"])
            lats.append(pos["lat"])
            r, g, b = get_color_from_wind(pos["wind"], args.scale)
            colors.append((r, g, b, args.alpha))
            if pos.get("type") == "SUBTROPICAL":
                markers.append('s')
                sizes.append(dot_area * 0.60)
            elif pos.get("type") == "EXTRATROPICAL":
                markers.append('^')
                sizes.append(dot_area * 0.70)
            else:
                markers.append('o')
                sizes.append(dot_area)

        for marker in set(markers):
            idxs = [i for i, m in enumerate(markers) if m == marker]
            marker_lons = [lons[i] for i in idxs]
            marker_lats = [lats[i] for i in idxs]
            marker_colors = [colors[i] for i in idxs]
            marker_sizes = [sizes[i] for i in idxs]
            ax.scatter(marker_lons, marker_lats, c=marker_colors, s=marker_sizes,
                       marker=marker, zorder=20, edgecolor='none', linewidths=0)

    ax.set_xlim(view_lon_min, view_lon_max)
    ax.set_ylim(view_lat_min, view_lat_max)

    ax.set_aspect('equal', adjustable='box')
    ax.set_axis_off()

    if hasattr(args, 'show_legend') and args.show_legend:
        legend_entries = []
        legend_labels = []
        
        if args.scale == "SSHWS":
            categories = [
                ((0.75, 0.75, 0.75), "Depression"),
                ((0, 0, 1), "Storm"),
                ((0, 1, 1), "Category 1"),
                ((0, 1, 0), "Category 2"),
                ((1, 1, 0), "Category 3"),
                ((1, 0.5, 0), "Category 4"),
                ((1, 0, 0), "Category 5")
            ]
        elif args.scale == "AUS":
            categories = []
            for entry in AUS_ENTRIES:
                categories.append((entry.value, entry.name))
        elif args.scale == "IMD":
            categories = []
            for entry in IMD_ENTRIES:
                categories.append((entry.value, entry.name))
        elif args.scale == "JMA":
            categories = []
            for entry in JMA_ENTRIES:
                categories.append((entry.value, entry.name))
        elif args.scale == "MFR":
            categories = []
            for entry in MFR_ENTRIES:
                categories.append((entry.value, entry.name))
        elif args.scale == "JMADOM":
            categories = []
            for entry in JMADOM_ENTRIES:
                categories.append((entry.value, entry.name))
        
        for color, label in categories:
            legend_entries.append(plt.Line2D([0], [0], marker='o', color='w', 
                                          markerfacecolor=color, markersize=8, 
                                          linewidth=0))
            legend_labels.append(label)
        
        legend = ax.legend(legend_entries, legend_labels, loc='lower left', 
                         frameon=True, facecolor='black', framealpha=0.7, 
                         fontsize=8)
        
        for text in legend.get_texts():
            text.set_color('white')
    
    try:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        plt.savefig(args.output, bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close(fig)
        print(f"Map generated and saved to {args.output}")
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        # fallback to saving in the current directory
        fallback_path = os.path.join(os.getcwd(), "track_map_fallback.png")
        plt.savefig(fallback_path, bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close(fig)
        print(f"Map saved to fallback location: {fallback_path}")

def get_pos(pos, img_size, args):
    if None in [args.xmin, args.xmax, args.ymin, args.ymax]:
        xmin = args.xmin if args.xmin is not None else -180
        xmax = args.xmax if args.xmax is not None else 180
        ymin = args.ymin if args.ymin is not None else -90
        ymax = args.ymax if args.ymax is not None else 90
    else:
        xmin = args.xmin
        xmax = args.xmax
        ymin = args.ymin
        ymax = args.ymax
    
    x = (pos["lon"] - xmin) / (xmax - xmin) * img_size[0]
    
    y = (ymax - pos["lat"]) / (ymax - ymin) * img_size[1]
    
    return x, y

def main():
    args = parse_args()
    
    if not args.input:
        print("Input file not specified; please specify --input.")
        return
    
    if not args.format:
        if args.input.endswith('.txt'):
            print("Format not specified; assuming hurdat format.")
            args.format = "hurdat"
        else:
            print("Jinkies. No format specified; please specify --format.")
            return
    
    print(f"Reading storm data from {args.input}...")
    storms = read_storm_data(args)
    
    if not storms:
        print("No storms found after filtering. Please check your filters.")
        return
    
    print(f"Generating track map for {len(storms)} storms...")
    generate_track_map(storms, args)
    print("Track map generated successfully.")

if __name__ == "__main__":
    main()
