#!/usr/bin/env python3
# coding: utf-8

# metadata::nemo-icon-position
# gio info --attributes=metadata:: Desktop/*
# gio set --type=unset Desktop/DS3.desktop metadata::nemo-icon-position: 1781 \
#   ,100
# ~/.config/nemo/desktop-metadata

import os
import subprocess
import json
import appdirs
import glob
import tempfile
import shutil
import datetime

import ctypes.util

# from tkinter import *
from tkinter import Tk, Listbox, StringVar, Scrollbar, N, W, S, E
from tkinter import simpledialog
from tkinter import ttk


#######################################################

APP_NAME = 'icman'

META_PATH_HOLDER = '~~META~~'

NEMO_DESKTOP_NAME = "nemo-desktop"

HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
TMP_DIR = tempfile.gettempdir()

NEMO_NAME = "nemo"
NEMO_META_FILE_NAME = "desktop-metadata"
NEMO_META_PATH = "{}/{}".format(appdirs.user_config_dir(NEMO_NAME),
                                NEMO_META_FILE_NAME)

DATA_FILE_EXT = "jdat"

HDR1 = 'local path:'
NIC_HDR = 'nemo-icon-position'
HDR2 = f'metadata::{NIC_HDR}'

MON_HDR = 'monitor'
HDR3 = f'metadata::{MON_HDR}'

DESK_MON_HDR='desktop-monitor'

LHDR1 = len(HDR1)
LNIC_HDR = len(NIC_HDR)
LHDR2 = len(HDR2)
LMON_HDR = len(MON_HDR)
LHDR3 = len(HDR3)


LOAD_DESKTOP_ICONS_CMD = ('gio info --attributes=metadata:: ~/Desktop/* '
                          f'| grep "{HDR1}\\|{HDR2}:\\|{HDR3}"')

GIO_SET_ICONS_POS_CMD_TPL = f'gio set "{{}}" {HDR2} {{}},{{}}'
GIO_SET_ICONS_MON_CMD_TPL = f'gio set "{{}}" {HDR3} {{}}'

E_GEN = ('metadata format changed, current version is non-operable.')

#######################################################


class Monitor:
    x = y = w = h = 0
    name = ""

    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __str__(self):
        return str(vars(self))

    def __repr__(self):
        return str(self)

#######################


class XRRCrtcInfo(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_ulong),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("mode", ctypes.c_long),
        ("rotation", ctypes.c_int),
        ("noutput", ctypes.c_int),
        ("outputs", ctypes.POINTER(ctypes.c_long)),
        ("rotations", ctypes.c_ushort),
        ("npossible", ctypes.c_int),
        ("possible", ctypes.POINTER(ctypes.c_long)),
    ]


class XRRModeInfo(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_ulong),
        ("width", ctypes.c_uint),
        ("height", ctypes.c_uint),
        ("dotClock", ctypes.c_ulong),
        ("hSyncStart", ctypes.c_uint),
        ("hSyncEnd", ctypes.c_uint),
        ("hTotal", ctypes.c_uint),
        ("hSkew", ctypes.c_uint),
        ("vSyncStart", ctypes.c_uint),
        ("vSyncEnd", ctypes.c_uint),
        ("vTotal", ctypes.c_uint),
        ("name", ctypes.c_char_p),
        ("nameLength", ctypes.c_uint),
        ("modeFlags", ctypes.c_ulong)
    ]


class XRRScreenResources(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_ulong),
        ("configTimestamp", ctypes.c_ulong),
        ("ncrtc", ctypes.c_int),
        ("crtcs", ctypes.POINTER(ctypes.c_ulong)),
        ("noutput", ctypes.c_int),
        ("outputs", ctypes.POINTER(ctypes.c_ulong)),
        ("nmode", ctypes.c_int),
        ("modes", ctypes.POINTER(XRRModeInfo)),
    ]


class XRROutputInfo(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_ulong),
        ("crtc", ctypes.c_ulong),
        ("name", ctypes.c_char_p),
        ("nameLen", ctypes.c_int),
        ("mm_width", ctypes.c_ulong),
        ("mm_height", ctypes.c_ulong),
        ("connection", ctypes.c_ushort),
        ("subpixel_order", ctypes.c_ushort),
        ("ncrtc", ctypes.c_int),
        ("crtcs", ctypes.POINTER(ctypes.c_ulong)),
        ("nclone", ctypes.c_int),
        ("clones", ctypes.POINTER(ctypes.c_ulong)),
        ("nmode", ctypes.c_int),
        ("npreferred", ctypes.c_int),
        ("modes", ctypes.POINTER(ctypes.c_ulong)),
    ]

