import tkinter as tk
from logging import getLogger
from os import path, removedirs, chdir, walk, remove
from pprint import pformat
from shlex import split
from shutil import move, copy2, rmtree
from subprocess import Popen, PIPE
from time import time
from tkinter import filedialog, messagebox

from moht import PLUGINS2CLEAN
from moht.utils import parse_cleaning

__version__ = '0.0.1'
LOG = getLogger(__name__)


class MohtTkGui(tk.Frame):
    def __init__(self, master: tk.Tk,) -> None:
        """
        Create basic GUI for MOHT application.

        :param master: Top level widget
        """
        super().__init__(master)
        self.master = master
        self.master.title('MOHT')
        self.statusbar = tk.StringVar()
        self.mods_dir = tk.StringVar()
        self.morrowind_dir = tk.StringVar()
        self.chkbox_backup = tk.BooleanVar()
        self.chkbox_cache = tk.BooleanVar()
        self.stats = {'all': 0, 'cleaned': 0, 'clean': 0, 'error': 0}
        self._init_widgets()
        self.statusbar.set(f'ver. {__version__}')
        # self.mod_dir.set('/home/emc/.local/share/openmw/data')
        self.mods_dir.set('/home/emc/CitiesTowns/')
        self.morrowind_dir.set('/home/emc/.wine/drive_c/Morrowind/Data Files/')
        self.chkbox_backup.set(True)
        self.chkbox_cache.set(True)
        self._check_clean_bin()

    def _init_widgets(self) -> None:
        self.master.columnconfigure(index=0, weight=10)
        self.master.columnconfigure(index=1, weight=1)
        self.master.rowconfigure(index=0, weight=10)
        self.master.rowconfigure(index=1, weight=1)
        self.master.rowconfigure(index=2, weight=1)
        self.master.rowconfigure(index=3, weight=1)
        self.master.rowconfigure(index=4, weight=1)

        mods_dir = tk.Entry(master=self.master, textvariable=self.mods_dir)
        morrowind_dir = tk.Entry(master=self.master, textvariable=self.morrowind_dir)
        mods_btn = tk.Button(master=self.master, text='Select Mods Dir', width=16, command=self.select_dir)
        morrowind_btn = tk.Button(master=self.master, text='Select Morrowind Dir', width=16, command=self.select_dir)
        self.clean_btn = tk.Button(master=self.master, text='Clean Mods', width=16, command=self.start_clean)
        self.report_btn = tk.Button(master=self.master, text='Report', width=16, state=tk.DISABLED, command=self.report)
        close_btn = tk.Button(master=self.master, text='Close Tool', width=16, command=self.master.destroy)
        statusbar = tk.Label(master=self.master, textvariable=self.statusbar)
        chkbox_backup = tk.Checkbutton(master=self.master, text='Remove backup after successful clean-up', variable=self.chkbox_backup)
        chkbox_cache = tk.Checkbutton(master=self.master, text='Remove cache after successful clean-up', variable=self.chkbox_cache)

        mods_dir.grid(row=0, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        morrowind_dir.grid(row=1, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        chkbox_backup.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        chkbox_cache.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        mods_btn.grid(row=0, column=1, padx=2, pady=2)
        morrowind_btn.grid(row=1, column=1, padx=2, pady=2)
        self.clean_btn.grid(row=2, column=1, padx=2, pady=2)
        self.report_btn.grid(row=3, column=1, padx=2, pady=2)
        close_btn.grid(row=4, column=1, padx=2, pady=2)
        statusbar.grid(row=5, column=0, columnspan=3, sticky=tk.W)

    def select_dir(self) -> None:
        """Select directory location."""
        directory = filedialog.askdirectory(initialdir='/home/emc/', title='Select directory')
        LOG.debug(f'Directory: {directory}')
        self.mods_dir.set(f'{directory}')

    def start_clean(self) -> None:
        """Start cleaning process."""
        all_plugins = [path.join(root, filename) for root, _, files in walk(self.mods_dir.get()) for filename in files if filename.lower().endswith('.esp') or filename.lower().endswith('.esm')]
        LOG.debug(all_plugins)
        plugins_to_clean = [plugin_file for plugin_file in all_plugins if plugin_file.split('/')[-1] in PLUGINS2CLEAN]
        LOG.debug(f'{len(all_plugins)}: {all_plugins}')
        no_of_plugins = len(plugins_to_clean)
        LOG.debug(f'{no_of_plugins}: {plugins_to_clean}')
        chdir(self.morrowind_dir.get())
        here = path.abspath(path.dirname(__file__))
        self.stats = {'all': no_of_plugins, 'cleaned': 0, 'clean': 0, 'error': 0}
        start = time()
        for idx, plug in enumerate(plugins_to_clean, 1):
            LOG.debug(f'---------------------------- {idx} / {no_of_plugins} ---------------------------- ')
            LOG.debug(f'Copy: {plug} -> {self.morrowind_dir.get()}')
            copy2(plug, self.morrowind_dir.get())
            mod_file = plug.split('/')[-1]
            cmd = f'{path.join(here, "tes3cmd-0.37w")} clean --output-dir --overwrite "{mod_file}"'
            LOG.debug(f'CMD: {cmd}')
            stdout, stderr = Popen(split(cmd), stdout=PIPE, stderr=PIPE).communicate()
            out, err = stdout.decode('utf-8'), stderr.decode('utf-8')
            LOG.debug(f'Out: {out}')
            LOG.debug(f'Err: {err}')
            result, reason = parse_cleaning(out, err, mod_file)
            LOG.debug(f'Result: {result}, Reason: {reason}')
            self._update_stats(mod_file, plug, reason, result)
            if self.chkbox_backup.get():
                LOG.debug(f'Remove: {self.morrowind_dir.get()}{mod_file}')
                remove(f'{self.morrowind_dir.get()}{mod_file}')
        LOG.debug(f'---------------------------- Done: {no_of_plugins} ---------------------------- ')
        if self.chkbox_cache.get():
            removedirs(f'{self.morrowind_dir.get()}1')
            rmtree(f'{self.morrowind_dir.get()}.tes3cmd-3')
        LOG.debug(f'Total time: {time() - start:.2f} s')
        self.statusbar.set('Done. See report!')
        self.report_btn.config(state=tk.NORMAL)

    def _update_stats(self, mod_file: str, plug: str, reason: str, result: bool) -> None:
        if result:
            LOG.debug(f'Move: {self.morrowind_dir.get()}1/{mod_file} -> {plug}')
            move(f'{self.morrowind_dir.get()}1/{mod_file}', plug)
            self.stats['cleaned'] += 1
        if not result and reason == 'not modified':
            self.stats['clean'] += 1
        if not result and 'not found' in reason:
            self.stats['error'] += 1
            esm = self.stats.get(reason, 0)
            esm += 1
            self.stats.update({reason: esm})

    def report(self) -> None:
        """Show report after clean-up."""
        LOG.debug(f'Report: {self.stats}')
        messagebox.showinfo('Report', pformat(self.stats, width=15))
        self.report_btn.config(state=tk.DISABLED)
        self.statusbar.set(f'ver. {__version__}')

    def _check_clean_bin(self):
        here = path.abspath(path.dirname(__file__))
        LOG.debug(f'Checking tes3cmd')
        cmd = f'{path.join(here, "tes3cmd-0.37w")} -h'
        LOG.debug(f'CMD: {cmd}')
        stdout, stderr = Popen(split(cmd), stdout=PIPE, stderr=PIPE).communicate()
        out, err = stdout.decode('utf-8'), stderr.decode('utf-8')
        result, reason = parse_cleaning(out, err, '')
        LOG.debug(f'Result: {result}, Reason: {reason}')
        if not result and 'Config::IniFiles' in reason:
            msg = 'Use your package manager, check for `perl-Config-IniFiles` or a similar package.\n\nOr run from a terminal:\ncpan install Config::IniFiles'
            messagebox.showerror('Missing package', msg)
            self.statusbar.set(f'Error: {reason}')
            self.clean_btn.config(state=tk.DISABLED)
