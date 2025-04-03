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
            
            tokens = [token.strip() for token in line.split(',')]
            
            if len(tokens) < 9:
                continue
                
            if storm is None or tokens[1] != storm['id']:
                if storm is not None:
                    storms.append(storm)
                storm = {
                    'id': tokens[1].strip(),
                    'name': tokens[27].strip() if len(tokens) > 27 and tokens[27].strip() else 'UNNAMED',
                    'positions': []
                }
            
            try:
                lat_value = float(tokens[6][:-1]) / 10.0 if tokens[6] and len(tokens[6]) > 1 else 0.0
                lat_dir = tokens[6][-1] if tokens[6] and len(tokens[6]) > 0 else 'N'
                lat = lat_value * (1 if lat_dir == 'N' else -1)
                
                lon_value = float(tokens[7][:-1]) / 10.0 if tokens[7] and len(tokens[7]) > 1 else 0.0
                lon_dir = tokens[7][-1] if tokens[7] and len(tokens[7]) > 0 else 'E'
                lon = lon_value * (1 if lon_dir == 'E' else -1)
                
                storm_type_token = ''
                if len(tokens) > 10 and tokens[10].strip():
                    storm_type_token = tokens[10].strip()
                
                pos = {
                    'year': int(tokens[2][:4]) if len(tokens[2]) >= 4 else 0,
                    'month': int(tokens[2][4:6]) if len(tokens[2]) >= 6 else 0,
                    'day': int(tokens[2][6:8]) if len(tokens[2]) >= 8 else 0,
                    'hour': int(tokens[2][8:10]) if len(tokens[2]) >= 10 else 0,
                    'lat': lat,
                    'lon': lon,
                    'wind': int(tokens[8]) if tokens[8].strip() and tokens[8].strip().isdigit() else 0,
                    'pres': int(tokens[9]) if len(tokens) > 9 and tokens[9].strip() and tokens[9].strip().isdigit() else 0,
                    'type': get_storm_type(storm_type_token)
                }
                
                if skipasynoptic and pos['hour'] % 6 != 0:
                    continue
                    
                storm['positions'].append(pos)
            except Exception as e:
                print(f"Zoinks! Error while processing line: {line}")
                print(f"Actual error: {e}")
                
        if storm is not None:
            storms.append(storm)
    return storms

def get_storm_type(token):
    if token in ['TD', 'TS', 'TY', 'ST', 'TC', 'HU', 'XX']:
        return 'TROPICAL'
    elif token in ['SD', 'SS']:
        return 'SUBTROPICAL'
    elif token in ['EX', 'MD', 'IN', 'DS', 'LO', 'WV', 'ET', 'DB']:
        return 'EXTRATROPICAL'
    else:
        return 'TROPICAL'
