# create_csv_from_strings

from ghidra.program.flatapi import FlatProgramAPI
from ghidra.program.model.symbol import SymbolTable
import csv
import os


def read_shift_jis_string(api, address):
    """Reads a null-terminated Shift JIS string starting at the given address."""
    string_bytes = []
    while True:
        byte = api.getByte(address)
        if byte == 0:  # Null terminator
            break
        string_bytes.append(str(hex(byte & 0xFF))[2:])  # Ensure unsigned byte and remove "0x" prefix
        address = address.add(1)

    # Decode bytes as Shift JIS
    hex_string = str.join("", string_bytes)
    return hex_string.decode('shift_jis', errors='replace')


def get_address_by_label(label_name):
    """Finds the address of a label by name."""
    symbols = currentProgram.symbolTable.getGlobalSymbols(label_name)
    symbol = symbols[0]
    if symbol is None:
        raise Exception("Label '{}' not found!".format(label_name))
    return symbol.getAddress()


def extract_pointer_table(start_label, end_label):
    """Extracts pointer table data using start and end labels."""
    api = FlatProgramAPI(currentProgram)

    # Get start and end addresses based on labels
    pointer_table_start = get_address_by_label(start_label)
    pointer_table_end = get_address_by_label(end_label)

    # Generate CSV file name based on start label
    csv_file = "{}_strings.csv".format(start_label)
    csv_file = csv_file = os.path.expanduser("~/ghidra_scripts/" + csv_file)

    # Open CSV file for writing
    with open(csv_file, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["jp_pointer", "jp_address", "jp_string"])

        current_pointer_address = pointer_table_start

        while not current_pointer_address.equals(pointer_table_end):
            # Get target address
            target_address_value = api.getLong(current_pointer_address)
            target_address_value = target_address_value & 0xffffffff # convert to unsigned
            target_address_value = str(hex(target_address_value))[:-1] # remove "L" at the end of the string
            target_address = currentProgram.getAddressFactory().getAddress(target_address_value)

            # Read the string at the target address
            string = read_shift_jis_string(api, target_address)

            # Write the data to the CSV
            writer.writerow([current_pointer_address.toString(), target_address.toString(), string])

            # Go to next pointer
            current_pointer_address = current_pointer_address.next().next().next().next()

    print("Pointer table and Shift JIS strings extracted to: {}".format(csv_file))


# Parameters
start_label = "start_label"  # Replace with the name of the start label
end_label = "end_label"      # Replace with the name of the end label

# Run the extraction
extract_pointer_table(start_label, end_label)
