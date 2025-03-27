import os

def read_stormdata_hurdat2(file_path, skipasynoptic):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tokens = line.split(',')
            if len(tokens) < 4:
                continue
            if is_header_line(tokens):
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': int(tokens[0][2:4]),
                    'name': tokens[1].strip(),
                    'year': int(tokens[0][4:8]),
                    'positions': []
                }
            else:
                pos = parse_position(tokens, skipasynoptic)
                if pos:
                    storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def is_header_line(tokens):
    return tokens[0][0].isalpha() and len(tokens) == 4

def parse_position(tokens, skipasynoptic):
    pos = {
        'year': int(tokens[0][:4]),
        'month': int(tokens[0][4:6]),
        'day': int(tokens[0][6:8]),
        'hour': int(tokens[1][:2]),
        'lat': float(tokens[4][:-1]) * (1 if tokens[4][-1] == 'N' else -1),
        'lon': float(tokens[5][:-1]) * (1 if tokens[5][-1] == 'E' else -1),
        'wind': int(tokens[6]),
        'pres': int(tokens[7]),
        'type': get_storm_type(tokens[3])
    }
    if skipasynoptic and pos['hour'] % 6 != 0:
        return None
    return pos

def get_storm_type(token):
    if token in ['TD', 'TS', 'TY', 'ST', 'TC', 'HU']:
        return 'TROPICAL'
    elif token in ['SD', 'SS']:
        return 'SUBTROPICAL'
    elif token == 'EX':
        return 'EXTRATROPICAL'
    elif token in ['LO', 'WV', 'DB']:
        return 'LOW'
    else:
        return 'UNKNOWN'
