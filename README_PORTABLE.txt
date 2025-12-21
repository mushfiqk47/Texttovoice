PORTABLE MODE INSTRUCTIONS
==========================

To run this application in Portable Mode (e.g., from a USB drive):

1. Ensure the `.venv` folder is present inside this directory.
   - If you are preparing this for a USB drive, copy the entire "Texttovoice-main" folder, including `.venv`.
   - The `.venv` folder contains the Python interpreter and all dependencies.

2. Double-click `start_portable.bat`.
   - This script automatically finds the Python environment inside the folder.
   - It does NOT require Python to be installed on the host computer.

3. The application will open in your default web browser at http://localhost:8000.

TROUBLESHOOTING
---------------
- If you see "Could not find a local Python environment", make sure the `.venv` folder was copied correctly.
- If you are moving between different operating systems (e.g., Windows to Mac), this portable version will NOT work. The `.venv` folder is specific to Windows.
- If you have GPU issues, the app will automatically fall back to CPU mode (slower).

NOTES
-----
- Do not rename the `.venv` folder unless you update the `start_portable.bat` script.
- You can safely delete `setup_cpu.cmd`, `setup_gpu.cmd`, and `run.bat` if you only use `start_portable.bat`.
