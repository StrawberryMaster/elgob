import argparse
import os
from PIL import Image, ImageDraw
from atcf import read_stormdata_atcf
from hurdat import read_stormdata_hurdat
from hurdat2 import read_stormdata_hurdat2
from jma import read_stormdata_jma
from md import read_stormdata_md
from tcr import read_stormdata_tcr
from scales import get_color

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
    return storms

def generate_track_map(storms, args):
    img = Image.open(args.bg)
    draw = ImageDraw.Draw(img)
    for storm in storms:
        for pos in storm["positions"]:
            x, y = get_pos(pos, img.size, args)
            r, g, b = get_color(pos, args.scale)
            draw.ellipse((x - args.dots, y - args.dots, x + args.dots, y + args.dots), fill=(r, g, b, int(args.alpha * 255)))
    img.save(args.output)
    print(f"Track map generated and saved to {args.output}")

def get_pos(pos, img_size, args):
    x = (pos["lon"] - args.xmin) / (args.xmax - args.xmin) * img_size[0]
    y = (args.ymax - pos["lat"]) / (args.ymax - args.ymin) * img_size[1]
    return x, y

def main():
    args = parse_args()
    print("Reading storm data...")
    storms = read_storm_data(args)
    print("Generating track map...")
    generate_track_map(storms, args)
    print("Track map generation completed.")

if __name__ == "__main__":
    main()
