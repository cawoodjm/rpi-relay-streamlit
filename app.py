"""RelayApp Module.

This module provides a Streamlit web-based interface for remotely controlling
power relays. It includes simple user authentication through a password and manages
relay toggling by invoking a shell script. The example used is for FlexRadio power
control, but the logic can be adapted to other devices with similar relay control capabilities.

Logging is configured to capture application events to both a file and the
console to assist in troubleshooting and operational monitoring.

Classes:
    None

Functions:
    check_password: Validates user-entered password against the stored environment variable.
    toggle_relay: Executes a shell script to toggle a specified relay channel on or off.
    main: Implements the main logic of the Streamlit application.

Author: Joseph Cawood
License: GPL-3.0
"""

import subprocess
import os
import dotenv  # pylint: disable=import-error
import logging
import time

"Third-party imports"
import streamlit as st  # pylint: disable=import-error

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RelayApp")
dotenv.load_dotenv()


# --- AUTHENTICATION ---
def check_password():
    """
    Checks if the user-provided password matches the correct password required for
    authentication and handles the password validation process.

    Functions:
        password_entered: Validates the entered password against the system's
        correct password and updates the session state accordingly.

    Raises:
        None
    """

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        input_password = st.session_state["password"]
        correct_password = os.getenv("AUTH_PASSWORD")

        if not correct_password:
            st.error("Authentication Error: AUTH_PASSWORD is not set in the environment.")
            logger.error("AUTH_PASSWORD environment variable is missing or empty.")
            return

        if input_password == correct_password:
            st.session_state["password_correct"] = True
            logger.info("User authenticated successfully.")
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False
            logger.warning("Failed login attempt.")
            time.sleep(1)  # Basic rate limiting to slow down brute-force attempts

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    if not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False

    # Password correct.
    return True


# --- RELAY CONTROL LOGIC ---
def toggle_relay(channel, action):
    """
    Toggles the state of a relay by invoking an external shell script.

    This function attempts to execute a shell script to toggle the state of a
    relay channel to a specified action. It ensures that the script exists and
    is executable before running it. If the script encounters an error or if
    there are issues executing the script, appropriate error messages are
    logged and returned.

    Parameters:
        channel (str): The relay channel to toggle.
        action (str): The action to perform on the relay (e.g., "on", "off").

    Returns:
        str: The output from the shell script if successful, or an error
        message if there was a failure.
    """
    # Use absolute path for the script to ensure it's found
    # and to prevent execution of shadowed files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "Relay.sh")
    logger.info("Attempting to toggle %s to %s", channel, action)

    # Ensure script exists
    if not os.path.exists(script_path):
        err_msg = f"Script not found at {script_path}"
        logger.error(err_msg)
        return err_msg

    # Ensure script is executable
    if not os.access(script_path, os.X_OK):
        try:
            logger.info("Setting executable permissions on %s", script_path)
            os.chmod(script_path, 0o755)
        except OSError as e:
            err_msg = f"Error setting permissions: {e}"
            logger.exception(err_msg)
            return err_msg

    try:
        # Run the shell script
        result = subprocess.run(
            [script_path, channel, action],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        logger.info("Command successful. Output: %s", output)
        return output
    except subprocess.CalledProcessError as e:
        err_msg = f"Script error: {e.stderr.strip() if e.stderr else e.stdout.strip()}"
        logger.error("CalledProcessError: %s", err_msg)
        return err_msg
    except OSError as e:
        logger.exception("Subprocess execution failed: %s", e)
        return "An error occurred during relay control execution. Check app.log for details."
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error during script execution")
        return "An unexpected error occurred during relay control. Check app.log for details."


# --- MAIN APP ---
def main():
    """
    Main function for the FlexRadio Remote Power Control web application.

    This function initializes the web application interface, performs authentication,
    and provides the control logic for managing relay channels. It manages the layout
    and interaction flow using Streamlit components and methods. The function also
    handles all user interaction such as turning relays on/off and logging out.

    Raises:
        Exception: Captures and logs any unexpected critical errors that occur during
        execution and displays an error message to the user.
    """
    try:
        st.set_page_config(page_title="FlexRadio Remote Power Control", layout="centered")
        if not check_password():
            st.warning("Please enter the correct password to access this page.")
            st.stop()
        st.success("Login successful.")

        st.title("FlexRadio Remote Power Control")
        channels = ["CH1", "CH2", "CH3"]

        # Use columns for a nice layout
        cols = st.columns(len(channels))

        for i, ch in enumerate(channels):
            with cols[i]:
                st.markdown(f"### {ch}")

                if st.button("ON", key=f"on_{ch}", use_container_width=True):
                    with st.spinner(f"Turning ON {ch}..."):
                        res = toggle_relay(ch, "ON")
                        if "Error" in res or "error" in res:
                            st.error(res)
                        else:
                            st.success(res)

                if st.button("OFF", key=f"off_{ch}", type="primary", use_container_width=True):
                    with st.spinner(f"Turning OFF {ch}..."):
                        res = toggle_relay(ch, "OFF")
                        if "Error" in res or "error" in res:
                            st.error(res)
                        else:
                            st.info(res)

        st.divider()
        if st.button("Logout"):
            logger.info("User logged out.")
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Global application error")
        st.error("A critical error occurred. Please check the logs (app.log) for more details.")


if __name__ == "__main__":
    logger.info("Application started.")
    main()
