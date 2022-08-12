import tkinter as tk
from functools import partial
from logging import getLogger
from os import path, removedirs, chdir, walk, remove, sep
from pathlib import Path
from shutil import move, copy2, rmtree
from sys import platform
from time import time
from tkinter import filedialog, messagebox

from moht import PLUGINS2CLEAN, VERSION
from moht.utils import is_latest_ver, parse_cleaning, run_cmd

logger = getLogger(__name__)


class MohtTkGui(tk.Frame):
    def __init__(self, master: tk.Tk,) -> None:
        """
        Create basic GUI for Mod Helper Tool application.

        :param master: Top level widget
        """
        logger.info(f'moht v{VERSION} https://gitlab.com/modding-openmw/modhelpertool')
        super().__init__(master)
        latest, desc = is_latest_ver(package='moht', current_ver=VERSION)
        self.master = master
        self.statusbar = tk.StringVar()
        self._mods_dir = tk.StringVar()
        self._morrowind_dir = tk.StringVar()
        self._tes3cmd = tk.StringVar()
        self.chkbox_backup = tk.BooleanVar()
        self.chkbox_cache = tk.BooleanVar()
        self.stats = {'all': 0, 'cleaned': 0, 'clean': 0, 'error': 0, 'time': 0.0}
        self._init_widgets()
        current_ver = '' if latest else f'new version: {desc}'
        self.statusbar.set(f'ver. {VERSION} {current_ver}')
        self._mods_dir.set(str(Path.home()))
        self._morrowind_dir.set(str(Path.home()))
        here = path.abspath(path.dirname(__file__))
        tes3cmd = 'tes3cmd-0.37v.exe' if platform == 'win32' else 'tes3cmd-0.37w'
        self._tes3cmd.set(path.join(here, 'resources', tes3cmd))
        self.chkbox_backup.set(True)
        self.chkbox_cache.set(True)

    def _init_widgets(self) -> None:
        self.master.columnconfigure(index=0, weight=10)
        self.master.rowconfigure(index=0, weight=1)
        self.master.rowconfigure(index=1, weight=1)
        self.master.rowconfigure(index=2, weight=1)

        mods_dir = tk.Entry(master=self.master, textvariable=self._mods_dir)
        morrowind_dir = tk.Entry(master=self.master, textvariable=self._morrowind_dir)
        tes3cmd_file = tk.Entry(master=self.master, textvariable=self._tes3cmd)
        mods_btn = tk.Button(master=self.master, text='Select Mods', width=16, command=partial(self.select_dir, self._mods_dir))
        morrowind_btn = tk.Button(master=self.master, text='Select Data Files', width=16, command=partial(self.select_dir, self._morrowind_dir))
        tes3cmd_btn = tk.Button(master=self.master, text='Select tes3cmd', width=16, command=partial(self.select_tes3cmd_file, self._tes3cmd))
        self.clean_btn = tk.Button(master=self.master, text='Clean Mods', width=16, command=self.start_clean)
        self.report_btn = tk.Button(master=self.master, text='Report', width=16, state=tk.DISABLED, command=self.report)
        close_btn = tk.Button(master=self.master, text='Close Tool', width=16, command=self.master.destroy)
        statusbar = tk.Label(master=self.master, textvariable=self.statusbar)
        chkbox_label = tk.Label(master=self.master, text='After successful clean-up:')
        chkbox_backup = tk.Checkbutton(master=self.master, text='Remove backups of plugins', variable=self.chkbox_backup)
        chkbox_cache = tk.Checkbutton(master=self.master, text='Remove cache of master files', variable=self.chkbox_cache)

        mods_dir.grid(row=0, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        morrowind_dir.grid(row=1, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        tes3cmd_file.grid(row=2, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        chkbox_label.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        chkbox_backup.grid(row=4, column=0, padx=2, pady=2, sticky=tk.W)
        chkbox_cache.grid(row=5, column=0, padx=2, pady=2, sticky=tk.W)
        mods_btn.grid(row=0, column=1, padx=2, pady=2)
        morrowind_btn.grid(row=1, column=1, padx=2, pady=2)
        tes3cmd_btn.grid(row=2, column=1, padx=2, pady=2)
        self.clean_btn.grid(row=3, column=1, padx=2, pady=2)
        self.report_btn.grid(row=4, column=1, padx=2, pady=2)
        close_btn.grid(row=5, column=1, padx=2, pady=2)
        statusbar.grid(row=6, column=0, columnspan=3, sticky=tk.W)

    @staticmethod
    def select_dir(text_var: tk.StringVar) -> None:
        """
        Select directory location.

        :param text_var: StringVar of Entry to update
        """
        directory = filedialog.askdirectory(initialdir=str(Path.home()), title='Select directory')
        logger.debug(f'Directory: {directory}')
        text_var.set(f'{directory}')

    def select_tes3cmd_file(self, text_var: tk.StringVar) -> None:
        """
        Select tes3cmd file location.

        :param text_var: StringVar of Entry to update
        """
        filename = filedialog.askopenfilename(initialdir=str(Path.home()), title='Select file')
        logger.debug(f'File: {filename}')
        text_var.set(f'{filename}')
        if self._check_clean_bin():
            self.clean_btn.config(state=tk.ACTIVE)
        else:
            self.clean_btn.config(state=tk.DISABLED)

    def start_clean(self) -> None:
        """Start cleaning process."""
        if not all([path.isdir(folder) for folder in [self.mods_dir, self.morrowind_dir]]):
            self.statusbar.set('Check directories and try again')
            return
        all_plugins = [Path(path.join(root, filename))
                       for root, _, files in walk(self.mods_dir)
                       for filename in files
                       if filename.lower().endswith('.esp') or filename.lower().endswith('.esm')]
        logger.debug(f'all_plugins: {len(all_plugins)}: {all_plugins}')
        plugins_to_clean = [plugin_file for plugin_file in all_plugins if str(plugin_file).split(sep)[-1] in PLUGINS2CLEAN]
        no_of_plugins = len(plugins_to_clean)
        logger.debug(f'to_clean: {no_of_plugins}: {plugins_to_clean}')
        chdir(self.morrowind_dir)
        self.stats = {'all': no_of_plugins, 'cleaned': 0, 'clean': 0, 'error': 0}
        start = time()
        for idx, plug in enumerate(plugins_to_clean, 1):
            logger.debug(f'---------------------------- {idx} / {no_of_plugins} ---------------------------- ')
            logger.debug(f'Copy: {plug} -> {self.morrowind_dir}')
            copy2(plug, self.morrowind_dir)
            mod_file = str(plug).split(sep)[-1]
            out, err = run_cmd(f'{self.tes3cmd} clean --output-dir --overwrite "{mod_file}"')
            result, reason = parse_cleaning(out, err, mod_file)
            logger.debug(f'Result: {result}, Reason: {reason}')
            self._update_stats(mod_file, plug, reason, result)
            if self.chkbox_backup.get():
                logger.debug(f'Remove: {self.morrowind_dir}/{mod_file}')
                remove(f'{self.morrowind_dir}/{mod_file}')
        logger.debug(f'---------------------------- Done: {no_of_plugins} ---------------------------- ')
        if self.chkbox_cache.get():
            removedirs(f'{self.morrowind_dir}/1')
            cachedir = 'tes3cmd' if platform == 'win32' else '.tes3cmd-3'
            rmtree(f'{self.morrowind_dir}/{cachedir}', ignore_errors=True)
        cleaning_time = time() - start
        self.stats['time'] = cleaning_time
        logger.debug(f'Total time: {cleaning_time} s')
        self.statusbar.set('Done. See report!')
        self.report_btn.config(state=tk.NORMAL)

    def _update_stats(self, mod_file: str, plug: Path, reason: str, result: bool) -> None:
        if result:
            logger.debug(f'Move: {self.morrowind_dir}/1/{mod_file} -> {plug}')
            move(f'{self.morrowind_dir}/1/{mod_file}', plug)
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
        logger.debug(f'Report: {self.stats}')
        report = f'Detected plugins to clean: {self.stats["all"]}\n'
        report += f'Already clean plugins: {self.stats["clean"]}\n'
        report += f'Cleaned plugins: {self.stats["cleaned"]}\n'
        report += '\n'.join([f'Error {k}: {self.stats[k]}' for k in self.stats if 'not found' in k])
        report += '\n\nCopy missing esm file(s) to Data Files directory and clean again.\n\n' if 'Error' in report else '\n'
        report += f'Total time: {self.stats["time"]:.2f} s'
        messagebox.showinfo('Cleaning Report', report)
        self.report_btn.config(state=tk.DISABLED)
        self.statusbar.set(f'ver. {VERSION}')

    def _check_clean_bin(self) -> bool:
        logger.debug('Checking tes3cmd')
        out, err = run_cmd(f'{self.tes3cmd} -h')
        result, reason = parse_cleaning(out, err, '')
        logger.debug(f'Result: {result}, Reason: {reason}')
        if not result:
            self.statusbar.set(f'Error: {reason}')
            if 'Config::IniFiles' in reason:
                reason = 'Use package manager, check for `perl-Config-IniFiles` or a similar package.\n\nOr run from a terminal:\ncpan install Config::IniFiles'
            elif 'Not tes3cmd' in reason:
                reason = 'Selected file is not a valid tes3cmd executable.\n\nPlease select a correct binary file.'
            messagebox.showerror('Not tes3cmd', reason)
        return result

    @property
    def mods_dir(self) -> str:
        """
        Get root of mods directory.

        :return: mods dir as string
        """
        return str(self._mods_dir.get())

    @mods_dir.setter
    def mods_dir(self, value: Path) -> None:
        self._mods_dir.set(str(value))

    @property
    def morrowind_dir(self) -> str:
        """
        Get Morrowind Data Files directory.

        :return: morrowind dir as string
        """
        return str(self._morrowind_dir.get())

    @morrowind_dir.setter
    def morrowind_dir(self, value: Path) -> None:
        self._morrowind_dir.set(str(value))

    @property
    def tes3cmd(self) -> str:
        """
        Get tes3cmd binary file path.

        :return: tes3cmd file as string
        """
        return str(self._tes3cmd.get())

    @tes3cmd.setter
    def tes3cmd(self, value: Path) -> None:
        self._tes3cmd.set(str(value))
