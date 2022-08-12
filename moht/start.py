import tkinter as tk
from os import path

from moht import tkgui


def run_tk():
    """Function to start Mod Helper Tool Tk GUI."""
    root = tk.Tk()
    width, height = 500, 230
    root.title('Mod Helper Tool')
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    root.iconphoto(False, tk.PhotoImage(file=path.join(path.abspath(path.dirname(__file__)), 'img', 'moht.png')))
    window = tkgui.MohtTkGui(master=root)
    window.mainloop()


if __name__ == '__main__':
    run_tk()
