import time

from pynput import mouse

def on_move(x, y):
    print('{1} Pointer moved to {0}'.format(
        (x, y), time.time()))

def on_click(x, y, button, pressed):
    print('{3} {0} at {1} {2}'.format(
        'Pressed' if pressed else 'Released',
        (x, y), button, time.time()))

if __name__ == '__main__':

    # Collect events until released
    with mouse.Listener(
            on_move=on_move,
            on_click=on_click) as listener:
        listener.join()