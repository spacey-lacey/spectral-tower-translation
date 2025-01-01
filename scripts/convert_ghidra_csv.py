from pathlib import Path
import pandas as pd
import sys


def get_input_csv_name(input_file):
    '''
    get name of input file
    '''
    return input_file.name


def get_dataframe(input_path):
    '''
    read in csv file as a pandas dataframe
    '''
    df = pd.read_csv(input_path, delimiter="\t", keep_default_na=False, dtype={"en_text": str})
    print("Read", input_path)
    return df


def add_japanese_text(df):
    '''
    add translation column
    '''
    df["jp_text"] = df["jp_string"].apply(decode_shift_jis)
    return df


def decode_shift_jis(hex_string):
    '''
    convert hex string to bytes, then unicode
    '''
    raw_bytes = bytes.fromhex(hex_string)
    return raw_bytes.decode("shift_jis", errors="replace")


def create_new_csv(input_file):
    '''
    save new csv with addresses and japanese text (no shift jis)
    '''
    df = get_dataframe(input_file)
    df = add_japanese_text(df)
    output_file_name = get_input_csv_name(input_file)
    df.to_csv(output_file_name, sep="\t", index=False)
    print("Created", output_file_name)


if __name__ == "__main__":

    input_file = Path(sys.argv[1])
    create_new_csv(input_file)
