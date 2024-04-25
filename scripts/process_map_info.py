import re

def split_dms_regex(dms_str, direction='N'):
    """Splits a coordinate string in DMS format into degrees, minutes, and seconds using regular expressions.

    Args:
        dms_str (str): The coordinate string in DMS format (e.g., "34°50'12"N").

    Returns:
        tuple: A tuple containing degrees (float), minutes (float), and seconds (float).
    """

    pattern = r"""
        (?P<degrees>\d+)  # Match one or more digits for degrees
        °                 # Match the degree symbol
        (?:               # Optional non-capturing group for minutes and seconds
          (?P<minutes>\d+)  # Match one or more digits for minutes
          '                 # Match the single quote symbol
          (?P<seconds>\d+(?:\.\d+)?)  # Match digits and optional decimal for seconds
        )?                # Make the minutes and seconds group optional
    """

    match = re.search(pattern, dms_str, re.VERBOSE)

    if match:
        degrees = float(match.group('degrees'))
        minutes = float(match.group('minutes')) if match.group('minutes') else 0
        seconds = float(match.group('seconds')) if match.group('seconds') else 0
        decimal = degrees + minutes / 60 + seconds / 3600
        if direction.upper() in ('S', 'W'):  # Negative for South and West
            decimal *= -1        
        return degrees, minutes, seconds, decimal
    else:
        raise ValueError("Invalid DMS format")

# read excel file
import pandas as pd
import numpy as np
df = pd.read_excel('geolmap/rose_map_data.xlsx')
#print(df)
region_info = []
# for every row, create a hash of the row
cell_coords = { 'x': {}, 'y': {} }


for index, row in df.iterrows():
    #print(row['도폭이름'], row['row'], row['col'], row['rowspan'], row['colspan'], row['위도'], row['경도'])
    print(row['도폭이름'], row['row'], row['col'], row['rowspan'], row['colspan'], row['위도'], row['경도'])
    # if the latitude or longitude is not a number as imported through pandas, set it to None
    latitude = row['위도']
    longitude = row['경도']
    print(latitude, longitude)
    if isinstance(row['위도'],float):
        latitude = None
    else:
        d, m, s, latitude = split_dms_regex(row['위도'])
    if isinstance(row['경도'],float):
    #if row['경도'].isna():
        longitude = None
    else:
        d, m, s, longitude = split_dms_regex(row['경도'])
    row_num = int(row['row'])
    col_num = int(row['col'])

    if latitude:
        print(row_num,latitude)
        if row_num not in cell_coords['y']:
            cell_coords['y'][row_num] = []
        cell_coords['y'][row_num].append(latitude)
    if longitude:
        if col_num not in cell_coords['x']:
            cell_coords['x'][col_num] = []
        cell_coords['x'][col_num].append(longitude)

        
    entry = {'name': row['도폭이름'], 'row': row['row'], 'col': row['col'], 'rowspan': row['rowspan'], 'colspan': row['colspan']}#, 'lat': latitude, 'lon': longitude} 
    print(entry)
    region_info.append(entry)

key_list = list(cell_coords['x'].keys())
key_list.sort()
for key in key_list:
    print('x', key, np.mean(cell_coords['x'][key]))
max_x_idx = max(key_list)
min_x_idx = min(key_list)

key_list = list(cell_coords['y'].keys())
key_list.sort()
for key in key_list:
    print('y', key, np.mean(cell_coords['y'][key]))

max_x_coords = np.mean(cell_coords['x'][max_x_idx])
min_x_coords = np.mean(cell_coords['x'][min_x_idx])

max_y_idx = max(key_list)
min_y_idx = min(key_list)
max_y_coords = np.mean(cell_coords['y'][max_y_idx])
min_y_coords = np.mean(cell_coords['y'][min_y_idx])

# get average coord diff for x and y
x_coords_diff = max_x_coords - min_x_coords
x_idx_diff = max_x_idx - min_x_idx
y_coords_diff = max_y_coords - min_y_coords
y_idx_diff = max_y_idx - min_y_idx

x_diff = x_coords_diff / x_idx_diff
y_diff = y_coords_diff / y_idx_diff

print('x coords diff:', max_x_coords - min_x_coords, 'x idx diff', max_x_idx - min_x_idx)
print('y coords diff:', max_y_coords - min_y_coords, 'y idx diff', max_y_idx - min_y_idx)
print('x diff:', x_diff, 'y diff:', y_diff)

x_0 = min_x_coords - x_diff * min_x_idx
y_0 = min_y_coords - y_diff * min_y_idx
print('x_0:', x_0, 'y_0:', y_0)

coords_basis = {'x_0': x_0, 'y_0': y_0, 'x_diff': x_diff, 'y_diff': y_diff}

map_info = {'regions': region_info, 'coords_basis': coords_basis}

import json
with open('geolmap/map_info.json', 'w') as f:
    json.dump(map_info, f)
#with open('geolmap/coords_basis.json', 'w') as f:
#    json.dump(coords_basis, f)

# Example usage (same as before)
if False:
    coordinates = ["34°", "127°44'51\"N", "127°44'51\"S", "35°12'52\"W" , "35°12'52\"E"]

    for coord in coordinates:
        if coord[-1] in ('E','W','N', 'S'):
            deg, min, sec, dec = split_dms_regex(coord, direction=coord[-1])
            #deg, min, sec, dec = split_dms_regex(coord)
            print(f"Degrees: {deg}, Minutes: {min}, Seconds: {sec} => {dec} ")    