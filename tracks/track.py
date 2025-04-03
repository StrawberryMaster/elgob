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
    
    if not all([args.xmin, args.xmax, args.ymin, args.ymax]) and filtered_storms:
        lon_positions = [pos["lon"] for storm in filtered_storms for pos in storm["positions"]]
        lat_positions = [pos["lat"] for storm in filtered_storms for pos in storm["positions"]]
        
        if lon_positions and lat_positions:
            min_lon = min(lon_positions)
            max_lon = max(lon_positions)
            min_lat = min(lat_positions)
            max_lat = max(lat_positions)
            
            padding = 10.0
            args.xmin = min_lon - padding if args.xmin is None else args.xmin
            args.xmax = max_lon + padding if args.xmax is None else args.xmax
            args.ymin = min_lat - padding if args.ymin is None else args.ymin
            args.ymax = max_lat + padding if args.ymax is None else args.ymax
        else:
            args.xmin = -180 if args.xmin is None else args.xmin
            args.xmax = 180 if args.xmax is None else args.xmax
            args.ymin = -90 if args.ymin is None else args.ymin
            args.ymax = 90 if args.ymax is None else args.ymax
    
    return filtered_storms

def generate_track_map(storms, args):
    print(f"Loading background image: {args.bg}")
    
    width = args.res
    height = int(width * 9 / 16)
    print(f"Image size: {width} x {height} (16:9 format)")
    
    dpi = 100
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi, facecolor='black')
    ax = fig.add_subplot(111)
    
    try:
        bg_img = mpimg.imread(args.bg)
    except FileNotFoundError:
        print(f"Background image not found: {args.bg}")
        print("Using solid black background instead")
        bg_img = np.zeros((height, width, 3))
    
    extent = None
    if args.xmin is not None and args.xmax is not None and args.ymin is not None and args.ymax is not None:
        if args.xmin >= args.xmax or args.ymin >= args.ymax:
            print("Warning: Invalid geographic limits. Resetting to defaults.")
            args.xmin, args.xmax = -180, 180
            args.ymin, args.ymax = -90, 90
            
        lon_span = args.xmax - args.xmin
        lat_span = args.ymax - args.ymin
        target_ratio = 16 / 9
        current_ratio = lon_span / lat_span
        
        if current_ratio < target_ratio:
            extra_lon = (target_ratio * lat_span - lon_span) / 2
            args.xmin -= extra_lon
            args.xmax += extra_lon
        elif current_ratio > target_ratio:
            extra_lat = (lon_span / target_ratio - lat_span) / 2
            args.ymin -= extra_lat
            args.ymax += extra_lat
        
        full_height, full_width = bg_img.shape[:2]
        xscale = full_width / 360.0
        yscale = full_height / 180.0
        
        left = (args.xmin + 180) * xscale
        right = (args.xmax + 180) * xscale
        top = (90 - args.ymax) * yscale
        bottom = (90 - args.ymin) * yscale
        
        if 0 <= left < full_width and 0 <= right < full_width and 0 <= top < full_height and 0 <= bottom < full_height:
            bg_img = bg_img[int(top):int(bottom), int(left):int(right)]
        
        extent = [args.xmin, args.xmax, args.ymin, args.ymax]
    
    ax.imshow(bg_img, extent=extent, interpolation='lanczos')
    ax.set_xlim(args.xmin, args.xmax)
    ax.set_ylim(args.ymin, args.ymax)
    ax.set_axis_off()
    
    line_width = (0.09 / 360) * width + (0.09 / 180) * height
    
    def calculate_dot_size(dots_param, width, height, xrange, yrange):
        base_size = (dots_param * min(width / xrange, height / yrange)) ** 2
        return max(10, min(200, base_size * 2))
    
    dot_size = calculate_dot_size(args.dots, width, height, 
                                 args.xmax - args.xmin, 
                                 args.ymax - args.ymin)
    
    for storm in storms:
        if hasattr(args, 'show_names') and args.show_names and len(storm["positions"]) > 0:
            label_pos = storm["positions"][0]
            
            offset_y = (args.ymax - args.ymin) * 0.05
            
            label_text = ax.text(label_pos["lon"], label_pos["lat"] - offset_y, 
                               storm["name"], 
                               color='white', fontsize=8, fontweight='bold',
                               ha='center', va='top', zorder=30)
            label_text.set_path_effects([
                path_effects.Stroke(linewidth=2, foreground='black'),
                path_effects.Normal()
            ])
        
        if len(storm["positions"]) > 1:
            for i in range(len(storm["positions"]) - 1):
                pos1 = storm["positions"][i]
                pos2 = storm["positions"][i+1]
                
                if not args.noextra and (pos1.get("type") == "EXTRATROPICAL" or pos2.get("type") == "EXTRATROPICAL"):
                    continue
                
                ax.plot([pos1["lon"], pos2["lon"]], [pos1["lat"], pos2["lat"]], 
                       color=(1, 1, 1, args.alpha), linewidth=line_width, zorder=10)
        
        if len(storm["positions"]) > 1:
            for i in range(len(storm["positions"]) - 1):
                pos1 = storm["positions"][i]
                pos2 = storm["positions"][i+1]
                
                if args.noextra and (pos1.get("type") == "EXTRATROPICAL" or pos2.get("type") == "EXTRATROPICAL"):
                    continue
                
                ax.plot([pos1["lon"], pos2["lon"]], [pos1["lat"], pos2["lat"]], 
                       color=(1, 1, 1, args.alpha), linewidth=line_width, zorder=10)
        
        lons = []
        lats = []
        colors = []
        sizes = []
        markers = []
        
        for pos in storm["positions"]:
            if args.noextra and pos.get("type") == "EXTRATROPICAL":
                continue
                
            lons.append(pos["lon"])
            lats.append(pos["lat"])
            
            r, g, b = get_color_from_wind(pos["wind"], args.scale)
            colors.append((r, g, b, args.alpha))
            
            if pos.get("type") == "SUBTROPICAL":
                markers.append('s')
                sizes.append(dot_size * 0.60)
            elif pos.get("type") == "EXTRATROPICAL":
                markers.append('^')
                sizes.append(dot_size * 0.70)
            else:
                markers.append('o')
                sizes.append(dot_size)
        
        if lons and lats:
            marker_groups = {}
            for i, marker in enumerate(markers):
                if marker not in marker_groups:
                    marker_groups[marker] = {'lons': [], 'lats': [], 'colors': [], 'sizes': []}
                marker_groups[marker]['lons'].append(lons[i])
                marker_groups[marker]['lats'].append(lats[i])
                marker_groups[marker]['colors'].append(colors[i])
                marker_groups[marker]['sizes'].append(sizes[i])
            
            for marker, data in marker_groups.items():
                ax.scatter(data['lons'], data['lats'], c=data['colors'], 
                          s=data['sizes'], marker=marker, zorder=20, 
                          edgecolor='none', linewidths=0)
                
                ax.set_aspect('equal', adjustable='datalim')
    
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
