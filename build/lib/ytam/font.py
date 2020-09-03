HEADER = "\033[95m"
OKBLUE = "\033[94m"
OKGREEN = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"


def header(text):
    return f"{HEADER}{text}{ENDC}"


def ok_blue(text):
    return f"{OKBLUE}{text}{ENDC}"


def ok_green(text):
    return f"{OKGREEN}{text}{ENDC}"


def warning(text):
    return f"{WARNING}{text}{ENDC}"


def fail(text):
    return f"{FAIL}{text}{ENDC}"


def bold(text):
    return f"{BOLD}{text}{ENDC}"


def underline(text):
    return f"{UNDERLINE}{text}{ENDC}"


lookup = {
    "h": header,
    "l": ok_blue,
    "g": ok_green,
    "w": warning,
    "f": fail,
    "b": bold,
    "u": underline,
}


def apply(params, text):
    formatted_text = text
    for style in params:
        formatted_text = lookup[style](formatted_text)

    return formatted_text
