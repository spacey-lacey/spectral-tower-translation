from encode_char_tiles import image_path, char_width, tile_width, tile_height, split_into_tiles, extend_tile_width, encode_tile



def write_tiles(file):
    '''
    add encoded tiles to binary file
    '''

    tiles = split_into_tiles(image_path, char_width, tile_width, tile_height)

    for tile in tiles:
        for copy in range(2):
            rows = encode_tile(tile, n_row_bytes=1)
            file.write(b"".join(rows))




if __name__ == "__main__":

    file_name = "ASCII"

    file = open(file_name, "wb")
    write_tiles(file)
    file.close()

    print("Binary data written to", file_name)
