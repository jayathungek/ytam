from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import Text, Frame, Layout, Label, Divider
import queue
import argparse
from asciimatics.exceptions import StopApplication, ResizeScreenError
from asciimatics.event import KeyboardEvent
import sys
import random
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from multiprocessing import Process, Event, Queue, Pool
from threading import Thread
import time
from bidict import bidict
from pytube import Playlist
import re

from title import TitleGenerator
from downloader import YTDL
import progress
import error


def del_ctrl(ctrl_key):
    key = ctrl_key.split("_")
    return key[1]


def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def same_sign(n1, n2):
    return (n1 * n2) > 0

def pos_index(index, len_list):    
    return index + len_list if index < 0 else index

PLAYLIST_OK = "Playlist ok, initialising download ..."
PLAYLIST_ERR = "Playlist has the wrong number of songs."
INTERNAL_ERR = "Internal Error."
INTERNAL_ERR_PROMPT = "Internal error - retry?"
RETRYING = "Retrying..."
SKIP = "Skipped failed songs."
NO_LOGS = "No log items to show."
RETRY_DOWNLOAD = "Some songs failed to download. Try downloading them again?"
RETRY_DOWNLOAD_MSG = "Some songs failed to download."
CANCEL_DOWNLOAD = "Download cancelled."
WELCOME = "Welcome to YouTube Album Maker! Please input a command."
FIX_ERR = "Some invalid inputs were found. Please fix them to continue."

# keys that are recognised by the program
KEY_CODES = {
    0: "CTRL_SPACE",
    2: "CTRL_B",
    4: "CTRL_D",
    5: "CTRL_E",
    6: "CTRL_F",
    7: "CTRL_G",
    12: "CTRL_L",
    14: "CTRL_N",
    18: "CTRL_R",
    24: "CTRL_X",
    25: "CTRL_Y",
}

# use this to remap keys
COMMANDS = bidict(
    {
        "CTRL_G": "HELP",
        "CTRL_L": "LOGS",
        "CTRL_Y": "YES",
        "CTRL_X": "NO",
        "CTRL_N": "NEXT",
        "CTRL_B": "BACK",
        "CTRL_E": "EXIT",
        "CTRL_D": "DISMISS",
        "CTRL_R": "RETRY",
        "CTRL_F": "CANCEL",
        "CTRL_SPACE": "DOWNLOAD",
    }
)

HELP_TEXTS = [
    "HELP [1/7]: URL - target URL of the playlist to download.",
    "HELP [2/7]: DIR - download directory (defaults to current directory).",
    "HELP [3/7]: TIL - path to file containing names of the songs in the playlist (each on a new line).",
    "HELP [4/7]: ALB - name of the album the songs in the playlist belongs to (defaults to playlist title).",
    "HELP [5/7]: ART - name of the artist that performed the songs in the playlist (defaults to Unknown).",
    "HELP [6/7]: STA - the position in the playlist of the first song in the album (zero-indexed, defaults to 0).",
    "HELP [7/7]: END - the position in the playlist of the last song in the album (zero-indexed, defaults to -1).",
]

START_PROMPT = {
    "commands": ["HELP", "EXIT", "DOWNLOAD", "LOGS"],
    "text": (
        "<ctrl+{} - start download |"
        " ctrl+{} - help |"
        " ctrl+{} - logs |"
        " ctrl+{} - exit>"
    ).format(
        del_ctrl(COMMANDS.inverse["DOWNLOAD"]),
        del_ctrl(COMMANDS.inverse["HELP"]),
        del_ctrl(COMMANDS.inverse["LOGS"]),
        del_ctrl(COMMANDS.inverse["EXIT"]),
    ),
}

CYCLE_PROMPT = {
    "commands": ["EXIT", "BACK", "NEXT", "DISMISS"],
    "text": ("<ctrl+{} - back |" " ctrl+{} - next |" " ctrl+{} - dismiss>").format(
        del_ctrl(COMMANDS.inverse["BACK"]),
        del_ctrl(COMMANDS.inverse["NEXT"]),
        del_ctrl(COMMANDS.inverse["DISMISS"]),
    ),
}

INPUT_PROMPT = {
    "commands": ["YES", "NO"],
    "text": ("<ctrl+{} - yes |" " ctrl+{} - no>").format(
        del_ctrl(COMMANDS.inverse["YES"]), del_ctrl(COMMANDS.inverse["NO"])
    ),
}

