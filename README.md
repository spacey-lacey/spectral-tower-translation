# spectral-tower-translation
translating spectral tower (ps1) into english!!

## Changes made
- Removed logic for Shift_JIS tables 0x84–0x87 from character code remapping
- Greek and Cyrillic fullwidth tiles replaced with ASCII and blank space
- Added single-byte ASCII logic to character code remapping (for inventory)
- Implemented odd index english tileset

## Tiles
- The game uses 14x14 instead of 16x16 tiles for some ungodly reason
- For some other ungodly reason, the game does not use 7x7 tiles; it alternates between 8x7 and 6x7
- Characters cannot be any wider than 6 px (other than a few possible exceptions when they're guaranteed not to touch)
- Depending on the character's position/index in a line of text, take it from one of two tilesets that is shifted accourdinly: one for even indices (0, 2, ...) and one for odd indices (1, 3, ...)

## Very incomplete instructions
- Set up python venv using requirements.txt
- Build psximager
- Extract code from ROM with psxrip
- Analyze code in Ghidra using ghidra-psx-ldr
- Edit code in Ghidra (there were some special settingss for the header that i need to write down)
- In Ghidra, export updated code using File -> Export Program...-> Raw Binary
- The exported code will not contain the header, so it must be added to the top of the file (note to self: write a lil bash function to do this, copy the code over, and rebuild the rom)
- Rebuild ROM using psxbuilder 
- Make changes to the code in the smallest possible increments, or you will have a bad time debugging
