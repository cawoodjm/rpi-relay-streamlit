import streamlit as st
import subprocess
import os
import dotenv
import logging

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
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        input_password = st.session_state["password"]
        correct_password = os.getenv("AUTH_PASSWORD")
        
        if input_password == correct_password:
            st.session_state["password_correct"] = True
            logger.info("User authenticated successfully.")
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False
            logger.warning("Failed login attempt with incorrect password.")

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password doesn't correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# --- RELAY CONTROL LOGIC ---
def toggle_relay(channel, action):
    script_path = "./Relay.sh"
    logger.info(f"Attempting to toggle {channel} to {action}")
    
    # Ensure script exists
    if not os.path.exists(script_path):
        err_msg = f"Script not found at {script_path}"
        logger.error(err_msg)
        return err_msg

    # Ensure script is executable
    if not os.access(script_path, os.X_OK):
        try:
            logger.info(f"Setting executable permissions on {script_path}")
            os.chmod(script_path, 0o755)
        except Exception as e:
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
        logger.info(f"Command successful. Output: {output}")
        return output
    except subprocess.CalledProcessError as e:
        err_msg = f"Script error: {e.stderr.strip() if e.stderr else e.stdout.strip()}"
        logger.error(f"CalledProcessError: {err_msg}")
        return err_msg
    except Exception as e:
        err_msg = f"Unexpected error during script execution: {str(e)}"
        logger.exception(err_msg)
        return err_msg

# --- MAIN APP ---
def main():
    try:
        st.set_page_config(page_title="FlexRadio Power Control", page_icon="🔌", layout="centered")

        if not check_password():
            st.stop()

        st.title("🔌 FlexRadio Power Control")
        st.info("Connected via Tailscale Secure Network")

        channels = ["CH1", "CH2", "CH3"]

        # Use columns for a nice layout
        cols = st.columns(len(channels))

        for i, ch in enumerate(channels):
            with cols[i]:
                st.markdown(f"### {ch}")
                
                if st.button(f"ON", key=f"on_{ch}", use_container_width=True):
                    with st.spinner(f"Turning ON {ch}..."):
                        res = toggle_relay(ch, "ON")
                        if "Error" in res or "error" in res:
                            st.error(res)
                        else:
                            st.success(res)

                if st.button(f"OFF", key=f"off_{ch}", type="primary", use_container_width=True):
                    with st.spinner(f"Turning OFF {ch}..."):
                        res = toggle_relay(ch, "OFF")
                        if "Error" in res or "error" in res:
                            st.error(res)
                        else:
                            st.info(res)

        st.divider()
        if st.button("Logout"):
            logger.info("User logged out.")
            st.session_state["password_correct"] = False
            st.rerun()

    except Exception as e:
        logger.exception("Global application error")
        st.error(f"A critical error occurred: {e}")

if __name__ == "__main__":
    logger.info("Application started.")
    main()
