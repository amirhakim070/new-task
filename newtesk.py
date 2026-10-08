
import paho.mqtt.client as mqtt
import sys
import tty
import termios
import time
import json
from pathlib import Path

# ==========================================
# MQTT SETTINGS
# ==========================================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "greenhouse/button"

# ==========================================
# COUNT SETTINGS
# ==========================================

COUNT_FILE = Path.home() / "keyboard_count.txt"

try:
    count = max(0, int(COUNT_FILE.read_text()))
except (FileNotFoundError, ValueError):
    count = 0

mode = "STOP"

# ==========================================
# MQTT CLIENT
# ==========================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

try:
    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    client.loop_start()
    print("MQTT connection started!")

except Exception as e:
    print("MQTT connection failed:", e)
    sys.exit(1)

# ==========================================
# GET KEYBOARD INPUT
# ==========================================

def get_key():

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings
        )

    return key

# ==========================================
# SAVE COUNT
# ==========================================

def save_count():
    COUNT_FILE.write_text(str(count))

# ==========================================
# PUBLISH MQTT
# ==========================================

def publish_data(button, status):

    payload = {
        "button": button,
        "status": status,
        "mode": mode,
        "count": count,
        "timestamp": time.time()
    }

    message = json.dumps(payload)

    try:
        result = client.publish(
            MQTT_TOPIC,
            message,
            qos=1
        )

        result.wait_for_publish(timeout=3)

        print("\n--------------------------")
        print("BUTTON:", button)
        print("STATUS:", status)
        print("MODE:", mode)
        print("TOTAL COUNT:", count)

        if result.is_published():
            print("MQTT SENT:", message)
        else:
            print("MQTT delivery not confirmed")

        print("--------------------------")

    except Exception as e:
        print("MQTT publish error:", e)

# ==========================================
# PROGRAM INFORMATION
# ==========================================

print("==============================")
print(" Raspberry Pi 5 MQTT Counter")
print("==============================")
print("0 = STOP")
print("1 = RUN")
print("2 = DELAY")
print("3 = COUNT DOWN (-1)")
print("4 = COUNT UP (+1)")
print("ESC = EXIT")
print("==============================")
print("Current Count:", count)
print("Current Mode:", mode)
print("==============================")

# ==========================================
# MAIN PROGRAM
# ==========================================

try:

    while True:

        key = get_key()

        # KEY 0 = STOP
        if key == "0":

            mode = "STOP"
            publish_data("0", "STOP")

        # KEY 1 = RUN
        elif key == "1":

            mode = "RUN"
            publish_data("1", "RUN")

        # KEY 2 = DELAY
        elif key == "2":

            mode = "DELAY"
            publish_data("2", "DELAY")

        # KEY 3 = COUNT DOWN
        elif key == "3":

            if mode == "RUN":

                count = max(0, count - 1)
                save_count()
                publish_data("3", "DOWN")

            else:
                print("\nCounting paused. Press 1 to RUN.")

        # KEY 4 = COUNT UP
        elif key == "4":

            if mode == "RUN":

                count += 1
                save_count()
                publish_data("4", "UP")

            else:
                print("\nCounting paused. Press 1 to RUN.")

        # ESC = EXIT
        elif key == "\x1b" or key == "\x03":

            mode = "STOP"
            publish_data("ESC", "STOP")
            print("\nStopping program...")
            break

# ==========================================
# CLEAN UP
# ==========================================

except KeyboardInterrupt:
    print("\nProgram interrupted.")

finally:

    client.loop_stop()
    client.disconnect()

    print("MQTT disconnected.")
    print("Final Count:", count)
