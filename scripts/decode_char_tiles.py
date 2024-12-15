import re

# path to exe file from the rom
# all of the tile data is in here
rom_path = "../rom/SLPS_004.76"

# "addresses," aka positions in rom
text_color_table = 99332
chunk_table_nonkanji = 514412
chunk_table_forbidden = 514488
chunk_table_kanji = 514564
tile_table_nonkanji = 514840 
tile_table_kanji = 528464


def remap_shift_jis_char(shift_jis_code, rom_file):
    '''
    transforms a shift jis code into some kind of index number used by the rom
    transliterated from ghidra pseudocode (with some cleanup)
    '''
    code_bytes = shift_jis_code.to_bytes(2, byteorder="big")
    byte1 = code_bytes[0]
    byte2 = code_bytes[1]

    # before shift jis tables
    if byte1 < 0x81:
        return -1

    # shift jis symbol table
    elif byte1 == 0x81:
        if byte2 < 0x7f: # "normal" punctuation
            table_chunk_index = 0
        elif byte2 < 0xad: # math symbols and shapes
            table_chunk_index = 1
        elif byte2 < 0xc0: # math cup symbols
            table_chunk_index = 2
        elif byte2 < 0xcf: # more math symbols
            table_chunk_index = 3
        elif byte2 < 0xe9: # even more math symbols, for your vector calculus needs
            table_chunk_index = 4
        elif byte2 < 0xf8: # random symbols
            table_chunk_index = 5
        elif byte2 == 0xfc: # the circle
            table_chunk_index = 6
        else: # invalid
            return -1

    # latin and hiragana
    elif byte1 == 0x82:
        if byte2 < 0x59: # numbers
            table_chunk_index = 7
        elif byte2 < 0x7a: # capital latin
            table_chunk_index = 8
        elif byte2 < 0x9b: # lowercase latin
            table_chunk_index = 9
        elif byte2 < 0xf2: # hiragana
            table_chunk_index = 10
        else:
            return -1

    # katakana and greek
    elif byte1 == 0x83:
        if byte2 < 0x7f: # katakana 1
            table_chunk_index = 0xb
        elif byte2 < 0x97: # katakana 2
            table_chunk_index = 0xc
        elif byte2 < 0xb7: # capital greek
            table_chunk_index = 0xd
        elif byte2 < 0xd7: # lowercase greek
            table_chunk_index = 0xe
        else:
            return -1

    # cyrillic and box drawing
    elif byte1 == 0x84:
        if byte2 < 0x61: # capital cyrillic
            table_chunk_index = 0xf
        elif byte2 < 0x7f: # lowercase cyrillic 1
            table_chunk_index = 0x10
        elif byte2 < 0x92: # lowercase cyrillic 2
            table_chunk_index = 0x11
        elif byte2 < 0xbf: # box drawing
            table_chunk_index = 0x12
        else:
            table_chunk_index = 0 # why not return -1?  who knows

    # forbidden tables
    # deceptively complex—none of these are in the game
    elif byte1 == 0x85:
        if byte2 < 0x45:
            table_chunk_index = 0
        elif byte2 == 0x46:
            table_chunk_index = 1
        elif byte2 == 0x4b:
            table_chunk_index = 2
        elif byte2 < 0x50:
            table_chunk_index = 3
        elif byte2 < 0x5c:
            table_chunk_index = 4
        elif byte2 < 0xad:
            table_chunk_index = 5
        elif byte2 < 0xbc:
            table_chunk_index = 6
        else:
            return -1
    elif byte1 == 0x86:
        if byte2 < 0x42:
            table_chunk_index = 7
        elif byte2 == 0x43:
            table_chunk_index = 8
        elif byte2 == 0x45:
            table_chunk_index = 9
        elif byte2 < 0x49:
            table_chunk_index = 10
        elif byte2 < 0x4d:
            table_chunk_index = 0xb
        elif byte2 < 0x50:
            table_chunk_index = 0xc
        elif byte2 < 0x70:
            table_chunk_index = 0xd
        elif byte2 < 0xb7:
            table_chunk_index = 0xe
        elif byte2 < 0xf5:
            table_chunk_index = 0xf
        else:
            return -1

    # second symbols table, but these tiles aren't in the game either
    elif byte1 == 0x87:
        if byte2 < 0x5b:
            table_chunk_index = 0x10
        elif byte2 < 0x63:
            table_chunk_index = 0x11
        elif byte2 < 0x96:
            table_chunk_index = 0x12
        else:
            return -1

    # kanji
    elif byte1 < 0x99:
        if byte2 == 0x7f or (byte2 < 0x9f and byte1 == 0x88) or byte2 > 0xfc:
            return -1
        else:
            table_chunk_index = byte1 - 0x88

    # after shift jis tables
    else:
        return -1

    # prepare to get offset
    i = 4 * table_chunk_index

    # nonkanji
    if 0x81 <= byte1 <= 0x84:
        chunk_offset = get_int_from_file(chunk_table_nonkanji + i + 2, 2, rom_file)
        adjusted_code = shift_jis_code - get_int_from_file(chunk_table_nonkanji + i, 2, rom_file)

    # forbidden
    elif 0x85 <= byte1 <= 0x87:
        chunk_offset = get_int_from_file(chunk_table_forbidden + i + 2, 2, rom_file)
        adjusted_code = shift_jis_code - get_int_from_file(chunk_table_forbidden + i, 2, rom_file)

    # kanji
    else:
        chunk_offset = get_int_from_file(chunk_table_kanji + i + 2, 2, rom_file)
        adjusted_code = shift_jis_code - get_int_from_file(chunk_table_kanji + i, 2, rom_file)

        # correct for unused shift jis codes
        # this is so gross but i can't come up with a more clever way
        if byte1 >= 0x89 and byte2 > 0x7f:
            adjusted_code -= 1
        if byte1 >= 0x8a:
            adjusted_code -= get_weird_kanji_offset(byte1)

    return adjusted_code + chunk_offset