#######################


def GetMonitorsInfo():

    results = []

    x11_lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
    x11_lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11_lib.XOpenDisplay.restype = ctypes.POINTER(ctypes.c_void_p)

    xrandr_lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Xrandr"))
    xrandr_lib.XRRGetScreenResourcesCurrent.restype = ctypes.POINTER(
        XRRScreenResources)
    xrandr_lib.XRRGetOutputInfo.restype = ctypes.POINTER(XRROutputInfo)
    xrandr_lib.XRRGetCrtcInfo.restype = ctypes.POINTER(XRRCrtcInfo)

    disp = x11_lib.XOpenDisplay(b"")
    if not disp:
        raise RuntimeError("Can't open default display")

    try:

        wrt = x11_lib.XDefaultRootWindow(disp)
        sr = xrandr_lib.XRRGetScreenResourcesCurrent(disp, wrt)

        for i in range(sr.contents.noutput):

            oi = xrandr_lib.XRRGetOutputInfo(disp, sr, sr.contents.outputs[i])
            if not oi.contents.crtc or oi.contents.connection != 0:
                continue

            try:
                ci = xrandr_lib.XRRGetCrtcInfo(disp, ctypes.byref(oi),
                                               oi.contents.crtc)
                try:
                    m = Monitor(x=ci.contents.x, y=ci.contents.y,
                                w=ci.contents.width, h=ci.contents.height,
                                name=oi.contents.name.decode(
                                    os.sys.getfilesystemencoding()))
                    results.append(m)

                finally:
                    xrandr_lib.XRRFreeCrtcInfo(ci)
            finally:
                xrandr_lib.XRRFreeOutputInfo(oi)
    finally:
        x11_lib.XCloseDisplay(disp)

    return results


#######################################################

class IconData:

    fp = ''
    name = ''
    x = y = 0
    m = 0

    def __init__(self, entries):
        self.__dict__.update(entries)

    def __str__(self):
        # return f"{{{self.path=}, {self.x=}, {self.y=}}}"
        return str(vars(self))

    def __repr__(self):
        return str(self)


# get file just name: name from path /some/path/name.ext
def gfjn(fp_):
    return os.path.splitext(os.path.split(fp_)[1])[0]


