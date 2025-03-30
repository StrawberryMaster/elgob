import os

def read_stormdata_hurdat(file_path):
    storms = []
    
    if not os.path.exists(file_path):
        print(f"Zoinks! File {file_path} not found!")
        return storms
        
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            storm = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if '/' in line and len(line) > 35:  # header line
                    if storm is not None:
                        storms.append(storm)
                    
                    # extract 
                    parts = line.split(',')
                    storm_id = parts[0].strip()
                    storm_name = parts[1].strip()
                    
                    # extract year from the storm ID
                    date_parts = parts[3].strip().split('/')
                    year = int(date_parts[2])
                    
                    # extract storm ID)
                    try:
                        numeric_id = int(storm_id[2:4])
                    except ValueError:
                        numeric_id = 0
                    
                    storm = {
                        'id': numeric_id,
                        'name': storm_name,
                        'year': year,
                        'positions': []
                    }
                elif storm is not None:
                    # data line format:
                    # 06/25/1851, 18Z, , LO, 28.0N, 94.8W,  0, , , 0, , , 0, , 0, 0, , 0, , 
                    parts = line.split(',')
                    
                    if len(parts) < 10:
                        continue
                        
                    date_parts = parts[0].strip().split('/')
                    month = int(date_parts[0])
                    day = int(date_parts[1])
                    
                    # hour (ex: 18Z)
                    hour_str = parts[1].strip()
                    hour = int(hour_str[0:2]) if hour_str else 0
                    
                    # storm type (ex: LO, HU, TS)
                    system_type = parts[3].strip()
                    
                    # latitude and longitude
                    lat_str = parts[4].strip()
                    lon_str = parts[5].strip()
                    
                    lat_value = float(lat_str[:-1]) if lat_str else 0
                    lon_value = float(lon_str[:-1]) if lon_str else 0
                    
                    # adjust latitude and longitude based on N/S and E/W
                    if lat_str.endswith('S'):
                        lat_value = -lat_value
                    if lon_str.endswith('W'):
                        lon_value = -lon_value
                    
                    # wind and pressure
                    wind = int(parts[6].strip()) if parts[6].strip() else 0
                    pressure = int(parts[7].strip()) if parts[7].strip() else 0
                    
                    storm_type = map_storm_type(system_type)
                    
                    pos = {
                        'month': month,
                        'day': day,
                        'hour': hour,
                        'lat': lat_value,
                        'lon': lon_value,
                        'wind': wind,
                        'pres': pressure,
                        'type': storm_type
                    }
                    
                    storm['positions'].append(pos)
                    
            if storm is not None:
                storms.append(storm)
    except Exception as e:
        print(f"Error processing file: {e}")
    
    print(f"Processed {len(storms)} storms from file {file_path}")
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
