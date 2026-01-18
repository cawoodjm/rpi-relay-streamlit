#!/bin/bash

# Configuration for Waveshare RPi Relay Board (3-ch)
# Wiki: https://www.waveshare.com/wiki/RPi_Relay_Board

# Channel to GPIO mapping
if [ "$1" == 'CH1' ]; then
    ch=26
elif [ "$1" == 'CH2' ]; then
    ch=20
elif [ "$1" == 'CH3' ]; then
    ch=21
else
    echo "Parameter error: Use CH1, CH2, or CH3"
    exit 1
fi

# ON/OFF to logic state mapping
# Note: Waveshare Relay Board uses 'Active Low' (0 = ON, 1 = OFF)
if [ "$2" == 'ON' ]; then
    state="dl" # Driven Low
elif [ "$2" == 'OFF' ]; then
    state="dh" # Driven High
else
    echo "Parameter error: Use ON or OFF"
    exit 1
fi

# Modern command to set GPIO state
# 'op' sets the pin to output mode
sudo pinctrl set $ch op $state

echo "Relay $1 $2 (GPIO $ch set to $state)"
