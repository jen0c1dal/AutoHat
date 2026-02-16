# AutoHat

AutoHat is a small toolkit for managing ultimate frisbee league check-ins and generating balanced, random teams from registrant data.

**Features**
- Import registrant CSVs and calculate player ranks from skill fields
- Launch a simple GUI check-in or run via the CLI
- Generate balanced teams (exports to Excel)
- Add drop-in players and preserve exported player sheets for reuse

**Requirements**
- Python 3.8+
- pandas, numpy, xlsxwriter

Install dependencies (example):

```powershell
python -m pip install -r requirements.txt
```

**Quick Usage**

- GUI: Run the GUI frontend

```powershell
python GUI.py
```

- CLI: Use the main script to run available command-line flows

```powershell
python main.py
```

**Typical workflow**
- Place registration CSV exports in the `player_input/` directory.
- Use the GUI or `launch_checkin()` to load a roster; the code expects first/last name and skill columns used by `import_roster()`.
- Generate teams with `generate_teams()` — this writes an Excel file to the chosen output directory.

**Important files**
- GUI entry point: GUI.py
- CLI/runner: main.py
- Core logic: hatFunctions.py
- Example inputs: player_input/ (CSV exports)

**Contributing**
- Please open issues or PRs for bug fixes and feature requests.
