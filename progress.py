def bar(ratio, l):
    filled = round(ratio * l)
    completed = "█" * filled
    empty = "-" * (l - filled)
    percent = round(ratio * 100)
    bar = "|{complete}{empty}| - {percent}%".format(
        complete=completed, empty=empty, percent=percent
    )
    return bar


def spinner(i, speed=30):
    cycle = "|/―\\"
    if i == 0:
        index = 0
    else:
        index = int((i - 1) / speed) % (len(cycle))
    return cycle[index]


def demo(screen):
    items = [
        {"name": "Title 1", "steps": 234},
        {"name": "Another Title", "steps": 190},
        {"name": "extrme 123 title", "steps": 200},
        {"name": "I don have idea", "steps": 100},
        {"name": "top 10 monkys", "steps": 500},
    ]
    l = len(items)
    percent = 0
    i = 0
    while percent < 1.0:
        item = items[i]
        item_name = item["name"]
        item_steps = item["steps"]
        percent += round(1 / l, 2)
        screen.print_at(
            bar(percent, 60), 0, 1,
        )
        for j in range(item_steps):
            screen.print_at("Downloading {} ... {}".format(item_name, spinner(j)), 0, 0)
            screen.refresh()
        screen.print_at("Downloading {} ... done.".format(item_name), 0, 0)
        percent += round(1 / l, 2)
        i += 1

        ev = screen.get_key()
        if ev in (ord("Q"), ord("q")):
            return
        screen.refresh()


if __name__ == "__main__":
    from random import randint
    from asciimatics.screen import Screen

    Screen.wrapper(demo)
