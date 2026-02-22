"""GUI elements for AutoHat app"""

# Third party libraries
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Internal libraries
import hatFunctions as hf


# Main App Class
class AutoHat(tk.Tk):
    """Main application class for the AutoHat GUI"""

    def __init__(self):
        """Initialize the main application window"""

        # main setup
        super().__init__()
        self.title('Auto Hat')
        self.geometry('500x250')

        self.file_frame = FileFrame(self, self.show_checkin_frame)
        self.file_frame.pack(padx=5, pady=5, fill='both', expand=True)

        self.checkin_frame = None

        # run
        self.mainloop()

    def show_checkin_frame(self):
        """Switch frames and load the check-in frame"""
        if self.file_frame.done:
            self.geometry('500x700')
            self.checkin_frame = CheckInFrame(self, self.file_frame.roster, self.file_frame.save_dir)
            self.checkin_frame.pack(padx=5, pady=5, fill='both', expand=True)
            self.file_frame.pack_forget()


class FileFrame(ttk.Frame):
    """Frame for selecting input file and save directory"""

    def __init__(self, parent, callback):
        """Initialize the file selection frame"""

        super().__init__(parent)
        self.callback = callback
        self.done = False
        self.file_path = ''
        self.save_dir = ''
        self.roster = None
        self.data_in_label = ttk.Label(self, text='Check In Sheet Filepath: ')
        self.data_in_path = ttk.Label(self, text='', padding=5)
        self.data_in_button = ttk.Button(self, text='Browse', command=self.get_filepath)

        self.save_dir_label = ttk.Label(self, text='Save Directory Filepath: ')
        self.save_dir_path = ttk.Label(self, text='', padding=5)
        self.save_dir_button = ttk.Button(self, text='Browse', command=self.get_save_dir)

        self.check_in_button = ttk.Button(self, text='Start Check In', command=self.check_in)

        self.create_layout()

    def create_layout(self):
        """Pack the frame widgets"""
        self.data_in_label.pack(anchor=tk.W, padx=10, pady=5)
        self.data_in_path.pack(anchor=tk.W, padx=10, pady=5)
        self.data_in_button.pack(anchor=tk.W, padx=10, pady=5)

        self.save_dir_label.pack(anchor=tk.W, padx=10, pady=5)
        self.save_dir_path.pack(anchor=tk.W, padx=10, pady=5)
        self.save_dir_button.pack(anchor=tk.W, padx=10, pady=5)

        self.check_in_button.pack(anchor=tk.SE, padx=10, pady=5)

    def get_filepath(self):
        """Browse and select the input file"""
        self.file_path = filedialog.askopenfilename(
            title='Select a file',
            initialdir='AutoHat\\player_input',
            filetypes=(('All files', '*.*'),)
        )
        if self.file_path:
            self.data_in_path.config(text=self.file_path)

    def get_save_dir(self):
        """Browse and select the save directory"""
        self.save_dir = filedialog.askdirectory(title='Select a Folder', initialdir='AutoHat\\teams')
        if self.save_dir:
            self.save_dir_path.config(text=self.save_dir)

    def check_in(self):
        """Callback to switch frames and load the check-in frame"""
        self.roster = hf.launch_checkin(self.file_path)
        self.done = True
        self.callback()


