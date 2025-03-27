import os

def read_stormdata_md(file_path):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if is_header1_line(line):
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': 1,
                    'name': line.strip(),
                    'year': 0,
                    'positions': []
                }
            elif is_header2_line(line):
                continue
            else:
                pos = parse_position(line)
                storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def is_header1_line(line):
    return line[0].isalpha()

def is_header2_line(line):
    return line[4].isalpha()

def parse_position(line):
    pos = {
        'lat': float(line[31:36].strip()),
        'lon': float(line[22:28].strip()),
        'wind': int(line[37:41].strip()),
        'pres': int(line[45:50].strip()),
        'type': 'TROPICAL'
    }
    return pos