DOWNLOAD_PROMPT = {
    "commands": ["CANCEL"],
    "text": ("<ctrl+{} - cancel download>").format(
        del_ctrl(COMMANDS.inverse["CANCEL"])
    ),
}

METADATA_PROMPT = {
    "commands": ["CANCEL"],
    "text": ("<ctrl+{} - cancel>").format(del_ctrl(COMMANDS.inverse["CANCEL"])),
}

GUI_STATES = {
    "start": {
        "name": "start",
        "commands": START_PROMPT["commands"],
        "prompt_text": START_PROMPT["text"],
    },
    "help": {
        "name": "help",
        "commands": CYCLE_PROMPT["commands"],
        "prompt_text": CYCLE_PROMPT["text"],
    },
    "logs": {
        "name": "logs",
        "commands": CYCLE_PROMPT["commands"],
        "prompt_text": CYCLE_PROMPT["text"],
    },
    "checking_playlist": {
        "name": "checking_playlist",
        "commands": INPUT_PROMPT["commands"],
        "prompt_text": INPUT_PROMPT["text"],
    },
    "init_download_err": {
        "name": "init_download_err",
        "commands": INPUT_PROMPT["commands"],
        "prompt_text": INPUT_PROMPT["text"],
    },
    "downloading_song": {
        "name": "downloading_song",
        "commands": DOWNLOAD_PROMPT["commands"],
        "prompt_text": DOWNLOAD_PROMPT["text"],
    },
    "setting_metadata": {
        "name": "setting_metadata",
        "commands": METADATA_PROMPT["commands"],
        "prompt_text": METADATA_PROMPT["text"],
    },
    "retry_download": {
        "name": "retry_download",
        "commands": INPUT_PROMPT["commands"],
        "prompt_text": INPUT_PROMPT["text"],
    },
}


