#!/bin/bash

# Start tmux with claude in the first window
# Use Ctrl-b c to open a new terminal window, Ctrl-b n/p to switch
exec tmux new-session -s claude "claude"
