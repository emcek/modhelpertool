import tkinter as tk
from os import path

from moht.tk_gui import MohtTkGui


def run():
    """Function to start MOHT GUI."""
    root = tk.Tk()
    width, height = 500, 200
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    here = path.abspath(path.dirname(__file__))
    # root.iconbitmap(default=path.join(here, 'moht.ico'))
    gui = MohtTkGui(master=root)
    gui.mainloop()


if __name__ == '__main__':
    run()
