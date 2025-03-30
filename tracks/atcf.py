import os

def read_stormdata_atcf(file_path, skipasynoptic):
    storms = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        storm = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tokens = line.split(',')
            if len(tokens) < 9:
                continue
            if storm is None or tokens[1] != storm['id']:
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': tokens[1],
                    'name': tokens[27] if len(tokens) > 27 else 'UNNAMED',
                    'positions': []
                }
            pos = {
                'year': int(tokens[2][:4]),
                'month': int(tokens[2][4:6]),
                'day': int(tokens[2][6:8]),
                'hour': int(tokens[2][8:10]),
                'lat': float(tokens[6][:-1]) / 10.0 * (1 if tokens[6][-1] == 'N' else -1),
                'lon': float(tokens[7][:-1]) / 10.0 * (1 if tokens[7][-1] == 'E' else -1),
                'wind': int(tokens[8]),
                'pres': int(tokens[9]) if len(tokens) > 9 else None,
                'type': get_storm_type(tokens[10]) if len(tokens) > 10 else 'TROPICAL'
            }
            if skipasynoptic and pos['hour'] % 6 != 0:
                continue
            storm['positions'].append(pos)
        if storm is not None:
            storms.append(storm)
    return storms

def get_storm_type(token):
    if token in ['TD', 'TS', 'TY', 'ST', 'TC', 'HU']:
        return 'TROPICAL'
    elif token in ['SD', 'SS']:
        return 'SUBTROPICAL'
    elif token == 'EX':
        return 'EXTRATROPICAL'
    elif token in ['LO', 'WV', 'MD', 'DB']:
        return 'LOW'
    else:
        return 'TROPICAL'