class IcMan:

    configs = {}

    def __init__(self):
        self._LoadConfigs()

    def _GenConfigPath(template_name_):
        conf_dir = CONFIG_DIR + "/"
        fp = conf_dir + template_name_ + "." + DATA_FILE_EXT
        i = 0
        while os.path.exists(fp):
            fp = conf_dir + template_name_ + "_" + str(i) + "." + DATA_FILE_EXT
            i += 1
        return fp

    def _LoadIconConf(fp_):

        data = []
        try:
            with open(fp_, "rt") as inf:
                data = json.load(inf)
        except Exception as e:
            print(f"Error reading: {fp_}\nerr: {os.sys.exc_info()[0]}"
                  f"\nex:{e} :")

        icons = []
        for d in data:
            icons.append(IconData(d))

        return icons

    def _LoadConfigs(self):

        self.configs = {}

        if not os.path.exists(CONFIG_DIR):
            subprocess.run(f'mkdir -p {CONFIG_DIR}', shell=True, check=True)

        conf_dir = CONFIG_DIR + "/"

        files = glob.glob(conf_dir + "*." + DATA_FILE_EXT)
        for fp in files:
            icons = IcMan._LoadIconConf(fp)
            if len(icons) > 0:
                self.configs[gfjn(fp)] = icons

    def _SaveIconConf(fp_, icons_):
        with open(fp_, "wt") as outf:
            json.dump(icons_, outf, indent=2, default=vars)

    def _LoadCurentIcons():

        icons = []
        id = {}

        h1_present = False
        h2_present = False
        h3_present = False

        e_no_hdr1 = f'Header <{HDR1}> is not present'

        lc = 0
        # print (f"Executing: {LOAD_DESKTOP_ICONS_CMD}")
        lines = subprocess.run(LOAD_DESKTOP_ICONS_CMD, shell=True,
                               check=True, capture_output=True,
                               text=True).stdout.splitlines()

        for line in lines:

            s = line.strip()
            # print('Processing: ', s)
            lc += 1

            if s.startswith(HDR1):
                id = IconData({})
                id.fp = s[LHDR1 + 1:]
                h1_present = True
                h2_present = False
                h3_present = False

            elif s.startswith(HDR2):

                if not h1_present or h2_present:
                    raise RuntimeError(
                        f'{E_GEN}\n{e_no_hdr1}\nInvalid line({lc}): {s}')

                v2 = s[LHDR2 + 2:].split(',')
                id.x = int(v2[0])
                id.y = int(v2[1])

                h2_present = True
                if h3_present:
                    h1_present = False
                    icons.append(id)

            elif s.startswith(HDR3):

                if not h1_present or h3_present:
                    raise RuntimeError(
                        f'{E_GEN}\n{e_no_hdr1}\nInvalid line({lc}): {s}')

                v3 = s[LHDR3 + 2:]
                id.m = int(v3)

                h3_present = True
                if h2_present:
                    h1_present = False
                    icons.append(id)

            else:
                raise RuntimeError(f'{E_GEN}\nInvalid line({lc}): {s}')

        return icons

    def _LoadNemoMetaIcons(fp_):

        icons = []
        id = {}
        skip_block = False
        processing_block = False

        h1_present = False
        h2_present = False
        h3_present = False

        try:
            lc = 0
            with open(fp_, 'rt') as file1:
                lines = file1.readlines()
                for line in lines:
                    lc += 1
                    s = line.strip()

                    if(len(s) == 0):
                        h1_present = False
                        h2_present = False
                        h3_present = False

                        continue

                    if skip_block:
                        if not s.startswith('['):
                            continue
                        else:
                            skip_block = False

                    if s.startswith(f'[{DESK_MON_HDR}'):
                        skip_block = True
                        h1_present = False
                        h2_present = False
                        h3_present = False
                        continue

                    if s.startswith("["):
                        h1_present = True
                        h2_present = False
                        h3_present = False

                        n = s.strip('[]')
                        id = IconData({})
                        id.fp = META_PATH_HOLDER
                        id.name = n
                        continue

                    if not h1_present:
                        raise RuntimeError(f'{fp_} {E_GEN}\n line({lc}): {s}')

                    if s.startswith(NIC_HDR + '='):

                        if h2_present:
                            raise RuntimeError(f'{fp_} {E_GEN}\n line({lc}): {s}')

                        v2 = s[LNIC_HDR + 1:].split(',')
                        id.x = int(v2[0])
                        id.y = int(v2[1])

                        h2_present = True
                        if h3_present:
                            icons.append(id)

                    if s.startswith(MON_HDR + '='):

                        if h3_present:
                            raise RuntimeError(f'{fp_} {E_GEN}\n line({lc}): {s}')

                        v3 = s[LMON_HDR + 1:]
                        id.m = int(v3)

                        h3_present = True
                        if h2_present:
                            icons.append(id)

        except Exception as e:
            print(f'_LoadNemoMetaIcons exception:\n{e}')

        return icons

    def _ApplyNemoMetaDesktop(fp_, meta_icons_):
        if len(meta_icons_) == 0:
            return

        meta_dict = {}
        for o in meta_icons_:
            meta_dict[o.name] = o

        out_line = []
        skip_block = False
        processing_block = False
        curr_o = IconData({})

        try:
            lc = 0
            with open(fp_, 'rt') as file1:
                lines = file1.readlines()
                for line in lines:
                    lc += 1
                    s = line.strip()

                    if(len(s) == 0):
                        processing_block = False
                        out_line.append('\n')
                        # print('0>>> ' + out_line[len(out_line) - 1])
                        continue

                    if skip_block:
                        if not s.startswith('['):
                            out_line.append(s + '\n')
                            # print('1>>> ' + out_line[len(out_line) - 1])
                            continue
                        else:
                            skip_block = False

                    if s.startswith("[desktop-monitor"):
                        skip_block = True
                        out_line.append(s + '\n')
                        # print('2>>> ' + out_line[len(out_line) - 1])
                        continue

                    if s.startswith("["):
                        processing_block = True
                        n = s.strip('[]')

                        if n not in meta_dict:
                            skip_block = True
                            out_line.append(s + '\n')
                            # print('3>>> ' + out_line[len(out_line) - 1])
                            continue
                        else:
                            curr_o = meta_dict[n]

                    if not processing_block:
                        raise RuntimeError(f'{fp_} {E_GEN}\n line({lc}): {s}')

                    if s.startswith(NIC_HDR + '='):
                        out_line.append(f'{NIC_HDR}={curr_o.x},{curr_o.y}\n')
                        # print('4>>> ' + out_line[len(out_line) - 1])
                    elif s.startswith(MON_HDR + '='):
                        out_line.append(f'{MON_HDR}={curr_o.m}\n')
                    else:
                        out_line.append(s + '\n')
                        # print('5>>> ' + out_line[len(out_line) - 1])

        except Exception as e:
            print(f'_LoadNemoMetaIcons read exception:\n{e}')

        if len(out_line) > 0:
            with open(fp_, "wt") as outf:
                str = ''.join(out_line)
                # print(str)
                outf.write(str)

    def SaveCurrentConfig(self):

        monitors = GetMonitorsInfo()
        name_tpl = '0x0'

        if len(monitors) == 1:
            name_tpl = f'{monitors[0].w}x{monitors[0].h}'
        elif len(monitors) == 2:
            name_tpl = (f'{monitors[0].w}x{monitors[0].h}'
                        f'+{monitors[1].w}x{monitors[1].h}')
        elif len(monitors) == 3:
            name_tpl = (f'{monitors[0].w}x{monitors[0].h}'
                        f'+{monitors[1].w}x{monitors[1].h}'
                        f'+{monitors[2].w}x{monitors[2].h}')
        elif len(monitors) > 3:
            name_tpl = (f'{monitors[0].w}x{monitors[0].h}'
                        f'+{len(monitors)}monitors')

        fp = IcMan._GenConfigPath(name_tpl)
        icons = IcMan._LoadCurentIcons()
        icons += IcMan._LoadNemoMetaIcons(NEMO_META_PATH)

        if len(icons) > 0:
            IcMan._SaveIconConf(fp, icons)
            self.configs[gfjn(fp)] = icons

    def _KillNemoDesktop():
        subprocess.run(['killall', f'{NEMO_DESKTOP_NAME}'])

    def _StartNemoDesktop():
        subprocess.Popen(f'{NEMO_DESKTOP_NAME}')

    def _RestartNemoDesktop():
        IcMan._KillNemoDesktop()
        IcMan._StartNemoDesktop()