class Console:
    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.display_widget = Label(WELCOME)
        self.prompt_widget = Label(START_PROMPT["text"], align=">")
        self.display_widget._name = "console_display"
        self.display_widget.disabled = True
        self.display_widget.custom_colour = "field"

        self.prompt_widget._name = "console_prompt"
        self.prompt_widget.disabled = True
        self.prompt_widget.custom_colour = "button"

        self.debug_widget = None

        self.available_commands = START_PROMPT["commands"]
        self.log_events = []
        self.log = []
        self.help_index = 0
        self.log_index = 0

        self.downloader = YTDL()
        self.url = None
        self.dir = None
        self.til = None
        self.alb = None
        self.art = None
        self.sta = 0
        self.end = -1
        self.title_list = []

        self.download_t = None

        self.init_complete = False
        self.init_q = Queue()
        self.download_q = Queue()

        self.state = "start"
        self.expression = re.compile(
            r"^((http(s)?:\/\/)?(www\.)?youtube\.com\/playlist\?list=([^ \t\n\r]){5,50})$"
        )

    def check_playlist(self):
        if self.url == None:
            raise error.EmptyUrlFieldError

        matches = self.expression.match(self.url)
        if matches is None:
            raise error.InvalidUrlError(self.url)

        playlist = Playlist(self.url)
        if len(playlist) == 0:
            raise error.InvalidPlaylistError()

        if not represents_int(self.sta):
            raise error.InvalidFieldError("STA", f"{self.sta} is not an integer")

        if not represents_int(self.end):
            raise error.InvalidFieldError("END", f"{self.end} is not an integer")

        start_index = pos_index(int(self.sta), len(playlist))
        end_index = pos_index(int(self.end), len(playlist))

        if end_index < start_index:
            raise error.IndicesOutOfOrderError()
        

        if not start_index < len(playlist):
            raise error.InvalidPlaylistIndexError(start_index, playlist.title())
        
        if not end_index < len(playlist):
            raise error.InvalidPlaylistIndexError(end_index, playlist.title())

        self.sta = start_index
        self.end = end_index




    def debug(self, text):
        if self.debug_mode:
            self.debug_widget._text = text

    def make_log(self):
        num = 1
        total = len(self.log_events)
        self.log = []
        for string in self.log_events:
            new_string = "LOG [{}/{}]: ".format(num, total) + string
            self.log.append(new_string)
            num += 1

    def set_state(self, state):
        self.state = state["name"]
        self.available_commands = state["commands"]
        self.prompt_widget._text = state["prompt_text"]

    def reset_display(self, text=""):
        self.display_widget._text = text

    async def run_command(self, command):

        command = COMMANDS[command]

        if command in self.available_commands:
            if command == "EXIT":
                if self.downloader is not None:
                    self.downloader.stop()
                sys.exit(0)

            elif command == "HELP":
                self.set_state(GUI_STATES["help"])
                self.display_widget._text = HELP_TEXTS[self.help_index]

            elif command == "LOGS":
                self.make_log()
                self.set_state(GUI_STATES["logs"])
                self.display_widget._text = (
                    self.log[self.log_index] if len(self.log) > 0 else NO_LOGS
                )

            elif command == "NEXT":
                if self.state == "help":
                    self.next_help()
                    self.display_widget._text = HELP_TEXTS[self.help_index]

                elif self.state == "logs" and len(self.log) > 0:
                    self.next_log()
                    self.display_widget._text = self.log[self.log_index]

            elif command == "BACK":

                if self.state == "help":
                    self.prev_help()
                    self.display_widget._text = HELP_TEXTS[self.help_index]

                elif self.state == "logs" and len(self.log) > 0:
                    self.prev_log()
                    self.display_widget._text = self.log[self.log_index]

            elif command == "YES":
                self.reset_display()
                if self.state == "checking_playlist":
                    self.downloader.testflag = ""
                    self.status_widget._text = PLAYLIST_OK
                    self.log_events.append(PLAYLIST_OK)
                    self.downloader.set_can_download()
                    self.available_commands = DOWNLOAD_PROMPT["commands"]
                    self.prompt_widget._text = DOWNLOAD_PROMPT["text"]
                    self.bar_widget._text = progress.bar(0, 128)

                elif self.state == "init_download_err":
                    self.bar_widget._text = ""
                    self.init_complete = False
                    self.downloader.reset()
                    self.downloader.pass_params(
                        self.url,
                        self.alb,
                        self.art,
                        self.title_list,
                        self.dir,
                        int(self.sta),
                        int(self.end),
                        self.download_q,
                    )
                    self.downloader.start()
                    self.downloader.set_init()
                    self.set_state(GUI_STATES["start"])
                    self.status_widget._text = RETRYING

                    self.download_t = Thread(target=self.downloader.main_loop)
                    self.download_t.setDaemon(True)
                    self.download_t.start()

                elif self.state == "retry_download":
                    self.log_events.append(RETRYING)
                    self.debug("retrying failed songs ...")
                    self.downloader.set_can_download()
                    self.available_commands = DOWNLOAD_PROMPT["commands"]
                    self.prompt_widget._text = DOWNLOAD_PROMPT["text"]
                    self.bar_widget._text = progress.bar(0, 128)

            elif command == "NO":
                self.init_complete = False
                self.reset_display()
                if self.state == "checking_playlist":
                    if self.downloader is not None:
                        self.downloader.set_init()
                        self.log_events.append(PLAYLIST_ERR)
                        self.log_events.append(RETRYING)
                        self.status_widget._text = RETRYING
                        self.available_commands = START_PROMPT["commands"]
                        self.prompt_widget._text = START_PROMPT["text"]

                elif (
                    self.state == "init_download_err" or self.state == "retry_download"
                ):
                    self.log_events.append(SKIP)
                    self.bar_widget._text = ""
                    self.status_widget._text = SKIP
                    self.set_state(GUI_STATES["start"])
                    self.reset_display(WELCOME)

            elif command == "DISMISS":
                self.set_state(GUI_STATES["start"])
                self.reset_display(WELCOME)
                self.help_index = 0
                self.log_index = 0

            elif command == "DOWNLOAD":
                try:
                    self.check_playlist()
                    if self.til is not None:
                        tg = TitleGenerator(self.til, self.art)
                        tg.make_titles()
                        self.title_list = tg.get_titles()
                except (
                    error.InvalidUrlError,
                    error.InvalidPlaylistError,
                    error.BadTitleFormatError,
                    error.TitlesNotFoundError,
                    error.InvalidPlaylistIndexError,
                    error.InvalidFieldError,
                    error.EmptyUrlFieldError,
                    error.IndicesOutOfOrderError
                ) as err:
                    err_msg = f"ERR: {err.message}"
                    self.display_widget._text = err_msg
                    self.log_events.append(err_msg)
                    return

                self.status_widget._text = f"{str(self.url)}, {str(self.alb)}, {str(self.art)}, {str(self.til)}, {str(self.dir)}, {str(self.sta)}"
                self.bar_widget._text = ""
                self.downloader.reset()
                self.downloader.pass_params(
                    self.url,
                    self.alb,
                    self.art,
                    self.title_list,
                    self.dir,
                    int(self.sta),
                    int(self.end),
                    self.download_q,
                )
                self.downloader.start()
                self.downloader.set_init()

                self.download_t = Thread(target=self.downloader.main_loop)
                self.download_t.setDaemon(True)
                self.download_t.start()

            elif command == "CANCEL":
                self.downloader.stop()
                self.downloader.reset()
                self.init_complete = False
                self.log_events.append(CANCEL_DOWNLOAD)
                self.status_widget._text = CANCEL_DOWNLOAD
                self.bar_widget._text = ""
                self.set_state(GUI_STATES["start"])
                self.reset_display(WELCOME)

    def next_help(self):
        next_index = self.help_index + 1
        if next_index == len(HELP_TEXTS):
            next_index = 0
        self.help_index = next_index

    def prev_help(self):
        prev_index = self.help_index - 1
        if prev_index == -1:
            prev_index = len(HELP_TEXTS) - 1
        self.help_index = prev_index

    def next_log(self):
        next_index = self.log_index + 1
        if next_index == len(self.log):
            next_index = 0
        self.log_index = next_index

    def prev_log(self):
        prev_index = self.log_index - 1
        if prev_index == -1:
            prev_index = len(self.log) - 1
        self.log_index = prev_index


