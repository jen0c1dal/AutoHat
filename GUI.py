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
            self.geometry('500x500')
            self.checkin_frame = CheckInFrame(self, self.file_frame.reg_df, self.file_frame.save_dir)
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
        self.reg_df = None
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
        self.reg_df = hf.launch_checkin(self.file_path)
        self.done = True
        self.callback()


# Class for check in frame which lets the user mark attendance, choose the number of teams to create rosters for, and
# generate excel spreadsheets which list the randomly shuffled teams
class CheckInFrame(ttk.Frame):
    def __init__(self, parent, reg_df, save_dir):
        super().__init__(parent)
        self.reg_df = reg_df
        self.save_dir = save_dir
        self.drop_in_df = pd.DataFrame()
        self.labels = []
        self.check_buttons = []

        self.num_teams_label = ttk.Label(self, text='Number of Teams: ')
        self.options = [2, 2, 3, 4]
        self.num_teams = tk.IntVar()
        self.num_teams.set(self.options[0])
        self.num_teams_menu = ttk.OptionMenu(self, self.num_teams, *self.options)

        self.draw_teams_button = ttk.Button(self, text='Draw Teams', command=self.draw_teams)

        self.num_players_label = ttk.Label(self, text=0)
        self.count_players = ttk.Button(self, text='Count Players', command=self.update_player_count)

        self.drop_in_button = ttk.Button(self, text='Add Drop-in Player', command=self.drop_in)

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
        for _, row in self.reg_df.iterrows():
            name = row['name']

            frame = ttk.Frame(self.canvas_frame)
            frame.pack(fill='x', padx=10, pady=5)

            label = ttk.Label(frame, text=name)
            label.pack(side='right', padx=10)

            var = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(frame, variable=var)
            checkbutton.pack(side='left', padx=10)

            self.check_buttons.append(var)
            self.labels.append(label)

        self.num_teams_label.pack(anchor=tk.W, padx=10, pady=5)
        self.num_teams_menu.pack(anchor=tk.W, padx=10, pady=5)
        self.draw_teams_button.pack(anchor=tk.SW, padx=10, pady=20)
        self.num_players_label.pack(anchor=tk.E, padx=10, pady=5)
        self.count_players.pack(anchor=tk.E, padx=10, pady=5)
        self.drop_in_button.pack(anchor=tk.W, padx=10, pady=5)

    # Function to update the count of players that are checked in, which will display automatically
    def update_player_count(self):
        num_players = sum(1 for here in self.check_buttons if here.get())
        num_players += self.drop_in_df.shape[0]
        self.num_players_label.config(text=num_players)

    # Function which updates the drop-in player list. Can be called by the child frame "DropInFrame"
    def update_drop_in_df(self, drop_in_df):
        self.drop_in_df = drop_in_df.copy()

    # Function which builds the drop-in frame to allow drop-in players to be added to the roster
    def drop_in(self):
        drop_in_window = tk.Toplevel(self)
        drop_in_window.title('Add Drop-in Player')
        drop_in_window.geometry('300x100')
        drop_in_frame = DropInFrame(drop_in_window, self.drop_in_df)
        drop_in_frame.pack()


    # Function which discards all rostered players not present, then randomly shuffles teams based on the GUI inputs
    # and generates an excel sheet with the newly created teams
    def draw_teams(self):
        hold_df = self.reg_df.copy()
        for index, here in enumerate(self.check_buttons):
            if not here.get():
                self.reg_df.drop(index=index, inplace=True)
        self.reg_df = self.reg_df.reset_index(drop=True)
        try:
            full_roster_df = pd.DataFrame(pd.concat([self.reg_df, self.drop_in_df], axis=0, ignore_index=True))
            hf.generate_teams(full_roster_df, self.save_dir, self.num_teams.get())
            messagebox.showinfo('hat empty', 'Teams spreadsheet created')
        except (IndexError, KeyError, ValueError):
            messagebox.showinfo('Error', 'Not enough players checked in')
        self.reg_df = hold_df


# Frame to allow a drop-in player to be manually added to the roster. Accessed from the Check-in frame
class DropInFrame(ttk.Frame):
    def __init__(self, master, drop_in_df):
        super().__init__(master)
        self.drop_in_df = drop_in_df
        self.name = tk.StringVar()
        self.gender = tk.StringVar()
        self.rank = tk.StringVar()

        self.name_label = ttk.Label(self, text="Player's full name")
        self.name_entry = ttk.Entry(self, textvariable=self.name)

        self.gender_label = ttk.Label(self, text='Gender')
        self.male_rb = ttk.Radiobutton(self, text='Male', variable=self.gender, value='male')
        self.female_rb = ttk.Radiobutton(self, text='Female', variable=self.gender, value='female')

        self.rank_label = ttk.Label(self, text='Skill rank (From 3 to 11)')
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
        self.drop_in_df = hf.add_drop_in(self.drop_in_df, self.name.get(), self.gender.get(), self.rank.get())
        self.master.master.update_drop_in_df(self.drop_in_df)
        self.master.destroy()
