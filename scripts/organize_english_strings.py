from pathlib import Path
import pandas as pd
import sys
import re

from convert_ghidra_csv import get_dataframe, get_input_csv_name


def encode_ascii(ascii_string):
    '''
    encode an ascii string
    if the string has an odd number of characters, add a trailing space
    then add zero terminators until the number of bytes is a multiple of 4
    '''
    # if there is no string
    if ascii_string == "":
        return ""

    # remove non-ascii characters before encoding
    ascii_string = replace_non_ascii_characters(ascii_string)

    # encode and do regex replacement
    byte_string = encode_and_regex_replace(ascii_string)

    # check number of characters
    if len(byte_string) % 2 != 0:
        byte_string += b"\x20"

    # add zeros
    byte_string += b"\x00"
    while len(byte_string) % 4 != 0:
        byte_string += b"\x00"

    return byte_string


def replace_non_ascii_characters(ascii_string):
    '''
    remove automatic non-ascii characters before encoding
    '''
    # replace "smart" apostrophe
    ascii_string = ascii_string.replace("’", "'")

    return ascii_string


def encode_and_regex_replace(ascii_string):
    '''
    replace spaces before odd-indexed capitals
    '''
    byte_array = bytearray(ascii_string.encode("ascii"))

    for match in re.finditer(r" ([A-Z])", ascii_string):
        space_index = match.start()
        # only need to replace spaces before odd-index capitals
        if space_index % 2 == 0:
            ascii_code = byte_array[space_index + 1]
            byte_array[space_index] = ascii_code - 0x40
        else:
            continue

    return bytes(byte_array)


def add_ascii_bytes(df):
    '''
    add column of encoded english text
    '''
    df["en_bytes"] = df["en_text"].apply(encode_ascii)
    return df


def add_english_byte_length(df):
    '''
    add column of length of english strings in bytes
    '''
    df["en_length"] = df["en_bytes"].apply(len)
    return df


def add_japanese_byte_length(df):
    '''
    add column of length of japanese (hex) strings in bytes
    '''
    df["jp_length"] = df["jp_string"].apply(get_japanese_byte_length)
    return df


def get_japanese_byte_length(hex_string):
    '''
    calculate number of bytes in japanese string
    '''
    if hex_string == "":
        return 0

    hex_string += "0000"
    string_length = len(hex_string) / 2

    # account for padding
    if string_length % 4 != 0:
        string_length += 2

    return int(string_length)


def add_byte_lengths(df):
    '''
    add byte lengths for japanese and english
    '''
    df = add_japanese_byte_length(df)
    df = add_english_byte_length(df)

    # set length to 0 for repeated strings
    addresses = []
    for i in df.index:
        int_address = hex_to_integer(df.loc[i]["jp_address"])
        if int_address not in addresses:
            addresses.append(int_address)
        else:
            df.at[i, "jp_length"] = 0
            df.at[i, "en_length"] = 0

    return df


def hex_to_integer(hex_string):
    '''
    to use in a dataframe
    '''
    return int(hex_string, 16)


def add_japanese_block_indices(df):
    '''
    identify groups of strings stored contiguously
    '''
    # sort df by integer address values
    df["jp_address_int"] = df["jp_address"].apply(hex_to_integer)
    df = df.sort_values(by="jp_address_int")
    df = df.reset_index()

    # Add a block index
    block_index = 0
    previous_address = df.loc[0]["jp_address_int"] # for keeping track of 0 length strings
    previous_length = df.loc[0]["jp_length"]
    df["jp_block"] = 0 # initialize column with first index

    for i in df.index:
        address = df.loc[i]["jp_address_int"]
        length = df.loc[i]["jp_length"]

        # move to a new index
        address_difference = address - previous_address
        if address_difference > previous_length:
            block_index += 1

        # skip duplicate strings
        if length != 0:
            previous_address = address
            previous_length = length

        df.at[i, "jp_block"] = block_index

    return df


def get_block_dictionary(df):
    '''
    create a dictionary of block index and starting, ending address
    '''
    block_list = df["jp_block"].unique()
    block_dictionary = {}

    for block in block_list:
        # apply a mask to find the start/end addresses
        mask = (df["jp_block"] == block)
        block_df = df[mask]

        # get starting address
        start_address = block_df["jp_address_int"].min()

        # add length to address of last string to get ending address
        end_index = block_df["jp_address_int"].idxmax()
        end_address = block_df.loc[end_index]["jp_address_int"] + block_df.loc[end_index]["jp_length"]

        # done!
        block_dictionary[block] = (start_address, end_address)

    # add an overflow space
    block = block_list[-1] + 1
    block_dictionary[block] = (0, 100000000) 

    return block_dictionary


def assign_english_addresses(df):
    '''
    use block index dictionary to assign starting addresses for english strings
    '''
    # easier than having to pass it in
    block_dictionary = get_block_dictionary(df)

    # prepare for loop
    df["en_block"] = 0
    df["en_address_int"] = 0
    block = 0 # first block index is always 0
    current_start_address = block_dictionary[block][0]
    block_end_address = block_dictionary[block][1]
    tentative_end_address = 0

    for i in df.index:
        # ignore empty (and therefore duplicated) strings
        if df.loc[i, "en_length"] == 0:
            df.at[i, "en_block"] = block
            df.at[i, "en_address_int"] = current_start_address
            continue

        # what would be the new end address if added to the current block
        tentative_end_address = current_start_address + df.loc[i]["en_length"]

        # if we need to start a new block, update info
        if tentative_end_address >= block_end_address:
            block += 1
            current_start_address = block_dictionary[block][0]
            block_end_address = block_dictionary[block][1]
            tentative_end_address = current_start_address + df.loc[i]["en_length"]

        df.at[i, "en_block"] = block
        df.at[i, "en_address_int"] = current_start_address
        current_start_address = tentative_end_address

    return df


def prepare_for_writing(input_file):
    '''
    perform all of the necessary functions to get us ready to write the files
    this will return a df sorted in order of pointer table
    '''
    df = get_dataframe(input_file)
    df = add_ascii_bytes(df)
    df = add_byte_lengths(df)
    df = add_japanese_block_indices(df)
    df = assign_english_addresses(df)

    # add integer pointers for next steps
    df["jp_pointer_int"] = df["jp_pointer"].apply(hex_to_integer)

    return df




if __name__ == "__main__":

    input_file = Path(sys.argv[1])

    # get dataframe and check length
    df = get_dataframe(input_file)
    df = add_ascii_bytes(df)
    df = add_byte_lengths(df)

    jp_total = df["jp_length"].sum()
    en_total = df["en_length"].sum()

    print("japanese bytes:", jp_total)
    print("english_bytes", en_total)

    # divide into blocks
    df = add_japanese_block_indices(df)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df)
    dictionary = get_block_dictionary(df)
    print(dictionary)

    for block, addresses in dictionary.items():
        length = addresses[1] - addresses[0]
        print("block", block, "length:", length)

    df = assign_english_addresses(df)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df)
