# ELGOB
ELGOB (an anagram of globe!) is a tropical cyclone track generator based on [titoxd](https://github.com/titoxd)'s [wptc-track](https://github.com/titoxd/wptc-track) project — written in Python. This software allows you to create high-quality visualizations of weather system tracks using various data sources.

**Note:** ELGOB is a (heavy) work in progress and may not support all features of the original wptc-track project. It is intended for educational and research purposes only.

## Key features
- Generation of tropical cyclone track maps with customizable formatting
- Support for multiple meteorological data formats (HURDAT, HURDAT2, ATCF, JMA, etc.)
- Color customization based on different classification scales (SSHWS, JMA, IMD, etc.)
- Options to filter storms by year, name, ID, or wind intensity
- Ability to set custom or automatic geographical boundaries
- Support for visualizing different storm phases (tropical, extratropical, subtropical)

## Requirements
- Python 3.6+
- Dependencies: matplotlib, numpy

## Installation
```bash
git clone https://github.com/your-username/elgob.git
cd elgob
pip install -r requirements.txt
```

## Basic usage
```bash
cd tracks
python track.py --input EXAMPLE --format hurdat
```

### Common parameters
- `--input`: Input data file
- `--format`: Data format (hurdat, hurdat2, atcf, jma, md, tcr)
- `--year`: Storm year
- `--name`: Storm name
- `--id`: Storm numeric ID
- `--wind`: Filter for minimum wind speed
- `--scale`: Scale to use (SSHWS, JMA, IMD, AUS, MFR, JMADOM)
- `--bg`: Custom background image
- `--res`: Horizontal image resolution
- `--output`: Output file
- `--noextra`: Ignore extratropical portions of tracks
- `--xmin`, `--xmax`, `--ymin`, `--ymax`: Geographic boundaries

## Directory structure
- [`tracks`](tracks): Main Python scripts
- [`data`](data): Background images and data
- [`png`](png): Default output directory for images

## Credits
ELGOB is based on the wptc-track project. Many thanks to titoxd and the contributors for their work on this project.

## License
See the [LICENSE](LICENSE) file for details.
