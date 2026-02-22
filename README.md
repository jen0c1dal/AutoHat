# AutoHat

AutoHat is a toolkit for managing ultimate frisbee league check-ins and generating balanced, random teams from registrant data.


**Features**
- Import registrant CSVs and calculate player ranks from skill fields
- Launch a simple GUI check-in or run via the CLI
- Generate balanced teams (exports to Excel)
- Add drop-in players and preserve exported player sheets for reuse
- Add/edit baggages (player groups) for team generation
- Robust Excel export/import using openpyxl
- Improved error handling and user feedback


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
- Export/import player sheets for attendance tracking and reuse
- Add drop-in players and baggages directly from the GUI

**Important files**
- GUI entry point: GUI.py
- CLI/runner: main.py
- Core logic: hatFunctions.py
- Example inputs: player_input/ (CSV exports)
- Linting config: pyproject.toml
- Requirements: requirements.txt, setup.py

**Testing & Contributing**
- Please test all GUI flows (check-in, team generation, export/import, baggage, drop-in) for edge cases
- Consider adding unit tests for core logic in hatFunctions.py
- Please open issues or PRs for bug fixes and feature requests.

**Contributing**
- Please open issues or PRs for bug fixes and feature requests.
