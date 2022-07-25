import tkinter as tk
from logging import getLogger
from os import path, removedirs, chdir, walk, remove
from pprint import pformat
from shlex import split
from shutil import move, copy2
from subprocess import Popen, PIPE
from tkinter import filedialog

from mht import PLUGINS2CLEAN
from mht.utils import parse_cleaning

__version__ = '0.0.1'
LOG = getLogger(__name__)


class MhtTkGui(tk.Frame):
    def __init__(self, master: tk.Tk,) -> None:
        """
        Create basic GUI for MHT application.

        :param master: Top level widget
        """
        super().__init__(master)
        self.master = master
        self.master.title('MHT')
        self.statusbar = tk.StringVar()
        self.mods_dir = tk.StringVar()
        self.morrowind_dir = tk.StringVar()
        self.chkbox_backup = tk.BooleanVar()
        self.stats = {'all': 0, 'cleaned': 0, 'clean': 0, 'error': 0}
        self._init_widgets()
        self.statusbar.set(f'ver. {__version__}')
        # self.mod_dir.set('/home/emc/.local/share/openmw/data')
        self.mods_dir.set('/home/emc/CitiesTowns/')
        self.morrowind_dir.set('/home/emc/.wine/drive_c/Morrowind/Data Files/')
        self.chkbox_backup.set(True)

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
        clean_btn = tk.Button(master=self.master, text='Clean Mods', width=16, command=self.start_clean)
        self.report_btn = tk.Button(master=self.master, text='Report', width=16, state=tk.DISABLED, command=self.report)
        close_btn = tk.Button(master=self.master, text='Close Tool', width=16, command=self.master.destroy)
        statusbar = tk.Label(master=self.master, textvariable=self.statusbar)
        chkbox_backup = tk.Checkbutton(master=self.master, text='Remove backup after successful clean-up', variable=self.chkbox_backup)

        mods_dir.grid(row=0, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        morrowind_dir.grid(row=1, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        chkbox_backup.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        mods_btn.grid(row=0, column=1, padx=2, pady=2)
        morrowind_btn.grid(row=1, column=1, padx=2, pady=2)
        clean_btn.grid(row=2, column=1, padx=2, pady=2)
        self.report_btn.grid(row=3, column=1, padx=2, pady=2)
        close_btn.grid(row=4, column=1, padx=2, pady=2)
        statusbar.grid(row=5, column=0, columnspan=3, sticky=tk.W)

    def select_dir(self) -> None:
        """Select directory location."""
        self.statusbar.set('You can close GUI')
        directory = filedialog.askdirectory(initialdir='/home/emc/', title='Select directory')
        LOG.debug(f'Directory: {directory}')
        self.mods_dir.set(f'{directory}')

    def start_clean(self) -> None:
        """Start cleaning process."""
        # add check for tes3cmd exaple of error when per initconfig not instaled
        # Can't locate Config/IniFiles.pm in @INC (you may need to install the Config::IniFiles module) (@INC contains: /usr/lib/perl5/5.36/site_perl
        # /usr/share/perl5/site_perl /usr/lib/perl5/5.36/vendor_perl /usr/share/perl5/vendor_perl /usr/lib/perl5/5.36/core_perl /usr/share/perl5/core_perl)
        # at /home/emc/tes3cmd-0.37w line 107.
        # BEGIN failed--compilation aborted at /home/emc/tes3cmd-0.37w line 107.

        all_plugins = [path.join(root, filename) for root, _, files in walk(self.mods_dir.get()) for filename in files if filename.lower().endswith('.esp') or filename.lower().endswith('.esm')]
        LOG.debug(all_plugins)
        plugins_to_clean = [plugin_file for plugin_file in all_plugins if plugin_file.split('/')[-1] in PLUGINS2CLEAN]
        LOG.debug(f'{len(all_plugins)}: {all_plugins}')
        LOG.debug(f'{len(plugins_to_clean)}: {plugins_to_clean}')
        chdir(self.morrowind_dir.get())
        LOG.debug('----------------------------------------------------')
        here = path.abspath(path.dirname(__file__))
        self.stats = {'all': len(plugins_to_clean), 'cleaned': 0, 'clean': 0, 'error': 0}
        for plug in plugins_to_clean:
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
            if self.chkbox_backup.get():
                LOG.debug(f'Remove: {self.morrowind_dir.get()}{mod_file}')
                remove(f'{self.morrowind_dir.get()}{mod_file}')
            LOG.debug('----------------------------------------------------')
        removedirs(f'{self.morrowind_dir.get()}1')
        self.statusbar.set('Done. See report!')
        self.report_btn.config(state=tk.NORMAL)

    def report(self) -> None:
        """Show report after clean-up."""
        LOG.debug(f'Report: {self.stats}')
        tk.messagebox.showinfo('Report', pformat(self.stats, width=15))
