"""GUI elements for AutoHat app"""

# Third party libraries
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

# Internal libraries
import hatFunctions as hf


# Main App Class
class AutoHat(tk.Tk):
    def __init__(self):

        # main setup
        super().__init__()
        self.title('Auto Hat')
        self.geometry('500x250')

        self.file_frame = FileFrame(self, self.show_checkin_frame)
        self.file_frame.pack(padx=5, pady=5, fill='both', expand=True)

        self.checkin_frame = None

        # run
        self.mainloop()

    # Method to switch frames and load the check in frame
    def show_checkin_frame(self):
        if self.file_frame.done:
            self.geometry('500x700')
            self.checkin_frame = CheckInFrame(self, self.file_frame.roster_df, self.file_frame.save_dir)
            self.checkin_frame.pack(padx=5, pady=5, fill='both', expand=True)
            self.file_frame.pack_forget()


# Class for frame which lets the user select the input file and save directory
class FileFrame(ttk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.done = False
        self.file_path = ''
        self.save_dir = ''
        self.roster_df = None
        self.data_in_label = ttk.Label(self, text='Check In Sheet Filepath: ')
        self.data_in_path = ttk.Label(self, text='', padding=5)
        self.data_in_button = ttk.Button(self, text='Browse', command=self.get_filepath)

        self.save_dir_label = ttk.Label(self, text='Save Directory Filepath: ')
        self.save_dir_path = ttk.Label(self, text='', padding=5)
        self.save_dir_button = ttk.Button(self, text='Browse', command=self.get_save_dir)

        self.check_in_button = ttk.Button(self, text='Start Check In', command=self.check_in)

        self.create_layout()

    # Pack the frame
    def create_layout(self):
        self.data_in_label.pack(anchor=tk.W, padx=10, pady=5)
        self.data_in_path.pack(anchor=tk.W, padx=10, pady=5)
        self.data_in_button.pack(anchor=tk.W, padx=10, pady=5)

        self.save_dir_label.pack(anchor=tk.W, padx=10, pady=5)
        self.save_dir_path.pack(anchor=tk.W, padx=10, pady=5)
        self.save_dir_button.pack(anchor=tk.W, padx=10, pady=5)

        self.check_in_button.pack(anchor=tk.SE, padx=10, pady=5)

    # Function to "Browse" and find the correct input file
    def get_filepath(self):
        self.file_path = filedialog.askopenfilename(
            title='Select a file',
            filetypes=(('All files', '*.*'),)
        )
        if self.file_path:
            self.data_in_path.config(text=self.file_path)

    # Function to "Browse" and find the correct save directory
    def get_save_dir(self):
        self.save_dir = filedialog.askdirectory(title='Select a Folder')
        if self.save_dir:
            self.save_dir_path.config(text=self.save_dir)

    # Callback function to main app class, switches frames and loads the check in frame
    def check_in(self):
        self.roster_df = hf.launch_checkin(self.file_path)
        self.done = True
        self.callback()


# Class for check in frame which lets the user mark attendance, choose the number of teams to create rosters for, and
# generate excel spreadsheets which list the randomly shuffled teams
class CheckInFrame(ttk.Frame):
    def __init__(self, parent, roster_df, save_dir):
        super().__init__(parent)
        self.roster_df = roster_df
        self.save_dir = save_dir
        self.baggages = []
        self.baggage_idxs = []
        self.labels = []
        self.check_buttons = []

        self.num_teams_label = ttk.Label(self, text='Number of Teams: ')
        self.options = [2, 2, 3, 4, 5, 6, 7, 8]
        self.num_teams = tk.IntVar()
        self.num_teams.set(self.options[0])
        self.num_teams_menu = ttk.OptionMenu(self, self.num_teams, *self.options)

        self.draw_teams_button = ttk.Button(self, text='Draw Teams', command=self.draw_teams)

        self.num_players_label = ttk.Label(self, text=0)
        self.count_players = ttk.Button(self, text='Count Players', command=self.update_player_count)

        self.drop_in_button = ttk.Button(self, text='Add Drop-in Player', command=self.drop_in)

        self.add_baggage_button = ttk.Button(self, text='Add Baggage', command=self.add_baggage)

        self.export_players_button = ttk.Button(self, text='Export Players', command=self.export_players)

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
        self.refresh_player_list()

        self.num_teams_label.pack(anchor=tk.W, padx=10, pady=5)
        self.num_teams_menu.pack(anchor=tk.W, padx=10, pady=5)
        self.draw_teams_button.pack(anchor=tk.SW, padx=10, pady=20)
        self.num_players_label.pack(anchor=tk.E, padx=10, pady=5)
        self.count_players.pack(anchor=tk.E, padx=10, pady=5)
        self.drop_in_button.pack(anchor=tk.W, padx=10, pady=5)
        self.add_baggage_button.pack(anchor=tk.W, padx=10, pady=5)
        self.export_players_button.pack(anchor=tk.E, padx=10, pady=5)
        
    # Function to update the count of players that are checked in, which will display automatically
    def update_player_count(self):
        num_players = sum(1 for here in self.check_buttons if here.get())
        self.num_players_label.config(text=num_players)

    # Function which updates the drop-in player list. Can be called by the child frame "DropInFrame"
    def update_roster(self, drop_in_df):
        start_index = len(self.roster_df)

        self.roster_df = pd.concat([self.roster_df, drop_in_df], axis=0, ignore_index=True)

        # Automatically check new players
        new_indices = list(range(start_index, len(self.roster_df)))

        self.refresh_player_list(prechecked_indices=new_indices)

    def refresh_player_list(self, prechecked_indices=None):
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
        for i, (_, row) in enumerate(self.roster_df.iterrows()):
            name = row['name']

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


    # Function which builds the drop-in frame to allow drop-in players to be added to the roster
    def drop_in(self):
        drop_in_window = tk.Toplevel(self)
        drop_in_window.title('Add Drop-in Player')
        drop_in_window.geometry('300x100')
        drop_in_frame = DropInFrame(drop_in_window)
        drop_in_frame.pack()


    def add_baggage(self):
        baggage_window = tk.Toplevel(self)
        baggage_window.title('Add Baggage')
        baggage_window.geometry('500x700')
        baggage_frame = BaggageFrame(baggage_window)
        baggage_frame.pack(fill='both', expand=True)


    # Function which discards all rostered players not present, then randomly shuffles teams based on the GUI inputs
    # and generates an excel sheet with the newly created teams
    def draw_teams(self):
        try:
            present_mask = [var.get() for var in self.check_buttons]
            filtered_df = self.roster_df[present_mask].reset_index(drop=True)
            hf.generate_teams(filtered_df, self.save_dir, self.num_teams.get(), self.baggages)
            messagebox.showinfo('hat empty', 'Teams spreadsheet created')
        except (IndexError, KeyError, ValueError):
            messagebox.showinfo('Error', 'Not enough players checked in')

    # Function to generate export a list of all checked in players and drop in players to the save directory
    def export_players(self):
        present_mask = [var.get() for var in self.check_buttons]
        filtered_df = self.roster_df[present_mask].reset_index(drop=True)
        hf.export_players(filtered_df, self.save_dir)
        messagebox.showinfo('Success', 'Player sheet exported successfully')


# Frame to allow a drop-in player to be manually added to the roster. Accessed from the Check-in frame
class DropInFrame(ttk.Frame):
    def __init__(self, master):
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
        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1, columnspan=2)
        self.gender_label.grid(row=1, column=0)
        self.male_rb.grid(row=1, column=1)
        self.female_rb.grid(row=1, column=2)
        self.rank_label.grid(row=2, column=0)
        self.rank_entry.grid(row=2, column=1, columnspan=2)
        self.add_button.grid(row=3, column=1)

    def add_player(self):
        drop_in_df = hf.add_drop_in(self.name.get(), self.gender.get(), self.rank.get())
        self.master.master.update_roster(drop_in_df)
        self.master.destroy()


