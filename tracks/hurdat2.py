import os

TYPE_MAPPINGS = {
    'HU': 'TROPICAL', 'TS': 'TROPICAL', 'TD': 'TROPICAL',
    'EX': 'EXTRATROPICAL',
    'SD': 'SUBTROPICAL', 'SS': 'SUBTROPICAL',
    'LO': 'LOW', 'WV': 'LOW', 'DB': 'LOW',
}

def read_stormdata_hurdat2(file_path, skipasynoptic=True):
    storms = []
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return storms
        
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
            storm = None
            i = 0
            total_lines = len(lines)
            
            while i < total_lines:
                line = lines[i].strip()
                i += 1
                
                if not line:
                    continue
                
                if any(line.startswith(prefix) for prefix in ('AL', 'EP', 'CP', 'MT')):
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    if storm is not None and storm["positions"]:
                        storms.append(storm)
                    
                    storm_id = parts[0].strip()
                    storm_name = parts[1].strip()
                    
                    year = int(storm_id[-4:]) if storm_id[-4:].isdigit() else 0
                    numeric_id = int(storm_id[2:4]) if storm_id[2:4].isdigit() else 0
                    
                    storm = {
                        "id": numeric_id,
                        "name": storm_name,
                        "year": year,
                        "positions": []
                    }
                
                elif storm is not None and line and ('/' in line or line[0:8].isdigit()):
                    parts = line.split(',')
                    if len(parts) < 6:
                        continue
                    
                    date_str = parts[0].strip()
                    
                    if '/' in date_str:
                        month, day, year = map(int, date_str.split('/'))
                    else:
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                    
                    hour_str = parts[1].strip()
                    hour = int(hour_str[0:2])
                    
                    system_type = parts[3].strip()
                    
                    lat_str = parts[4].strip()
                    is_south = lat_str.endswith('S')
                    lat_value = float(lat_str[:-1] if lat_str[-1] in 'NS' else lat_str)
                    if is_south:
                        lat_value = -lat_value

                    
                    lon_str = parts[5].strip()
                    is_west = lon_str.endswith('W')
                    lon_value = float(lon_str[:-1] if lon_str[-1] in 'EW' else lon_str)
                    if is_west:
                        lon_value = -lon_value
                    
                    wind = int(parts[6].strip()) if len(parts) > 6 and parts[6].strip() else 0
                    pressure = int(parts[7].strip()) if len(parts) > 7 and parts[7].strip() else 0
                    
                    storm_type = TYPE_MAPPINGS.get(system_type.upper(), 'UNKNOWN')
                    
                    pos = {
                        "month": month,
                        "day": day,
                        "hour": hour,
                        "lat": lat_value,
                        "lon": lon_value,
                        "wind": wind,
                        "pres": pressure,
                        "type": storm_type
                    }
                    
                    storm["positions"].append(pos)
            
            if storm is not None and storm["positions"]:
                storms.append(storm)
    
    except Exception as e:
        print(f"Error processing file: {e}")
    
    print(f"Processed {len(storms)} storms from {file_path}")
    return storms

def map_storm_type(type_code):
    return TYPE_MAPPINGS.get(type_code.upper(), 'UNKNOWN')
