#!/usr/bin/env python3

"example of using pynput..."

import sys
import time

import pynput


def start_listeners():
    "listener threads for mouse and keyboard events"
    def handle_mouse_input(*args):
        "handle mouse events"
        print("mouse:", repr(args), file=sys.stderr)

    def handle_kbd_input(*args):
        "handle keyboard events"
        print("kbd:", repr(args), file=sys.stderr)

    # kb_listen = pynput.keyboard.Listener(on_press=handle_kbd_input,
    #                                      on_release=handle_kbd_input)
    # kb_listen.start()
    # mouse_listen = pynput.mouse.Listener(on_click=handle_mouse_input,
    #                                      on_scroll=handle_mouse_input,
    #                                      on_move=handle_mouse_input)
    # mouse_listen.start()

    # The event listener will be running in this block
    with pynput.mouse.Events() as events:
        for event in events:
            print("event:", repr(event))
            print(dir(event))

def main():
    start_listeners()
    while True:
        time.sleep(0.25)
    return 0


if __name__ == "__main__":
    sys.exit(main())
