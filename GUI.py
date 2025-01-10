import tkinter as tk
from tkinter import filedialog, ttk, messagebox
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

    # Function to update the count of players that are checked in, which will display automatically
    def update_player_count(self):
        num_players = sum(1 for here in self.check_buttons if here.get())
        self.num_players_label.config(text=num_players)

    # Function which discards all rostered players not present, then randomly shuffles teams based on the GUI inputs
    # and generates an excel sheet with the newly created teams
    def draw_teams(self):
        hold_df = self.reg_df.copy()
        for index, here in enumerate(self.check_buttons):
            if not here.get():
                self.reg_df.drop(index=index, inplace=True)
        self.reg_df = self.reg_df.reset_index(drop=True)
        try:
            hf.generate_teams(self.reg_df, self.save_dir, self.num_teams.get())
            messagebox.showinfo('hat empty', 'Teams spreadsheet created')
        except (IndexError, KeyError, ValueError):
            messagebox.showinfo('Error', 'Not enough players checked in')
        self.reg_df = hold_df
