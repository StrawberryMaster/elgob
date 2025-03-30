import os

def read_stormdata_hurdat2(file_path, skipasynoptic=True):
    storms = []
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return storms
        
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
            storm = None
            for i in range(len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                
                if line.startswith("AL") or line.startswith("EP") or line.startswith("CP") or line.startswith("MT"):
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    if storm is not None and len(storm["positions"]) > 0:
                        storms.append(storm)
                    
                    storm_id = parts[0].strip()
                    storm_name = parts[1].strip()
                    
                    try:
                        year = int(storm_id[-4:])
                    except ValueError:
                        year = 0
                    
                    try:
                        numeric_id = int(storm_id[2:4])
                    except ValueError:
                        numeric_id = 0
                    
                    storm = {
                        "id": numeric_id,
                        "name": storm_name,
                        "year": year,
                        "positions": []
                    }
                
                elif storm is not None and ("/" in line or (len(line) > 10 and line[0:8].isdigit())):
                    parts = line.split(',')
                    if len(parts) < 6:
                        continue
                    
                    date_str = parts[0].strip()
                    if "/" in date_str:
                        date_parts = date_str.split('/')
                        if len(date_parts) == 3:
                            month = int(date_parts[0])
                            day = int(date_parts[1])
                            year = int(date_parts[2])
                        else:
                            continue
                    else:
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                    
                    hour_str = parts[1].strip()
                    if hour_str.endswith("Z"):
                        hour = int(hour_str[0:2])
                    else:
                        hour = int(hour_str[0:2])
                    
                    system_type = parts[3].strip()
                    
                    lat_str = parts[4].strip()
                    lon_str = parts[5].strip()
                    
                    if lat_str.endswith('N') or lat_str.endswith('S'):
                        lat_value = float(lat_str[:-1])
                        if lat_str.endswith('S'):
                            lat_value = -lat_value
                    else:
                        lat_value = float(lat_str)
                    
                    if lon_str.endswith('W') or lon_str.endswith('E'):
                        lon_value = float(lon_str[:-1])
                        if lon_str.endswith('W'):
                            lon_value = -lon_value
                    else:
                        lon_value = float(lon_str)
                    
                    wind = int(parts[6].strip()) if len(parts) > 6 and parts[6].strip() else 0
                    pressure = int(parts[7].strip()) if len(parts) > 7 and parts[7].strip() else 0
                    
                    storm_type = map_storm_type(system_type)
                    
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
            
            if storm is not None and len(storm["positions"]) > 0:
                storms.append(storm)
    
    except Exception as e:
        print(f"Error processing file: {e}")
    
    print(f"Processed {len(storms)} storms from {file_path}")
    return storms

def map_storm_type(type_code):
    tropical_codes = ['HU', 'TS', 'TD']
    extratropical_codes = ['EX']
    subtropical_codes = ['SD', 'SS']
    low_codes = ['LO', 'WV', 'DB']
    
    type_code = type_code.upper()
    
    if type_code in tropical_codes:
        return 'TROPICAL'
    elif type_code in extratropical_codes:
        return 'EXTRATROPICAL'
    elif type_code in subtropical_codes:
        return 'SUBTROPICAL'
    elif type_code in low_codes:
        return 'LOW'
    else:
        return 'UNKNOWN'