#   def ShakeIcon(_fp):
#       name = gfjn(_fp)
#       tmp_fp = f'{HOME_DIR}/{name}.{DATA_FILE_EXT}'
#       os.rename(_fp, tmp_fp)
#       os.rename(tmp_fp, _fp)
#       # print ("Moved: ", _fp, " <==> ", tmp_fp)

    def ApplyConfig(self, name_):

        if name_ not in self.configs:
            return

        icons = self.configs[name_]
        meta_icons = []

        IcMan._KillNemoDesktop()
        for o in icons:

            if o.fp != META_PATH_HOLDER:
                cmd = GIO_SET_ICONS_POS_CMD_TPL.format(o.fp, o.x, o.y)
                subprocess.run(cmd, shell=True)
                cmd = GIO_SET_ICONS_MON_CMD_TPL.format(o.fp, o.m)
                subprocess.run(cmd, shell=True)
            else:
                meta_icons.append(o)

            # IcMan.ShakeIcon(o.fp)

        IcMan._ApplyNemoMetaDesktop(NEMO_META_PATH, meta_icons)
        IcMan._StartNemoDesktop()

    def GetConfigFullPath(name_):
        fp = f'{CONFIG_DIR}/{name_}.{DATA_FILE_EXT}'
        return fp

    def DeleteConfig(self, name_):

        fp = IcMan.GetConfigFullPath(name_)
        print('CTD: ', fp)
        if os.path.exists(fp):
            os.remove(fp)
        self.configs.pop(name_, None)

    def Rename(self, new_name_, old_name_):

        if new_name_ != old_name_:
            fp_old = IcMan.GetConfigFullPath(old_name_)
            fp_new = IcMan.GetConfigFullPath(new_name_)
            print(f'CTR: {fp_old} => {fp_new}')

            if os.path.exists(fp_old):
                if os.path.exists(fp_new):
                    os.remove(fp_new)
                os.rename(fp_old, fp_new)
            self.configs[new_name_] = self.configs.pop(old_name_)


