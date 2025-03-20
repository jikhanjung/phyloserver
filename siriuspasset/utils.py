import re
from typing import List, Optional, Tuple, Any

def parse_image_filename(filename: str) -> Tuple[str, str, int, Optional[str]]:
    """
    Parse a filename like 'SP-2016-1A-157.JPG' or 'SP-2016-1A-123(water).JPG'
    into components for sorting.
    
    Returns a tuple of (slab_number, specimen_letter, photo_number, remarks)
    example: 'SP-2016-1A-157.JPG' -> ('SP-2016-1', 'A', 157, None)
    example: 'SP-2016-1A-123(water).JPG' -> ('SP-2016-1', 'A', 123, 'water')
    example: 'SP-2016-1-157.JPG' -> ('SP-2016-1', '', 157, None)
    """
    # Get filename without extension and paths
    base_filename = filename.split('/')[-1].split('\\')[-1]

    #remove white space from base_filename
    #base_filename = base_filename.replace(" ", "")
    #print("base_filename: ", base_filename)
    
    # First, extract remarks in parentheses if any
    remarks_match = re.search(r'(\d+)\((.+?)\)', base_filename)
    remarks = ''
    if remarks_match:
        photo_number_str = remarks_match.group(1)
        remarks = remarks_match.group(2)
        # Replace the parts with the photo number only for further parsing
        base_filename = base_filename.replace(f"{photo_number_str}({remarks})", photo_number_str)
    
    # Regular expression to match the pattern SP-YYYY-N[Letter]-Number
    pattern = r'(SP-\d{4}-\d+)([A-Za-z]?)(?:-(\d+))?'
    match = re.search(pattern, base_filename)
    
    if match:
        slab_number = match.group(1)  # SP-2016-1
        specimen_letter = match.group(2) or ''  # A or ''
        photo_number_str = match.group(3) or '0'  # 157 or 0
        
        try:
            photo_number = int(photo_number_str)
        except ValueError:
            photo_number = 0
            
        return (slab_number, specimen_letter, photo_number, remarks)
    
    # If no match, return default values for sorting
    return ('', '', 0, None)

def sort_images_by_filename(images: List[Any]) -> List[Any]:
    """
    Sort a list of SpFossilImage objects based on their filename pattern.
    
    Sorting order:
    1. Slab number (SP-2016-1)
    2. Specimen letter (if present)
    3. Photo number
    4. Remarks (if present)
    """
    # print image filenames
    for img in images:
        print(img.original_path)
    return sorted(images, key=lambda img: parse_image_filename(img.original_path or '')) 