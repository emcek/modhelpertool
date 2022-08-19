import tkinter as tk
from functools import partial
from logging import getLogger
from os import path, chdir, remove
from pathlib import Path
from shutil import move, copy2
from sys import platform
from time import time
from tkinter import filedialog, messagebox

from moht import VERSION, TES3CMD, utils


class MohtTkGui(tk.Frame):
    def __init__(self, master: tk.Tk,) -> None:
        """
        Create basic GUI for Mod Helper Tool application.

        :param master: Top level widget
        """
        super().__init__(master)
        self.logger = getLogger(__name__)
        self.master = master
        self.statusbar = tk.StringVar()
        self._mods_dir = tk.StringVar()
        self._morrowind_dir = tk.StringVar()
        self._tes3cmd = tk.StringVar()
        self.chkbox_backup = tk.BooleanVar()
        self.chkbox_cache = tk.BooleanVar()
        self.rb_tes3cmd = tk.StringVar()
        self.stats = {'all': 0, 'cleaned': 0, 'clean': 0, 'error': 0, 'time': 0.0}
        self._init_widgets()
        self.statusbar.set(f'ver. {VERSION}')
        self._mods_dir.set(str(Path.home()))
        self._morrowind_dir.set(str(Path.home()))
        self._tes3cmd.set(path.join(utils.here(__file__), 'resources', TES3CMD[platform]['0_37']))
        self._check_clean_bin()
        self.chkbox_backup.set(True)
        self.chkbox_cache.set(True)
        self.tes3cmd_file.config(state=tk.DISABLED)
        self.tes3cmd_btn.config(state=tk.DISABLED)

    def _init_widgets(self) -> None:
        self.master.columnconfigure(index=0, weight=10)
        self.master.rowconfigure(index=0, weight=1)
        self.master.rowconfigure(index=1, weight=1)
        self.master.rowconfigure(index=2, weight=1)

        mods_dir = tk.Entry(master=self.master, textvariable=self._mods_dir)
        morrowind_dir = tk.Entry(master=self.master, textvariable=self._morrowind_dir)
        self.tes3cmd_file = tk.Entry(master=self.master, textvariable=self._tes3cmd)
        mods_btn = tk.Button(master=self.master, text='Select Mods', width=16, command=partial(self.select_dir, self._mods_dir))
        morrowind_btn = tk.Button(master=self.master, text='Select Data Files', width=16, command=partial(self.select_dir, self._morrowind_dir))
        self.tes3cmd_btn = tk.Button(master=self.master, text='Select tes3cmd', width=16, command=partial(self.select_tes3cmd_file, self._tes3cmd))
        self.clean_btn = tk.Button(master=self.master, text='Clean Mods', width=16, command=self.start_clean)
        self.report_btn = tk.Button(master=self.master, text='Report', width=16, state=tk.DISABLED, command=self.report)
        chkupd_btn = tk.Button(master=self.master, text='Check Updates', width=16, command=self.check_updates)
        close_btn = tk.Button(master=self.master, text='Close Tool', width=16, command=self.master.destroy)
        statusbar = tk.Label(master=self.master, textvariable=self.statusbar)
        chkbox_frame = tk.LabelFrame(master=self.master, text='After successful clean-up:', relief=tk.GROOVE, borderwidth=2)
        chkbox_backup = tk.Checkbutton(master=chkbox_frame, text='Remove backups of plugins', variable=self.chkbox_backup)
        chkbox_cache = tk.Checkbutton(master=chkbox_frame, text='Remove cache of master files', variable=self.chkbox_cache)

        rb_frame = tk.LabelFrame(master=self.master, text='Version of tes3cmd:', relief=tk.GROOVE, borderwidth=2)
        rb_037 = tk.Radiobutton(master=rb_frame, text='built-in v0.37', value='0_37', variable=self.rb_tes3cmd, command=self._rb_tes3cmd_toggled)
        rb_040 = tk.Radiobutton(master=rb_frame, text='built-in v0.40', value='0_40', variable=self.rb_tes3cmd, command=self._rb_tes3cmd_toggled)
        rb_custom = tk.Radiobutton(master=rb_frame, text='custom', value='custom', variable=self.rb_tes3cmd, command=self._rb_tes3cmd_toggled)
        rb_037.select()

        mods_dir.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=f'{tk.W}{tk.E}')
        morrowind_dir.grid(row=1, column=0, padx=2, pady=2, columnspan=2, sticky=f'{tk.W}{tk.E}')
        self.tes3cmd_file.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky=f'{tk.W}{tk.E}')
        chkbox_frame.grid(row=3, column=0, padx=2, pady=2, rowspan=2, sticky=tk.W)
        chkbox_backup.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        chkbox_cache.grid(row=4, column=0, padx=2, pady=2, sticky=tk.W)
        statusbar.grid(row=7, column=0, columnspan=3, sticky=tk.W)

        rb_frame.grid(row=3, column=1, padx=2, pady=2, rowspan=3)
        rb_037.grid(row=3, column=1, padx=2, pady=2, sticky=tk.W)
        rb_040.grid(row=4, column=1, padx=2, pady=2, sticky=tk.W)
        rb_custom.grid(row=5, column=1, padx=2, pady=2, sticky=tk.W)

        mods_btn.grid(row=0, column=2, padx=2, pady=2)
        morrowind_btn.grid(row=1, column=2, padx=2, pady=2)
        self.tes3cmd_btn.grid(row=2, column=2, padx=2, pady=2)
        self.clean_btn.grid(row=3, column=2, padx=2, pady=2)
        self.report_btn.grid(row=4, column=2, padx=2, pady=2)
        chkupd_btn.grid(row=5, column=2, padx=2, pady=2)
        close_btn.grid(row=6, column=2, padx=2, pady=2)

    def select_dir(self, text_var: tk.StringVar) -> None:
        """
        Select directory location.

        :param text_var: StringVar of Entry to update
        """
        directory = filedialog.askdirectory(initialdir=str(Path.home()), title='Select directory')
        self.logger.debug(f'Directory: {directory}')
        text_var.set(f'{directory}')

    def select_tes3cmd_file(self, text_var: tk.StringVar) -> None:
        """
        Select tes3cmd file location.

        :param text_var: StringVar of Entry to update
        """
        filename = filedialog.askopenfilename(initialdir=str(Path.home()), title='Select file')
        self.logger.debug(f'File: {filename}')
        text_var.set(f'{filename}')
        if self._check_clean_bin():
            self.clean_btn.config(state=tk.ACTIVE)
        else:
            self.clean_btn.config(state=tk.DISABLED)

    def _rb_tes3cmd_toggled(self) -> None:
        if self.rb_tes3cmd.get() == 'custom':
            self.tes3cmd_file.config(state=tk.NORMAL)
            self.tes3cmd_btn.config(state=tk.NORMAL)
        else:
            self.logger.debug(f'tes3cmd version: {self.rb_tes3cmd.get()}')
            self._tes3cmd.set(path.join(utils.here(__file__), 'resources', TES3CMD[platform][self.rb_tes3cmd.get()]))
            self.tes3cmd_file.config(state=tk.DISABLED)
            self.tes3cmd_btn.config(state=tk.DISABLED)
            self._check_clean_bin()

    def start_clean(self) -> None:
        """Start cleaning process."""
        if not all([path.isdir(folder) for folder in [self.mods_dir, self.morrowind_dir]]):
            self.statusbar.set('Check directories and try again')
            return
        all_plugins = utils.get_all_plugins(mods_dir=self.mods_dir)
        self.logger.debug(f'all_plugins: {len(all_plugins)}: {all_plugins}')
        plugins_to_clean = utils.get_plugins_to_clean(plugins=all_plugins)
        no_of_plugins = len(plugins_to_clean)
        self.logger.debug(f'to_clean: {no_of_plugins}: {plugins_to_clean}')
        req_esm = utils.get_required_esm(plugins=plugins_to_clean)
        self.logger.debug(f'Required esm: {req_esm}')
        missing_esm = utils.find_missing_esm(dir_path=self.mods_dir, data_files=self.morrowind_dir, esm_files=req_esm)
        self.logger.debug(f'Missing esm: {missing_esm}')
        utils.copy_filelist(missing_esm, self.morrowind_dir)
        chdir(self.morrowind_dir)
        self.stats = {'all': no_of_plugins, 'cleaned': 0, 'clean': 0, 'error': 0}
        start = time()
        for idx, plug in enumerate(plugins_to_clean, 1):
            self.logger.debug(f'---------------------------- {idx} / {no_of_plugins} ---------------------------- ')
            self.logger.debug(f'Copy: {plug} -> {self.morrowind_dir}')
            copy2(plug, self.morrowind_dir)
            mod_file = utils.extract_filename(plug)
            out, err = utils.run_cmd(f'{self.tes3cmd} clean --output-dir --overwrite "{mod_file}"')
            result, reason = utils.parse_cleaning(out, err, mod_file)
            self.logger.debug(f'Result: {result}, Reason: {reason}')
            self._update_stats(mod_file, plug, reason, result)
            if self.chkbox_backup.get():
                mod_path = path.join(self.morrowind_dir, mod_file)
                self.logger.debug(f'Remove: {mod_path}')
                remove(mod_path)
        self.logger.debug(f'---------------------------- Done: {no_of_plugins} ---------------------------- ')
        if self.chkbox_cache.get():
            cachedir = 'tes3cmd' if platform == 'win32' else '.tes3cmd-3'
            utils.rm_dirs_with_subdirs(dir_path=self.morrowind_dir, subdirs=['1', cachedir])
        utils.rm_copied_extra_esm(esm=missing_esm, data_files=self.morrowind_dir)
        cleaning_time = time() - start
        self.stats['time'] = cleaning_time
        self.logger.debug(f'Total time: {cleaning_time} s')
        self.statusbar.set('Done. See report!')
        self.report_btn.config(state=tk.NORMAL)

    def _update_stats(self, mod_file: str, plug: Path, reason: str, result: bool) -> None:
        if result:
            clean_plugin = path.join(self.morrowind_dir, '1', mod_file)
            self.logger.debug(f'Move: {clean_plugin} -> {plug}')
            move(clean_plugin, plug)
            self.stats['cleaned'] += 1
        if not result and reason == 'not modified':
            self.stats['clean'] += 1
        if not result and 'not found' in reason:
            for res in reason.split('**'):
                self.stats['error'] += 1
                esm = self.stats.get(res, 0)
                esm += 1
                self.stats.update({res: esm})

    def report(self) -> None:
        """Show report after clean-up."""
        self.logger.debug(f'Report: {self.stats}')
        report = f'Detected plugins to clean: {self.stats["all"]}\n'
        report += f'Already clean plugins: {self.stats["clean"]}\n'
        report += f'Cleaned plugins: {self.stats["cleaned"]}\n'
        report += '\n'.join([f'Error {k}: {self.stats[k]}' for k in self.stats if 'not found' in k])
        report += '\n\nCopy missing esm file(s) to Data Files directory and clean again.\n\n' if 'Error' in report else '\n'
        report += f'Total time: {self.stats["time"]:.2f} s'
        messagebox.showinfo('Cleaning Report', report)
        self.report_btn.config(state=tk.DISABLED)
        self.statusbar.set(f'ver. {VERSION}')

    def check_updates(self):
        """Check for updates."""
        latest, desc = utils.is_latest_ver(package='moht', current_ver=VERSION)
        current_ver = 'No updates' if latest else f'Update available: {desc}'
        self.statusbar.set(f'ver. {VERSION} - {current_ver}')

    def _check_clean_bin(self) -> bool:
        self.logger.debug('Checking tes3cmd')
        out, err = utils.run_cmd(f'{self.tes3cmd} -h')
        result, reason = utils.parse_cleaning(out, err, '')
        self.logger.debug(f'Result: {result}, Reason: {reason}')
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
