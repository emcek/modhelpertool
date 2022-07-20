import tkinter as tk
from logging import getLogger
from os import path
from mht.tk_gui import MhtTkGui

LOG = getLogger(__name__)
__version__ = '0.0.1'


def run():
    """Function to start MHT GUI."""
    LOG.info(f'dcspy {__version__} https://github.com/emcek/dcspy')
    root = tk.Tk()
    width, height = 400, 200
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    here = path.abspath(path.dirname(__file__))
    # root.iconbitmap(default=path.join(here, 'dcspy.ico'))
    gui = MhtTkGui(master=root)
    gui.mainloop()


if __name__ == '__main__':
    run()
