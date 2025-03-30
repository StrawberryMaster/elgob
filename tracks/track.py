import argparse
import os
import math
from PIL import Image, ImageDraw
from atcf import read_stormdata_atcf
from hurdat import read_stormdata_hurdat
from hurdat2 import read_stormdata_hurdat2
from jma import read_stormdata_jma
from md import read_stormdata_md
from tcr import read_stormdata_tcr
from scales import SSHWS_ENTRIES, AUS_ENTRIES, IMD_ENTRIES, JMA_ENTRIES, MFR_ENTRIES, JMADOM_ENTRIES

def get_color_from_wind(wind, scale="SSHWS"):
    """
    Corrige o mapeamento de cores com base na intensidade do vento e na escala escolhida.
    Esta função garante que a categoria correta seja atribuída às tempestades.
    
    Args:
        wind: Velocidade do vento
        scale: Escala de classificação (SSHWS, AUS, IMD, JMA, MFR, JMADOM)
        
    Returns:
        Tupla (r, g, b) com os valores de cor na faixa 0-1
    """
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
    parser.add_argument("--extra", type=int, default=0, help="Do not cut off the extratropical portion of the tracks when extra!=0")
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
    return parser.parse_args()

def read_storm_data(args):
    storms = []
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
    img = Image.open(args.bg)
    
    width = args.res
    height = int(width * (args.ymax - args.ymin) / (args.xmax - args.xmin))
    print(f"Image size: {width} x {height}")
    
    if args.xmin is not None and args.xmax is not None and args.ymin is not None and args.ymax is not None:
        full_width, full_height = img.size
        xscale = full_width / 360.0
        yscale = full_height / 180.0
        
        left = (args.xmin + 180) * xscale
        right = (args.xmax + 180) * xscale
        top = (90 - args.ymax) * yscale
        bottom = (90 - args.ymin) * yscale
        
        cropped_img = img.crop((left, top, right, bottom))
        img = cropped_img.resize((width, height), Image.LANCZOS)
    
    draw = ImageDraw.Draw(img, 'RGBA')
    
    line_width = max(2, int(args.lines * min(width, height) / 30))
    
    for storm in storms:
        if len(storm["positions"]) > 1:
            for i in range(len(storm["positions"]) - 1):
                pos1 = storm["positions"][i]
                pos2 = storm["positions"][i+1]
                
                if not args.extra and (pos1.get("type") == "EXTRATROPICAL" or pos2.get("type") == "EXTRATROPICAL"):
                    continue
                
                x1, y1 = get_pos(pos1, img.size, args)
                x2, y2 = get_pos(pos2, img.size, args)
                
                draw_antialiased_line(draw, (x1, y1), (x2, y2), line_width, (255, 255, 255, int(255 * args.alpha)))
        
        for pos in storm["positions"]:
            if not args.extra and pos.get("type") == "EXTRATROPICAL":
                continue
                
            x, y = get_pos(pos, img.size, args)
            
            if 0 <= x < img.width and 0 <= y < img.height:
                r, g, b = get_color_from_wind(pos["wind"], args.scale)
                
                r_int = int(r * 255)
                g_int = int(g * 255)
                b_int = int(b * 255)
                
                dot_radius = args.dots * min(img.width / (args.xmax - args.xmin), 
                                         img.height / (args.ymax - args.ymin))
                
                draw_advanced_antialiased_circle(draw, (x, y), dot_radius, (r_int, g_int, b_int, int(255 * args.alpha)))
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    img.save(args.output)
    print(f"Map generated and saved to {args.output}")

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

def draw_antialiased_circle(draw, center, radius, color):
    x, y = center

    x0, y0 = x - radius, y - radius
    x1, y1 = x + radius, y + radius
    draw.ellipse((x0, y0, x1, y1), fill=color)
    
    for i in range(1, 3):
        r, g, b, a = color
        edge_alpha = int(a * (1.0 - i / 3.0))
        edge_color = (r, g, b, edge_alpha)
        
        outer_radius = radius + i/2.0
        x0, y0 = x - outer_radius, y - outer_radius
        x1, y1 = x + outer_radius, y + outer_radius
        draw.ellipse((x0, y0, x1, y1), fill=edge_color)

def draw_advanced_antialiased_circle(draw, center, radius, color):
    x, y = center
    r, g, b, a = color
    
    x0, y0 = x - radius, y - radius
    x1, y1 = x + radius, y + radius
    draw.ellipse((x0, y0, x1, y1), fill=color)
    
    steps = 5
    for i in range(1, steps + 1):
        edge_alpha = int(a * math.cos((i / (steps + 1)) * (math.pi / 2)))
        edge_color = (r, g, b, edge_alpha)
        
        outer_radius = radius + (i / steps)
        x0, y0 = x - outer_radius, y - outer_radius
        x1, y1 = x + outer_radius, y + outer_radius
        draw.ellipse((x0, y0, x1, y1), fill=edge_color)

def draw_antialiased_line(draw, start, end, width, color):
    x1, y1 = start
    x2, y2 = end
    r, g, b, a = color
    
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    
    dx = x2 - x1
    dy = y2 - y1
    distance = max(1, math.sqrt(dx*dx + dy*dy))

    steps = 3
    
    for i in range(1, steps + 1):
        edge_alpha = int(a * (1.0 - i/steps))
        if edge_alpha <= 0:
            continue
            
        edge_color = (r, g, b, edge_alpha)
        edge_width = width + i
        
        draw.line((x1, y1, x2, y2), fill=edge_color, width=edge_width)

if __name__ == "__main__":
    main()
