#!/bin/bash

# Start tmux with hermes in the first window.
# Use Ctrl-b c to open a new terminal window, Ctrl-b n/p to switch.
exec tmux new-session -s hermes "hermes"
