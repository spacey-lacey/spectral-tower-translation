from PIL import Image
from decode_char_tiles import hex_to_bytes, process_tile, print_tile

image_path = "../tiles/ascii_odd.png"
char_width = 8
tile_width = 8
tile_height = 13
row_height = 14 # png has 14px rows, so adjust for this



def split_into_tiles(image_path, char_width, tile_width, tile_height, row_height):
    '''
    split an image of characters into individual tiles
    '''
    image = Image.open(image_path).convert("L") # convert to grayscale
    image_width, image_height = image.size

    tiles = []
    for top in range(0, image_height, row_height):
        for left in range(0, image_width, char_width):

            # crop to the current tile
            right = min(left + char_width, image_width)
            bottom = min(top + tile_height, image_height)
            tile = image.crop((left, top, right, bottom))

            tiles.append(tile)

    return tiles


def print_png_tile(tile):
    '''
    print a tile to the terminal for testing purposes
    '''
    pixels = tile.load()
    width, height = tile.size
    for y in range(height):
        string = ""
        for x in range(width):
            pixel = pixels[x, y]
            if pixel == 0:
                string += "██"
            elif pixel == 255:
                string += "  "
        print(string)


def encode_tile(tile, n_row_bytes=2):
    '''
    encode a tile to the game format
    '''
    pixels = tile.load()
    width, height = tile.size
    rows = []

    for row in range(height):
        row_values = []
        for row_byte in range(n_row_bytes):
            row_values.append(0)
            for pixel_bit in range(0, 8, 2):
                x = row_byte * 8 + pixel_bit
                y = row
                pixel1 = pixels[x, y]
                pixel2 = pixels[x + 1, y]

                # black pixels are represented by 1
                if pixel1 == 255 and pixel2 == 255:
                    value = 0 # b"\x00"
                elif pixel1 == 255 and pixel2 == 0:
                    value = 1 # b"\x01"
                elif pixel1 == 0 and pixel2 == 255:
                    value = 2 # b"\x10"
                elif pixel1 == 0 and pixel2 == 0:
                    value = 3 #b"\x11"

                row_values[row_byte] = (row_values[row_byte] << 2) | value

        row_bytes = [row_value.to_bytes() for row_value in row_values]
        rows.append(b"".join(row_ for row_ in row_bytes))

    return rows


def decode_hex_string(hex_string, n_row_bytes=2):
    '''
    read in a string of tile bytes and decode them
    '''
    result = []
    digit_counter = 0
    for row in range(13):
        for row_byte in range(n_row_bytes):
            hex_value = hex_string[digit_counter : digit_counter + 2]
            value = int(hex_value, 16)
            for pixel_bit in range(6, -2, -2):
                pixel_byte = (value >> pixel_bit) & 3

                # kinda gross but at least it prints correctly
                if pixel_byte == 0:
                    pixel_byte = 0x00
                elif pixel_byte == 1:
                    pixel_byte = 0x10
                elif pixel_byte == 2:
                    pixel_byte = 0x01
                elif pixel_byte == 3:
                    pixel_byte = 0x11

                result.append(pixel_byte)

            digit_counter += 2

    return bytes(result)


def tile_to_hex(tile, n_row_bytes=2):
    '''
    the whole shebang
    '''
    rows = encode_tile(tile, n_row_bytes)
    rows = [row.hex() for row in rows]
    return "".join(rows)




if __name__ == "__main__":

    tiles = split_into_tiles(image_path, char_width, tile_width, tile_height)

    for tile in tiles:
        print_png_tile(tile)
        print("")
        tile_hex = tile_to_hex(tile, 1)
        decoded = decode_hex_string(tile_hex, 1)
        print_tile(process_tile(decoded, 8))
        print("")