# Frame to add PlayerGroup baggages to the baggages list. Accessed from the Check-in Frame
class BaggageFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Reference to CheckInFrame
        self.parent = master.master

        # --- Build player_roster dataframe ---
        roster = self.parent.roster_df.copy()
        present_mask = [var.get() for var in self.parent.check_buttons]
        filtered_roster = roster[present_mask]
        self.roster = filtered_roster[~filtered_roster.index.isin(self.parent.baggage_idxs)].copy()

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

    # --- Layout ---
    def create_layout(self):
        for _, row in self.roster.iterrows():
            name = row['name']

            frame = ttk.Frame(self.canvas_frame)
            frame.pack(fill='x', padx=10, pady=5)

            label = ttk.Label(frame, text=name)
            label.pack(side='right', padx=10)

            var = tk.BooleanVar()
            check = ttk.Checkbutton(frame, variable=var)
            check.pack(side='left', padx=10)

            self.check_vars.append(var)

        self.create_button.pack(anchor=tk.SW, padx=10, pady=10)

    # --- Create baggage and return selected players ---
    def create_baggage(self):
        selected_names = [
            self.roster.iloc[i]['name']
            for i, var in enumerate(self.check_vars)
            if var.get()
        ]

        # Send result back to CheckInFrame
        baggage, idxs = hf.create_baggage(selected_names, self.parent.roster_df)
        self.parent.baggages.append(baggage)
        self.parent.baggage_idxs.extend(idxs)

        # Close window
        self.master.destroy()
