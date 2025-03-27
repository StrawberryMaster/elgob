import os

def read_stormdata_hurdat(file_path):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if is_header_line(line):
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': int(line[22:24]),
                    'name': line[35:].strip(),
                    'year': int(line[12:16]),
                    'positions': []
                }
            else:
                pos = parse_position(line)
                storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def is_header_line(line):
    return line[11] == '/'

def parse_position(line):
    pos = {
        'month': int(line[6:8]),
        'day': int(line[9:11]),
        'hour': 0,
        'lat': int(line[12:16]) / 10.0,
        'lon': int(line[17:21]) / 10.0,
        'wind': int(line[22:25]),
        'pres': int(line[26:30]),
        'type': get_storm_type(line[0])
    }
    return pos

def get_storm_type(char):
    if char in ['*', 'D', 'd']:
        return 'TROPICAL'
    elif char in ['E', 'e', 'X', 'x']:
        return 'EXTRATROPICAL'
    elif char in ['S', 's']:
        return 'SUBTROPICAL'
    elif char in ['L', 'l', 'W', 'w']:
        return 'LOW'
    else:
        return 'UNKNOWN'
