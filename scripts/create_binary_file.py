from encode_char_tiles import char_width, tile_width, tile_height, split_into_tiles, encode_tile

image_paths = ["../tiles/blocks_even.png", "../tiles/blocks_odd.png"]


def write_tiles(file):
    '''
    add encoded tiles to binary file
    '''

    tiles = []
    for image_path in image_paths:
        tiles.append(split_into_tiles(image_path, char_width, tile_width, tile_height))

    # tile index
    for j in range(len(tiles[0])):
        # tileset index
        for i in range(2):
            rows = encode_tile(tiles[i][j], n_row_bytes=1)
            file.write(b"".join(rows))




if __name__ == "__main__":

    file_name = "ASCII"

    file = open(file_name, "wb")
    write_tiles(file)
    file.close()

    print("Binary data written to", file_name)
