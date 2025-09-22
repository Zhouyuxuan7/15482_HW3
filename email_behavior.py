from behavior import *
from transitions import Machine
from greenhouse_behaviors import Greenhouse_Behavior
import send_email
import os, os.path as op
import glob
import datetime
from email.utils import formatdate
import time

'''
The behavior should send an email that includes the team name and TerraBot
number, the date and time, the current sensor and actuator readings, and
the most recent image taken
'''
class Email(Greenhouse_Behavior):
    def __init__(self, agent):
        super(Email, self).__init__(agent, "EmailBehavior")
        # BEGIN STUDENT CODE
        # Config
        self.TEAM_NAME = "AutonoME3"
        self.FROM_ADDR = "TerraBot.6@outlook.com"
        self.PASSWORD_IGNORED = "ignored"
        self.TOKEN_CACHE = "/home/robotanist/TerraBot/param/token_cache.json"
        self.TEST_MODE = True  # set False for deployment
        self.SHOW_RAW = False

        # Recipients
        self.STUDENTS = ["wenleh@andrew.cmu.edu", "yuxuanz7@andrew.cmu.edu", "msomula@andrew.cmu.edu"]
        self.INSTRUCTORS = ["rsimmons@andrew.cmu.edu", "shashwa3@andrew.cmu.edu", "abhinanv@andrew.cmu.edu"]
        self.IMAGE_DIRS = ["/home/robotanist/TerraBot/images"]

        try:
            send_email.setCacheLocation(self.TOKEN_CACHE)
        except Exception:
            pass

        # FSM
        self.states = ["Halt", "Prepare", "Assemble", "Send", "Done", "Failure"]
        self.fsm = Machine(self, states=self.states, initial="Halt", ignore_invalid_triggers=True)
        self.fsm.add_transition("enable", "Halt", "Prepare")
        self.fsm.add_transition("disable", "*", "Halt")

        self.fsm.add_transition("doStep", "Prepare", "Assemble", conditions="have_recipients", after="gather_latest")
        self.fsm.add_transition("doStep", "Prepare", "Failure", unless="have_recipients", after="note_missing_recipients")
        self.fsm.add_transition("doStep", "Assemble", "Send", after="assemble_email")
        self.fsm.add_transition("doStep", "Send", "Done", conditions="send_ok")
        self.fsm.add_transition("doStep", "Send", "Failure", unless="send_ok")
        self.fsm.add_transition("doStep", "Done", "Halt", after="reset")
        self.fsm.add_transition("doStep", "Failure", "Halt", after="reset")

        self._latest_image_path = None
        self._latest_image_bytes = None
        self._subject = ""
        self._html = ""
        self._send_result = False
        # END STUDENT CODE

    # BEGIN STUDENT CODE
    # Conditions
    def have_recipients(self):
        if self.TEST_MODE:
            return len(self.STUDENTS) > 0
        return (len(self.STUDENTS) + len(self.INSTRUCTORS)) > 0

    def send_ok(self):
        return bool(self._send_result)

    # Actions
    def note_missing_recipients(self):
        print("[EmailBehavior] No recipients configured. Add STUDENTS/INSTRUCTORS and/or disable TEST_MODE.")

    def gather_latest(self):
        # find latest image
        self._latest_image_path = self._find_latest_image()
        self._latest_image_bytes = None
        if self._latest_image_path and op.exists(self._latest_image_path):
            try:
                with open(self._latest_image_path, "rb") as f:
                    self._latest_image_bytes = f.read()
                print(f"[EmailBehavior] Latest image: {self._latest_image_path}")
            except Exception as e:
                print("[EmailBehavior] Could not read image:", e)
                self._latest_image_path = None
                self._latest_image_bytes = None

        # snapshot sensors/actuators
        self._snapshot = self._make_snapshot()

    def assemble_email(self):
        # subject + HTML
        local_str = datetime.datetime.fromtimestamp(self.walltime).strftime("%Y-%m-%d %H:%M:%S")
        utc_str = datetime.datetime.utcfromtimestamp(self.walltime).strftime("%Y-%m-%d %H:%M:%S UTC")

        header = f"{self.TEAM_NAME} — TerraBot 6 — {local_str} ({utc_str})"
        self._subject = f"[TerraBot 6] Daily Status — {local_str}"

        sim_local = datetime.datetime.fromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S")
        sim_utc = datetime.datetime.utcfromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S UTC")
        sim_time_note = f"<p style='color:#777;'>Sim time: {sim_local} ({sim_utc})</p>"

        # tables
        def row(k, v): return f"<tr><td style='padding:4px 8px;'><b>{k}</b></td><td style='padding:4px 8px;'>{v}</td></tr>"
        sensor_rows = "\n".join(row(k, v) for k, v in self._snapshot["sensors"].items())
        actuator_rows = "\n".join(row(k, v) for k, v in self._snapshot["actuators"].items())
        raw_rows = "\n".join(row(k, v) for k, v in self._snapshot.get("sensors_raw", {}).items())

        raw_block = f"""
            <h3 style="margin-top:16px;">Raw Sensor Samples</h3>
            <table border="1" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                {raw_rows}
            </table>
            """ if (self.SHOW_RAW and raw_rows) else ""
        
        img_html = "<p><i>No image attachment available.</i></p>"
        if self._latest_image_bytes:
            img_html = "<p><img src='cid:image1' /></p>"

        self._html = f"""
        <html>
        <body style="font-family:sans-serif;">
            <h2>{header}</h2>
            {sim_time_note}
            <h3>Latest Sensor Readings</h3>
            <table border="1" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            {sensor_rows}
            </table>
            {raw_block}
            <h3 style="margin-top:16px;">Latest Actuators</h3>
            <table border="1" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            {actuator_rows}
            </table>
            {img_html}
            <p style="color:#777;font-size:12px;margin-top:16px;">Sent at {formatdate(localtime=True)}</p>
        </body>
        </html>
        """.strip()

        recipients = list(self.STUDENTS)
        if not self.TEST_MODE:
            recipients += self.INSTRUCTORS
        to_csv = ",".join(recipients)

        images = [self._latest_image_bytes] if self._latest_image_bytes else []
        inline = bool(images)

        try:
            self._send_result = send_email.send(
                self.FROM_ADDR,
                self.PASSWORD_IGNORED,
                to_csv,
                self._subject,
                self._html,
                images=images,
                inline=inline
            )
            print(f"[EmailBehavior] send_email.send returned: {self._send_result}")
        except Exception as e:
            print("[EmailBehavior] Exception in send:", e)
            self._send_result = False

    def reset(self):
        self._latest_image_path = None
        self._latest_image_bytes = None
        self._subject = ""
        self._html = ""
        self._send_result = False

    # Helpers
    def _find_latest_image(self):
        newest = None
        newest_mtime = -1.0
        for d in self.IMAGE_DIRS:
            if not op.isdir(d):
                continue
            for pat in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
                for p in glob.glob(op.join(d, pat)):
                    try:
                        m = os.path.getmtime(p)
                        if m > newest_mtime:
                            newest_mtime = m
                            newest = p
                    except Exception:
                        pass
        return newest

    def _make_snapshot(self):
        s = self.sensordata

        def is_simple(v):
            return isinstance(v, (int, float, str, bool)) or v is None

        sensors_clean = {}
        sensors_raw = {}

        for k, v in s.items():
            if k.endswith("_raw"):
                sensors_raw[k] = v
            else:
                if is_simple(v):
                    sensors_clean[k] = v
                else:
                    # non-primitive -> treat as raw/sample
                    sensors_raw[k] = v

        label_map = {
            "temp": "temperature (°C)",
            "humid": "humidity (%)",
            "light": "light",
            "smoist": "soil_moisture",
            "level": "water_level",
            "weight": "weight",
            "unix_time": "unix_time",
            "midnight_time": "midnight_time",
        }
        pretty_clean = {}
        for k in sorted(sensors_clean.keys()):
            label = label_map.get(k, k)
            pretty_clean[label] = sensors_clean[k]

        def _shorten_seq(val, max_items=6):
            try:
                seq = list(val)
                n = len(seq)
                if n <= max_items:
                    body = ", ".join(str(x) for x in seq)
                else:
                    body = ", ".join(str(x) for x in seq[:max_items]) + ", …"
                return f"[{body}] (len {n})"
            except Exception:
                return str(val)

        pretty_raw = {}
        for k in sorted(sensors_raw.keys()):
            v = sensors_raw[k]
            if isinstance(v, (list, tuple)) or getattr(v, "__iter__", None):
                pretty_raw[k] = _shorten_seq(v)
            else:
                pretty_raw[k] = str(v)

        # Actuators
        actuators = {}
        try:
            if hasattr(self.actuators, "current"):
                actuators.update(self.actuators.current)
        except Exception:
            pass

        return {"sensors": pretty_clean, "sensors_raw": pretty_raw, "actuators": actuators}
    # END STUDENT CODE

    def perceive(self):
        self.time = self.sensordata['unix_time']
        self.walltime = time.time() 

    def act(self):
        self.trigger("doStep")
