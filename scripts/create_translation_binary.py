from pathlib import Path
import pandas as pd
import sys

from organize_english_strings import prepare_for_writing, get_block_dictionary


def get_table_name(input_file):
    '''
    get name of input file without ".csv"
    '''
    return input_file.stem


def get_output_file_name(table_name, start_address, end_address):
    '''
    format for binary file name
    '''
    return table_name + "_" + str(hex(start_address)) + "_" + str(hex(end_address)) + ".bin"


def create_pointer_table(df, table_name):
    '''
    create binary file representing english pointer table
    '''
    # sort df by order of pointers
    df = df.sort_values(by="jp_pointer_int")

    # get start and end addresses for file name
    start_address = df["jp_pointer_int"].min()
    end_address = df["jp_pointer_int"].max() + 4 # add 4 for last address length
    file_name = get_output_file_name(table_name, start_address, end_address)

    with open(file_name, "wb") as f:
        for i in df.index:
            byte_string = int(df.loc[i]["en_address_int"]).to_bytes(4, "little")
            f.write(byte_string)

    print("Created file", file_name)


def create_string_data(df, table_name):
    '''
    use block dictionary to create one file of string data for each block
    fill out the file with zeros if the data do not cover the entire block
    '''
    block_dictionary = get_block_dictionary(df)

    for block, addresses in block_dictionary.items():
        mask = (df["en_block"] == block)
        block_df = df[mask]
        start_address = addresses[0]
        block_end_address = addresses[1]

        # if this block doesn't show up in the df, write zeros to that area
        if block_df.empty:
            end_address = start_address
        else:
            end_index = block_df["en_address_int"].idxmax()
            end_address = block_df.loc[end_index]["en_address_int"] + block_df.loc[end_index]["jp_length"]

        # sort df by integer address values
        block_df = block_df.sort_values(by="en_address_int")

        # check if we need to zero extend
        n_zero_bytes = 0
        if end_address < block_end_address:
            n_zero_bytes = block_end_address - end_address

        # write
        file_name = get_output_file_name(table_name, start_address, block_end_address)
        with open(file_name, "wb") as f:
            for i in block_df.index:
                # ignore repeated strings, indicated by length of 0
                if block_df.loc[i]["en_length"] != 0:
                    f.write(block_df.loc[i]["en_bytes"])
                else:
                    continue

            # finish with zero bytes
            zero_bytes = (0).to_bytes(n_zero_bytes)
            f.write(zero_bytes)

        print("Created file", file_name)
    

'''
shit to do later
add fancy english space tiles to code
remove 0x20 offset for ascii in remap_shift_jis_character
write a function to regex the english string???  and if it finds the pattern " [A-Z]",
use the string character index to change the byte at that index to LetterCode - 0x40
eventually add more functionality like ellipses, quotes, en dash
probably change replaced characters back to ascii and use 5 remaining slots for extras
space for one more character...do i need another?
'''


if __name__ == "__main__":

    input_file = Path(sys.argv[1])

    # only get the dataframe once
    df = prepare_for_writing(input_file)

    # name new files after input
    table_name = get_table_name(input_file)

    create_pointer_table(df, table_name)
    create_string_data(df, table_name)
