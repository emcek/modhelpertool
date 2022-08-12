import tkinter as tk
from os.path import abspath, dirname, join

from moht.tkgui import MohtTkGui


def run_tk():
    """Function to start Mod Helper Tool Tk GUI."""
    root = tk.Tk()
    width, height = 500, 230
    root.title('Mod Helper Tool')
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    root.iconphoto(False, tk.PhotoImage(file=join(abspath(dirname(__file__)), 'img', 'moht.png')))
    gui = MohtTkGui(master=root)
    gui.mainloop()


if __name__ == '__main__':
    run_tk()