class CheckInFrame(ttk.Frame):
    """Frame for check-in, marking attendance, selecting team count, and generating teams"""

    def __init__(self, parent, roster, save_dir):
        """Initialize the check-in frame"""

        super().__init__(parent)
        self.roster = roster
        self.save_dir = save_dir
        self.baggages = []
        self.labels = []
        self.check_buttons = []

        self.num_teams_label = ttk.Label(self, text='Number of Teams: ')
        self.options = [2, 2, 3, 4, 5, 6, 7, 8]
        self.num_teams = tk.IntVar()
        self.num_teams.set(self.options[0])
        self.num_teams_menu = ttk.OptionMenu(self, self.num_teams, *self.options)

        self.draw_teams_button = ttk.Button(self, text='Draw Teams', command=self.draw_teams)

        self.num_players_label = ttk.Label(self, text=0)
        self.num_players_text_label = ttk.Label(self, text='Players Checked In:')

        self.drop_in_button = ttk.Button(self, text='Add Drop-in Player', command=self.drop_in)

        self.add_baggage_button = ttk.Button(self, text='Add Baggage', command=self.add_baggage)

        self.export_players_button = ttk.Button(self, text='Export Players', command=self.export_players)
        self.load_exported_button = ttk.Button(self, text='Load Exported Players', command=self.load_exported_players)

        # Create a canvas to hold the contents of the frame
        self.canvas = tk.Canvas(self)

        # Create a vertical scrollbar for the canvas
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas that will contain the labels and checkbuttons
        self.canvas_frame = ttk.Frame(self.canvas)

        self.create_layout()

        # Place the canvas and scrollbar in the frame
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        # Add the canvas_frame to the canvas and allow scrolling
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")

        # Update the scroll region to the size of the canvas_frame
        self.canvas_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

    # Pack the frame
    def create_layout(self):
        """Pack the frame widgets"""

        self.refresh_player_list()

        self.update_player_count()  # Initial count

        self.num_teams_label.pack(anchor=tk.W, padx=10, pady=5)
        self.num_teams_menu.pack(anchor=tk.W, padx=10, pady=5)
        self.draw_teams_button.pack(anchor=tk.SW, padx=10, pady=20)
        self.num_players_text_label.pack(anchor=tk.E, padx=10, pady=5)
        self.num_players_label.pack(anchor=tk.E, padx=10, pady=5)
        self.drop_in_button.pack(anchor=tk.W, padx=10, pady=5)
        self.add_baggage_button.pack(anchor=tk.W, padx=10, pady=5)
        self.load_exported_button.pack(anchor=tk.E, padx=10, pady=5)
        self.export_players_button.pack(anchor=tk.E, padx=10, pady=5)
 
    def update_player_count(self):
        """Update the count of checked-in players"""
        num_players = sum(1 for here in self.check_buttons if here.get())
        self.num_players_label.config(text=num_players)

    def update_roster(self, drop_in_player):
        """Update the roster with drop-in players"""
        start_index = len(self.roster.players)

        self.roster.players.append(drop_in_player)

        # Automatically check new players
        new_indices = [start_index]

        self.refresh_player_list(prechecked_indices=new_indices)

    def refresh_player_list(self, prechecked_indices=None):
        """Refresh the player list with checkboxes"""
        if prechecked_indices is None:
            prechecked_indices = []

        # --- Save existing checkbox states ---
        old_states = {
            i: var.get()
            for i, var in enumerate(self.check_buttons)
        }

        # --- Clear old widgets ---
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        self.labels.clear()
        self.check_buttons.clear()

        # --- Rebuild list ---
        for i, player in enumerate(self.roster.players):
            name = player.name

            frame = ttk.Frame(self.canvas_frame)
            frame.pack(fill='x', padx=10, pady=5)

            label = ttk.Label(frame, text=name)
            label.pack(side='right', padx=10)

            # Determine checkbox state
            checked = old_states.get(i, False) or (i in prechecked_indices)

            var = tk.BooleanVar(value=checked)
            checkbutton = ttk.Checkbutton(frame, variable=var)
            checkbutton.pack(side='left', padx=10)

            self.check_buttons.append(var)
            self.labels.append(label)

        # Add trace to update player count automatically
        for var in self.check_buttons:
            var.trace_add('write', lambda *args: self.update_player_count())


    def drop_in(self):
        """Open the drop-in player addition window"""
        drop_in_window = tk.Toplevel(self)
        drop_in_window.title('Add Drop-in Player')
        drop_in_window.geometry('300x100')
        drop_in_frame = DropInFrame(drop_in_window)
        drop_in_frame.pack()


    def add_baggage(self):
        """Open the baggage addition window"""
        baggage_window = tk.Toplevel(self)
        baggage_window.title('Add Baggage')
        baggage_window.geometry('500x700')
        baggage_frame = BaggageFrame(baggage_window)
        baggage_frame.pack(fill='both', expand=True)


    def draw_teams(self):
        """Generate and save shuffled teams to Excel"""
        try:
            present_mask = [var.get() for var in self.check_buttons]
            filtered_players = [p for p, present in zip(self.roster.players, present_mask) if present]
            # Remove baggages if any
            if len(self.baggages) > 0:
                filtered_players = [p for p in filtered_players if p not in [bp for bg in self.baggages for bp in bg.players]]
            hf.generate_teams(filtered_players, self.save_dir, self.num_teams.get(), self.baggages)
            messagebox.showinfo('hat empty', 'Teams spreadsheet created')
        except (IndexError, KeyError, ValueError):
            messagebox.showinfo('Error', 'Not enough players checked in')

    def export_players(self):
        """Export checked-in players to Excel"""
        present_mask = [var.get() for var in self.check_buttons]
        filtered_players = [p for p, present in zip(self.roster.players, present_mask) if present]
        hf.export_players(filtered_players, self.save_dir)
        messagebox.showinfo('Success', 'Player sheet exported successfully')


    def load_exported_players(self):
        """Load previously exported players and mark as checked-in"""
        file_path = filedialog.askopenfilename(
            title='Select exported players file',
            filetypes=(('Excel files', '*.xlsx'), ('All files', '*.*'))
        )
        if not file_path:
            return

        try:
            exported_roster = hf.load_exported_players(file_path)
        except Exception as e:
            messagebox.showinfo('Error', f'Unable to read exported players file:\n{e}')
            return
        if not exported_roster.players:
            messagebox.showinfo('Error', 'Exported players file was empty or malformed')
            return

        indices, unmatched = hf.get_attendance_indices(self.roster, exported_roster, 'name')

        hf.apply_attendance_column(self.roster, indices)

        self.refresh_player_list(prechecked_indices=indices)

        messagebox.showinfo('Load Complete', f'Loaded exported players. {len(indices)} matched, {len(unmatched)} unmatched.')


