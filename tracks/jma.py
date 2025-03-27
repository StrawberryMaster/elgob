import os

def read_stormdata_jma(file_path, skipasynoptic):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) < 6:
                continue
            if tokens[0] == "66666":
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': int(tokens[1]) % 100,
                    'year': get_full_year(int(tokens[1]) // 100),
                    'name': tokens[7].strip(),
                    'positions': []
                }
            elif tokens[1] == "002":
                pos = parse_position(tokens, skipasynoptic)
                if pos:
                    storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def get_full_year(two_digit_date):
    if two_digit_date > 50:
        return 1900 + two_digit_date
    else:
        return 2000 + two_digit_date

def parse_position(tokens, skipasynoptic):
    pos = {
        'year': get_full_year(int(tokens[0]) // 1000000),
        'month': (int(tokens[0]) % 1000000) // 10000,
        'day': (int(tokens[0]) % 10000) // 100,
        'hour': int(tokens[0]) % 100,
        'lat': int(tokens[3]) / 10.0,
        'lon': -int(tokens[4]) / 10.0,
        'wind': int(tokens[6]),
        'pres': int(tokens[5]),
        'type': get_storm_type(int(tokens[2]))
    }
    if skipasynoptic and pos['hour'] % 6 != 0:
        return None
    return pos

def get_storm_type(stormtype):
    if stormtype == 6:
        return 'EXTRATROPICAL'
    else:
        return 'TROPICAL'