class GUI:
    def __init__(self, debug_mode):
        self.frame = None
        self.console = Console(debug_mode)
        self.first_dl_begun = False

    def disable_inputs(self):
        if self.frame is not None:
            self.frame.find_widget("url_field").blur()
            self.frame.find_widget("url_field").disabled = True

            self.frame.find_widget("dir_field").blur()
            self.frame.find_widget("dir_field").disabled = True

            self.frame.find_widget("til_field").blur()
            self.frame.find_widget("til_field").disabled = True

            self.frame.find_widget("alb_field").blur()
            self.frame.find_widget("alb_field").disabled = True

            self.frame.find_widget("art_field").blur()
            self.frame.find_widget("art_field").disabled = True

            self.frame.find_widget("sta_field").blur()
            self.frame.find_widget("sta_field").disabled = True

            self.frame.find_widget("end_field").blur()
            self.frame.find_widget("end_field").disabled = True

    def enable_inputs(self):
        if self.frame is not None:
            self.frame.find_widget("url_field").disabled = False
            self.frame.find_widget("dir_field").disabled = False
            self.frame.find_widget("til_field").disabled = False
            self.frame.find_widget("alb_field").disabled = False
            self.frame.find_widget("art_field").disabled = False
            self.frame.find_widget("sta_field").disabled = False
            self.frame.find_widget("end_field").disabled = False

    def url_changed(self):
        value = self.frame.find_widget("url_field").value
        self.console.url = (
            value
            if value is not ""
            else None
            # else "https://www.youtube.com/playlist?list=PLOoPqX_q5JAUnH2ZsoTXT8nIKKKEyNVbK"
        )

    def dir_changed(self):
        value = self.frame.find_widget("dir_field").value
        self.console.dir = value if value is not "" else "./test/"

    def til_changed(self):
        value = self.frame.find_widget("til_field").value
        self.console.til = value if value is not "" else "./titles.txt"

    def alb_changed(self):
        value = self.frame.find_widget("alb_field").value
        self.console.alb = value if value is not "" else None

    def art_changed(self):
        value = self.frame.find_widget("art_field").value
        self.console.art = value if value is not "" else "Unknown"

    def sta_changed(self):
        value = self.frame.find_widget("sta_field").value
        self.console.sta = value if value is not "" else 0

    def end_changed(self):
        value = self.frame.find_widget("end_field").value
        self.console.end = value if value is not "" else -1

    def make(self):
        url_field = Text(label="URL:", name="url_field", on_change=self.url_changed)
        dir_field = Text(label="DIR:", name="dir_field", on_change=self.dir_changed)
        til_field = Text(label="TIL:", name="til_field", on_change=self.til_changed)
        alb_field = Text(label="ALB:", name="alb_field", on_change=self.alb_changed)
        sta_field = Text(label="STA:", name="sta_field", on_change=self.sta_changed)
        end_field = Text(label="END:", name="end_field", on_change=self.end_changed)
        art_field = Text(label="ART:", name="art_field", on_change=self.art_changed)

        status_label = Label("")
        status_label._name = "status_label"
        status_label.disabled = True
        status_label.custom_colour = "edit_text"
        self.console.status_widget = status_label

        if self.console.debug_mode:
            debug_label = Label("")
            debug_label._name = "debug_label"
            debug_label.disabled = True
            debug_label.custom_colour = "edit_text"
            self.console.debug_widget = debug_label

        console_display = self.console.display_widget
        console_prompt = self.console.prompt_widget

        download_bar = Label("")
        download_bar._name = "download_bar"
        download_bar.disabled = True
        self.console.bar_widget = download_bar

        prompt = Label("")

        params_div = Divider()
        params_div.custom_colour = "title"

        status_div = Divider()
        status_div.custom_colour = "title"

        debug_div = Divider()
        debug_div.custom_colour = "title"

        params_layout = Layout([1])
        self.frame.add_layout(params_layout)
        params_layout.add_widget(url_field)
        params_layout.add_widget(dir_field)
        params_layout.add_widget(til_field)

        params_layout2 = Layout([40, 40, 10, 10])
        self.frame.add_layout(params_layout2)
        params_layout2.add_widget(alb_field)
        params_layout2.add_widget(art_field, column=1)
        params_layout2.add_widget(sta_field, column=2)
        params_layout2.add_widget(end_field, column=3)

        status_layout = Layout([1])
        self.frame.add_layout(status_layout)
        status_layout.add_widget(params_div)
        status_layout.add_widget(status_label)
        status_layout.add_widget(download_bar)
        status_layout.add_widget(status_div)
        status_layout.add_widget(console_display)
        status_layout.add_widget(console_prompt)

        if self.console.debug_mode:
            status_layout.add_widget(debug_div)
            status_layout.add_widget(debug_label)

    def global_shortcuts(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c in KEY_CODES.keys():
                command = KEY_CODES[c]
                async_to_sync(self.console.run_command)(command)
            else:
                self.console.debug(str(c))

    def draw(self, screen, scene):
        APP_WIDTH = 140
        APP_HEIGHT = 14 if self.console.debug_mode else 12

        self.frame = Frame(
            screen,
            APP_HEIGHT,
            APP_WIDTH,
            has_border=True,
            title="YouTube Album Maker",
            can_scroll=False,
        )
        # (foreground colour, attr, background colour)
        self.frame.palette["background"] = (
            Screen.COLOUR_WHITE,
            Screen.A_BOLD,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["borders"] = (
            Screen.COLOUR_RED,
            Screen.A_NORMAL,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["label"] = (
            Screen.COLOUR_WHITE,
            Screen.A_BOLD,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["edit_text"] = (
            Screen.COLOUR_WHITE,
            Screen.A_NORMAL,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["focus_edit_text"] = (
            Screen.COLOUR_WHITE,
            Screen.A_BOLD,
            Screen.COLOUR_RED,
        )
        self.frame.palette["disabled"] = (
            Screen.COLOUR_WHITE,
            Screen.A_BOLD,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["title"] = (
            Screen.COLOUR_WHITE,
            Screen.A_BOLD,
            Screen.COLOUR_RED,
        )
        self.frame.palette["field"] = (
            Screen.COLOUR_WHITE,
            Screen.A_NORMAL,
            Screen.COLOUR_BLACK,
        )
        self.frame.palette["scroll"] = (
            Screen.COLOUR_RED,
            Screen.A_NORMAL,
            Screen.COLOUR_RED,
        )

        self.frame.palette["button"] = (
            Screen.COLOUR_YELLOW,
            Screen.A_NORMAL,
            Screen.COLOUR_BLACK,
        )
        self.make()
        self.frame.fix()
        scenes = [Scene([self.frame], -1, name="App")]
        screen.set_scenes(
            scenes, start_scene=scene, unhandled_input=self.global_shortcuts
        )

    def run(self):
        screen = Screen.open()
        self.draw(screen, None)
        while True:
            try:
                screen.draw_next_frame(repeat=True)
                if screen.has_resized():
                    screen._scenes[screen._scene_index].exit()
                    raise ResizeScreenError(
                        "Screen resized", screen._scenes[screen._scene_index]
                    )
                time.sleep(0.05)

                self.console.debug(
                    f"init set: {self.console.downloader.init.is_set()}, downloader loop: {str(self.console.downloader.count)}, init complete: {self.console.init_complete}, download: {self.console.downloader.testflag}"
                )

                init = []

                # if self.console.state not in ["start", "help", "logs"]:
                #     self.disable_inputs()
                # else:
                #     self.enable_inputs()

                while not self.console.download_q.empty():
                    if not self.console.init_complete:
                        if not self.console.downloader.is_stopped():
                            event, message = self.console.download_q.get_nowait()
                            init.append((event, message))
                            if event == "OK_IN":
                                self.console.init_complete = True
                                _, playlist_len_msg = init[0]
                                _, album_msg = init[1]
                                _, total_items_msg = init[2]

                                playlist_len = playlist_len_msg["value"]
                                playlist_name = album_msg["value"]
                                total_items = total_items_msg["value"]
                                self.console.display_widget._text = f"{total_items}/{playlist_len} items found in playlist {self.console.downloader.playlist_title} - Is this correct?"
                                self.console.set_state(GUI_STATES["checking_playlist"])
                        else:
                            break

                    else:
                        if not self.console.downloader.is_stopped():
                            event, message = self.console.download_q.get_nowait()

                            if event == "INPUT":
                                self.first_dl_begun = False
                                if message["text"] == "internal":
                                    self.console.bar_widget._text = ""
                                    self.console.set_state(
                                        GUI_STATES["init_download_err"]
                                    )
                                    self.console.log_events.append(INTERNAL_ERR)
                                    self.console.status_widget._text = INTERNAL_ERR
                                    self.console.display_widget._text = (
                                        INTERNAL_ERR_PROMPT
                                    )
                                    self.console.downloader.stop()
                                    break
                                elif message["text"] == "retry":
                                    self.console.log_events.append(RETRY_DOWNLOAD_MSG)
                                    self.console.status_widget._text = (
                                        RETRY_DOWNLOAD_MSG
                                    )
                                    self.console.set_state(GUI_STATES["retry_download"])

                                    self.console.display_widget._text = RETRY_DOWNLOAD
                                    self.console.bar_widget._text = ""
                                    break

                            if event == "DL" and not self.first_dl_begun:
                                # first download has begun
                                self.console.bar_widget._text = progress.bar(0, 128)
                                self.first_dl_begun = True

                            if event == "OK_DL" or event == "ERR_DL":
                                self.console.bar_widget._text = progress.bar(
                                    message["arg"]
                                    / len(self.console.downloader.to_download),
                                    128,
                                )

                            if event == "END_MD":
                                self.first_dl_begun = False
                                self.console.debug(self.console.downloader.testflag)

                                self.console.log_events.append(message["text"])
                                self.console.status_widget._text = message["text"]
                                self.console.set_state(GUI_STATES["start"])
                                self.console.reset_display(WELCOME)

                                if not self.console.downloader.has_retries():
                                    self.console.downloader.stop()
                                    self.console.downloader.reset()
                                    self.console.init_complete = False
                                    break

                            if event == "STOP":
                                self.first_dl_begun = False
                                self.console.log_events.append(message["text"])
                                self.console.set_state(GUI_STATES["start"])
                                self.console.reset_display(WELCOME)
                                self.console.downloader.reset()
                                break

                            self.console.log_events.append(message["text"])
                            self.console.status_widget._text = message["text"]
                        else:
                            while not self.console.download_q.empty():
                                event, message = self.console.download_q.get_nowait()
                            break

            except (KeyboardInterrupt, SystemExit):
                screen.close()
                break
            except ResizeScreenError as e:
                self.draw(screen, e.scene)

        sys.exit(0)


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        action="store_true",
        help="shows debug information at the bottom of the app",
    )
    return parser.parse_args(args)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    g = GUI(args.debug)
    g.run()
