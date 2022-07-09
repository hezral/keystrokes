from pynput import keyboard

mod_state = False

mod_keys = [keyboard.Key.shift, keyboard.Key.alt, keyboard.Key.ctrl, keyboard.Key.cmd, "<65032>"]
mod_key_detected = []

def on_press(key):
    global mod_state
    global mod_key_detected

    if key in mod_keys:
        mod_state = True
        mod_key_detected.append(key)
    else:
        try:
            if mod_state:
                print("pressed", mod_key_detected, key)
                mod_state = False
                mod_key_detected = []
            else:
                print("presed", key)
        except Exception as e:
            print(e)

def on_release(key):
    global mod_state
    global mod_key_detected

    if key in mod_keys or str(key) in mod_keys:
        if mod_state:
            if len(mod_key_detected) == 1:
                print("released", key)
            else:
                print("released", mod_key_detected, key)
            mod_state = False
            mod_key_detected = []
    else:
        print("released", key)


# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=None) as listener:
    listener.join()