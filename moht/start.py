import tkinter as tk
from logging import getLogger
from os import path

from moht.tk_gui import MohtTkGui

LOG = getLogger(__name__)
__version__ = '0.0.1'


def run():
    """Function to start MHT GUI."""
    LOG.info(f'moht {__version__} https://gitlab.com/modding-openmw/modhelpertool')
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