def get_int_from_file(position, n_bytes, file):
    '''
    return an int from some bytes at the specified position in the file
    '''
    file.seek(position)
    value = file.read(n_bytes)
    return int.from_bytes(value, byteorder="little")


def get_weird_kanji_offset(byte1):
    '''
    calculate strange offset for kanji tables
    '''
    base_value = 0x43
    pairs = (byte1 - 0x8a) // 2
    odd_offset = (byte1 - 0x8a) % 2
    return base_value + pairs * 0x44 + odd_offset


def decode_shift_jis(shift_jis_code):
    '''
    print japanese character corresponding to given shift jis code (if one exists)
    '''
    try:
        shift_jis_bytes = shift_jis_code.to_bytes(2, byteorder="big")
        return shift_jis_bytes.decode("shift_jis")
    except (UnicodeDecodeError, OverflowError):
        return ""


def get_char_tile_start_address(shift_jis_code, rom_file):
    '''
    find the first byte of the tile to be decoded
    each tile is 13 rows with 2 bytes per row, hence 0x1a (26)
    '''
    remapped_shift_jis = remap_shift_jis_char(shift_jis_code, rom_file)

    if shift_jis_code < 0x8800:
        tile_table_base = tile_table_nonkanji
    else:
        tile_table_base = tile_table_kanji

    return tile_table_base + 0x1a * remapped_shift_jis


def read_in_char_string(shift_jis_bytestring, rom_file, color_index=0):
    '''
    read in a string of shift_jis bytes and get the decoded tiles as binary
    obvs we need the rom for this
    '''
    i = 0 # current char index
    result = []
    color_offset = 4 * color_index

    while i < len(shift_jis_bytestring) and shift_jis_bytestring[i] != 0:
        shift_jis_code = int.from_bytes(shift_jis_bytestring[i:i+2], byteorder="big")
        address = get_char_tile_start_address(shift_jis_code, rom_file)

        for row in range(13):
            for row_byte in range(2):
                value = get_int_from_file(address, 1, rom_file)
                for pixel_bit in range(6, -2, -2):
                    pixel_bit_index = (value >> pixel_bit) & 3 # magic
                    pixel_bit_index = pixel_bit_index + text_color_table + color_offset
                    pixel_bits = get_int_from_file(pixel_bit_index, 1, rom_file)
                    result.append(pixel_bits)

                address += 1
        i += 2

    return bytes(result)


def hex_to_bytes(hex_string):
    '''
    convert a string of hex numbers into a bytestring
    '''
    hex_string = hex_string.replace(" ", "").replace("\n", "").replace("\r", "")
    return bytes.fromhex(hex_string)


def split_into_words(bytestring):
    '''
    split a bytestring into a list of 4-byte words
    '''
    return [bytestring[i:i + 4] for i in range(0, len(bytestring), 4)]


def reverse_endianness(bytestring):
    return bytestring[::-1]


def swap_and_concatenate_words(words):
    '''
    each row consists of 2 bytes that must be swapped
    then concatenated bc why not
    '''
    rows = []
    for i in range(0, len(words), 2):
        rows.append(words[i + 1] + words[i]) # concatenate
    return rows


def get_reversed_hex_string(bytestring):
    hex_string = bytestring.hex()
    return hex_string[::-1]


def process_tile_hex(tile_hex_string):
    byte_string = hex_to_bytes(hex_string)
    return process_tile(byte_string)


def process_tile(byte_string):
    '''
    read in bytestring for one tile (2 bytes)
    return hex representation of rows
    '''
    words = split_into_words(byte_string)
    words = [reverse_endianness(word) for word in words]
    rows = swap_and_concatenate_words(words)
    hex_rows = [get_reversed_hex_string(row) for row in rows]
    return hex_rows


def print_tile(hex_rows):
    '''
    print tile with nonzero pixels as blocks and zeros as spaces
    '''
    for row in hex_rows:
        row = re.sub(r"[1-9a-f]", "██", row)
        print(row.replace("0", "  "))




if __name__ == "__main__":
    '''
    attempt to print all tiles in the shift_jis range, even the ones that don't exist)
    '''
    rom_file = open(rom_path, "rb")

    for code in range(0x8140, 0x9900):
        print(hex(code), decode_shift_jis(code))
        code_bytes = code.to_bytes(2, byteorder="big")
        tile_bytes = read_in_char_string(code_bytes, rom_file, color_index=2)
        print_tile(process_tile(tile_bytes))
        print("")

    rom_file.close()
