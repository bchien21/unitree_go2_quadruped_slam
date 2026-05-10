#!/usr/bin/env python3
"""Keyboard teleop for Go2 using unitree_sdk2_python SportClient."""

import sys
import tty
import termios
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

BANNER = """
------------------------------------------
  Go2 Keyboard Teleop  (unitree_sdk2py)
------------------------------------------
  Moving:        w
               a s d
  Turn:        q       e
  Stand up:    u
  Stand down:  j
  Recovery:    r
  Stop:        SPACE
  Quit:        ESC / Ctrl-C
------------------------------------------
  vx = {vx:.2f}  vy = {vy:.2f}  vyaw = {vyaw:.2f}
"""

VX_STEP = 0.2
VY_STEP = 0.2
VYAW_STEP = 0.3
VX_MAX = 1.0
VY_MAX = 0.5
VYAW_MAX = 1.5


def get_key(fd):
    """Read a single keypress (blocking)."""
    return sys.stdin.read(1)


def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else None
    if iface:
        ChannelFactoryInitialize(0, iface)
    else:
        ChannelFactoryInitialize(0)

    client = SportClient()
    client.SetTimeout(5.0)
    client.Init()

    vx, vy, vyaw = 0.0, 0.0, 0.0
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        print(BANNER.format(vx=vx, vy=vy, vyaw=vyaw))

        while True:
            key = get_key(fd)
            if key == '\x1b':  # ESC
                break
            elif key == '\x03':  # Ctrl-C
                break
            elif key == 'w':
                vx = min(vx + VX_STEP, VX_MAX)
            elif key == 's':
                vx = max(vx - VX_STEP, -VX_MAX)
            elif key == 'a':
                vy = min(vy + VY_STEP, VY_MAX)
            elif key == 'd':
                vy = max(vy - VY_STEP, -VY_MAX)
            elif key == 'q':
                vyaw = min(vyaw + VYAW_STEP, VYAW_MAX)
            elif key == 'e':
                vyaw = max(vyaw - VYAW_STEP, -VYAW_MAX)
            elif key == ' ':
                vx, vy, vyaw = 0.0, 0.0, 0.0
                client.StopMove()
            elif key == 'u':
                client.StandUp()
                continue
            elif key == 'j':
                client.StandDown()
                continue
            elif key == 'r':
                client.RecoveryStand()
                continue
            else:
                continue

            client.Move(vx, vy, vyaw)
            # Clear screen and reprint banner with current velocities
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.write(BANNER.format(vx=vx, vy=vy, vyaw=vyaw))
            sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        client.StopMove()
        print("\nTeleop stopped.")


if __name__ == "__main__":
    main()
