# FlexRadio Power Control (RPi GPIO Relay via Streamlit)

A modern web interface for controlling relays on a Raspberry Pi 5 to manage FlexRadio power, built with Streamlit. This application is designed for secure remote access over a VPN (like Tailscale) and includes robust logging and exception handling.

## Features

- **Streamlit Web UI**: Simple and intuitive interface to toggle relays.
- **RPi 5 Optimized**: Uses `pinctrl` for low-level GPIO control.
- **Secure**: Password-protected access and optimized for VPN deployment.
- **Logging**: Tracks authentication attempts and relay operations in `app.log`.
- **Systemd Integration**: Includes a service template to run the app on boot.

## Hardware Setup (Waveshare Relay Board)

This project is configured for the **Waveshare RPi Relay Board (3-ch)**.

- **GPIO Mapping**:
  - **CH1**: GPIO 26
  - **CH2**: GPIO 20
  - **CH3**: GPIO 21
- **Logic**: Active Low (Low level trigger). Setting the pin to `0` (Low) turns the relay ON, and `1` (High) turns it OFF.
- **Power**: The board is powered via the Raspberry Pi GPIO header (5V). Ensure your power supply is adequate for both the Pi 5 and the relay coils.
- **Jumpers**: Ensure the control jumpers on the board are set to the default positions (mapping to GPIO 26, 20, 21) as specified in the [Waveshare Wiki](https://www.waveshare.com/wiki/RPi_Relay_Board).

## Waveshare Software Setup

The Waveshare Relay Board documentation mentions several dependencies. For the Raspberry Pi 5, it is important to use updated versions of these libraries due to changes in the GPIO hardware (the new RP1 chip).

### 1. System Dependencies
Install the required system packages and Python development headers:
```bash
sudo apt update
sudo apt install python-dev-is-python3 RPi.GPIO
```

### 2. WiringPi (Version 3.x for RPi 5)
The original WiringPi library is deprecated and does not support the Raspberry Pi 5. You must install the community-maintained version 3.x to enable legacy support and the `gpio` command-line utility.

**Why install WiringPi 3.x?**
The RPi 5 uses a different mechanism for GPIO control. While our `Relay.sh` script uses the modern `pinctrl` tool, many Waveshare examples and legacy scripts rely on the `gpio` command provided by WiringPi. Version 3.x is specifically patched for RPi 5 compatibility.

**Building from source:**
```bash
# Install git if not present
sudo apt install git

# Fetch the source
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi

# Build the package
./build debian
mv debian-template/wiringpi-3.x.deb .

# Install the generated package
sudo dpkg -i wiringpi-3.x.deb
```
Verify the installation by running `gpio -v`.

## Prerequisites

- **Hardware**: Raspberry Pi 5 (or compatible) with a Waveshare relay board connected to GPIO pins 26, 20, and 21 (configurable in `Relay.sh`).
- **Operating System**: Raspberry Pi OS (64-bit recommended).
- **Software**: Python 3.10+, Tailscale (optional but recommended for remote access).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd rpi-gpio-streamlit
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Environment Variables
Create a `.env` file in the root directory to store your authentication password. You can use the provided `.env.example` as a template:

```bash
cp .env.example .env
# Then edit .env and replace 'your_secret_password_here' with your password
```

### 2. Relay Script Permissions
Ensure the `Relay.sh` script is executable:
```bash
chmod +x Relay.sh
```

*Note: The script uses `sudo pinctrl`. You may need to configure `sudoers` if you want the app to run the script without prompting for a password in the background.*

## Running the App

### For Testing
Run the Streamlit server manually:
```bash
streamlit run app.py
```
Access the app at `http://<your-pi-ip>:8501`.

### As a System Service (Production)
To ensure the app starts automatically on boot:

1. **Edit the service file**: Open `relay_app.service` and update the `User` and `WorkingDirectory` paths to match your setup.
2. **Install the service**:
   ```bash
   sudo cp relay_app.service /etc/systemd/system/relay_app.service
   sudo systemctl daemon-reload
   sudo systemctl enable relay_app.service
   sudo systemctl start relay_app.service
   ```

## Security

- **Tailscale**: It is highly recommended to use [Tailscale](https://tailscale.com/) to access your Pi. This avoids opening ports on your router.
- **Password Protection**: Streamlit does not offer in the community addition authentication out of the box. To get around that, we set up authentication using a password (defined in `.env`) before showing the control panel.

## Logging

Operational logs are stored in `app.log`. To monitor logs in real-time:
```bash
tail -f app.log
```

## Troubleshooting

- **Permissions**: If the relays don't trigger, check if the `pi` user (or whichever user runs the app) has permissions to execute `pinctrl` via `sudo`.
- **Type Warnings**: You might see type warnings in your IDE regarding `st.spinner`. These are false positives related to Streamlit's dynamic nature and can be safely ignored.
