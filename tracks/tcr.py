import os

def read_stormdata_tcr(file_path):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        targets = ["Date/Time", "Latitude", "Longitude", "Pressure", "Wind Speed", "Stage"]
        targets_found = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if targets_found < len(targets):
                if line == targets[targets_found]:
                    targets_found += 1
                continue
            if storm is None:
                storm = {
                    'id': 1,
                    'name': 'UNNAMED',
                    'positions': []
                }
            if '/' in line:
                pos = {
                    'year': int(line[:4]),
                    'month': int(line[5:7]),
                    'day': int(line[8:10]),
                    'hour': int(line[11:13]),
                    'lat': float(lines[lines.index(line) + 1].strip()),
                    'lon': float(lines[lines.index(line) + 2].strip()),
                    'pres': int(lines[lines.index(line) + 3].strip()),
                    'wind': int(lines[lines.index(line) + 4].strip()),
                    'type': get_storm_type(lines[lines.index(line) + 5].strip())
                }
                storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def get_storm_type(stage):
    if stage in ["hurricane", "tropical storm", "tropical depression"]:
        return "TROPICAL"
    elif stage == "extratropical":
        return "EXTRATROPICAL"
    elif stage in ["low", "remnant low", "tropical wave"]:
        return "LOW"
    elif stage in ["subtropical depression", "subtropical storm"]:
        return "SUBTROPICAL"
    else:
        return "UNKNOWN"