############################################################################


GRID_LB_VERT_SIZE = 6


class MainWnd:

    def __init__(self, root_, icman_):

        self.icman = icman_
        self.root = root_

        root_.title("Icons manager")
        root_.geometry('520x300')

        mainframe = ttk.Frame(root_, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root_.columnconfigure(0, weight=1)
        root_.rowconfigure(0, weight=1)

        self.config_names_var = StringVar()
        self._RefreshList()

        self.lbox = Listbox(mainframe, height=18, width=50,
                            listvariable=self.config_names_var)
        self.lbox.grid(column=0, row=0, rowspan=GRID_LB_VERT_SIZE,
                       sticky=(N, S, E, W))
        self.lbox.bind("<Double-1>", lambda e: self.ApplyConfig())

        scrollbar = Scrollbar(mainframe, orient="vertical")
        scrollbar.config(command=self.lbox.yview)
        self.lbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(column=1, row=0, rowspan=GRID_LB_VERT_SIZE, sticky=N+S)

        ttk.Button(mainframe, text="Save",
                   command=self.SaveCurrentConfig).grid(
                       column=3, row=0, sticky=W)
        ttk.Button(mainframe, text="Del",
                   command=self.DeleteCurrentConfig).grid(
                        column=3, row=1, sticky=W)
        ttk.Button(mainframe, text="Rename",
                   command=self.Rename).grid(
                       column=3, row=2, sticky=W)
        # ttk.Button(mainframe, text="Apply",
        #            command=self.ApplyConfig).grid(
        #                column=3, row=2, sticky=E)

    def _RefreshList(self):

        names_ts = []
        names = list(self.icman.configs.keys())
        for n in names:
            n_ts = MainWnd._GenConfigName(IcMan.GetConfigFullPath(n))
            names_ts.append(n_ts)

        self.config_names = names_ts
        self.config_names.sort(reverse=True)
        self.config_names_var.set(self.config_names)

    def SaveCurrentConfig(self):
        self.icman.SaveCurrentConfig()
        self._RefreshList()
#        #print("configs: ", self.config_names)

    def _CurrConfigName(self):
        idxs = self.lbox.curselection()
        idx = 0 if len(idxs) <= 0 else int(idxs[0])
        name = self.lbox.get(idx)
        return name

    def _CurrConfigNameEx(self):
        return MainWnd._ExtractConfigName(self._CurrConfigName())

    def ApplyConfig(self):
        name = self._CurrConfigNameEx()
        self.icman.ApplyConfig(name)

    def DeleteCurrentConfig(self):
        name = self._CurrConfigNameEx()
        self.icman.DeleteConfig(name)
        self._RefreshList()
        # print("configs: ", self.config_names)

    def Rename(self):
        old_name = self._CurrConfigNameEx()
        new_name = simpledialog.askstring("Rename", "Enter new name",
                                          parent=self.root,
                                          initialvalue=old_name)
        if new_name is not None:
            self.icman.Rename(new_name, old_name)
            self._RefreshList()

    def _GenConfigName(fp_):
        ts = os.path.getmtime(fp_)
        dt = datetime.datetime.fromtimestamp(ts)
        tm_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        nm_str = gfjn(fp_)
        s = f'{tm_str}    {nm_str}'
        return s

    def _ExtractConfigName(gen_name_):
        s = gen_name_.split()[2]
        return s


def GuiMain(icman_):
    root = Tk()
    MainWnd(root, icman_)
    root.mainloop()


def main():

    if shutil.which('gio') is None:
        print('gio not found')
        return 1

    if shutil.which(f'{NEMO_DESKTOP_NAME}') is None:
        print(f'{NEMO_DESKTOP_NAME} not found')
        return 1

    icman = IcMan()
    GuiMain(icman)
    return 0

# SaveIcons()


if __name__ == "__main__":
    main()