class DropInFrame(ttk.Frame):
    """Frame for adding drop-in players"""

    def __init__(self, master):
        """Initialize the drop-in frame"""

        super().__init__(master)

        self.name = tk.StringVar()
        self.gender = tk.StringVar()
        self.rank = tk.StringVar()

        self.name_label = ttk.Label(self, text="Player's full name")
        self.name_entry = ttk.Entry(self, textvariable=self.name)

        self.gender_label = ttk.Label(self, text='Gender')
        self.male_rb = ttk.Radiobutton(self, text='Male', variable=self.gender, value='male')
        self.female_rb = ttk.Radiobutton(self, text='Female', variable=self.gender, value='female')

        self.rank_label = ttk.Label(self, text='Skill rank (From 4 to 16)')
        self.rank_entry = ttk.Entry(self, textvariable=self.rank)

        self.add_button = ttk.Button(self, text='Add Player', command=self.add_player)

        self.create_layout()

    def create_layout(self):
        """Layout the widgets in the frame"""

        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1, columnspan=2)
        self.gender_label.grid(row=1, column=0)
        self.male_rb.grid(row=1, column=1)
        self.female_rb.grid(row=1, column=2)
        self.rank_label.grid(row=2, column=0)
        self.rank_entry.grid(row=2, column=1, columnspan=2)
        self.add_button.grid(row=3, column=1)

    def add_player(self):
        """Add the drop-in player to the roster"""
        drop_in_player = hf.add_drop_in(self.name.get(), self.gender.get(), self.rank.get())
        self.master.master.update_roster(drop_in_player)
        self.master.master.update_player_count()
        self.master.destroy()


class BaggageFrame(ttk.Frame):
    """Frame for adding player groups (baggages)"""

    def __init__(self, master):
        """Initialize the baggage frame"""

        super().__init__(master)

        # Reference to CheckInFrame
        self.parent = master.master

        # --- Build player_roster list ---
        present_mask = [var.get() for var in self.parent.check_buttons]
        filtered_players = [p for p, present in zip(self.parent.roster.players, present_mask) if present]
        # Remove already baggaged players
        baggaged_players = [bp for bg in self.parent.baggages for bp in bg.players]
        self.roster = [p for p in filtered_players if p not in baggaged_players]

        # Storage for checkbox variables
        self.check_vars = []

        # --- Button ---
        self.create_button = ttk.Button(self, text='Create baggage', command=self.create_baggage)

        # --- Scrollable area setup (same pattern as CheckInFrame) ---
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_frame = ttk.Frame(self.canvas)

        self.create_layout()

        # Pack scroll components
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")

        self.canvas_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

    def create_layout(self):
        """Layout the widgets in the frame"""
        for player in self.roster:
            name = player.name

            frame = ttk.Frame(self.canvas_frame)
            frame.pack(fill='x', padx=10, pady=5)

            label = ttk.Label(frame, text=name)
            label.pack(side='right', padx=10)

            var = tk.BooleanVar()
            check = ttk.Checkbutton(frame, variable=var)
            check.pack(side='left', padx=10)

            self.check_vars.append(var)

        self.create_button.pack(anchor=tk.SW, padx=10, pady=10)

    def create_baggage(self):
        """Create a baggage from selected players"""
        selected_names = [
            self.roster[i].name
            for i, var in enumerate(self.check_vars)
            if var.get()
        ]

        # Send result back to CheckInFrame
        baggage = hf.create_baggage(selected_names, self.parent.roster)
        self.parent.baggages.append(baggage)

        # Close window
        self.master.destroy()
