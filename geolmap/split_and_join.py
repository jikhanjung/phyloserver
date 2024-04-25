def split_file(file_path, chunk_size=99000000):  # 100MB in bytes 
    with open(file_path, 'rb') as infile:
        chunk_num = 0
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                break
            with open(f'output_chunk_{chunk_num}.bin', 'wb') as outfile:
                outfile.write(chunk)
            chunk_num += 1

def join_file(file_base_name, output_file, num_chunks):
    """ Joins split binary file chunks into a single output file.

    Args:
        file_base_name (str): The base name of the split files (e.g., 'chunk_').
        output_file (str): The path to the desired output file.
        num_chunks (int): The number of split chunks to join.
    """

    with open(output_file, 'wb') as outfile:
        for i in range(num_chunks):
            chunk_filename = f'{file_base_name}{i}.bin'  # Assuming chunks are named like chunk_0.bin, chunk_1.bin...
            with open(chunk_filename, 'rb') as infile:
                outfile.write(infile.read())

#split_file('geolmap/map_tiles.zip') 
join_file('geolmap/output_chunk_', 'geolmap/map_tiles_joined.zip', 4)