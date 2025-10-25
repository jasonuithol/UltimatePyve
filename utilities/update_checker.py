import urllib.request, json, os, sys

# --- CONFIGURATION ---
REPO = "jasonuithol/UltimatePyve"   # e.g. "torvalds/linux"
BRANCH = "master"
STATE_FILE = "log/last_commit.txt"
# ---------------------

url = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"

check_only      = ("--check-only"      in sys.argv)
non_interactive = ("--non-interactive" in sys.argv)
silent          = ("--silent"          in sys.argv)


try:
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
        latest = data["sha"]
except Exception as e:
    print("Error checking updates:", e)
    sys.exit(1)

if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        prev = f.read().strip()

    if (not silent) and (latest != prev):
        print(
            """






            ┌────────────────────────────────────────────────────────────────────────────┐



              UPDATES ARE AVAILABLE ! DOUBLE CLICK update.cmd TO AUTOMATICALLY UPDATE

              

            └────────────────────────────────────────────────────────────────────────────┘

            




            """
        )
        if not non_interactive:
            input("\nPress Enter to close...")
    else:
        if not silent:
            print("No new commits.")
else:
    if not silent:
        print("First run, storing:", latest)

if not check_only:
    with open(STATE_FILE, "w") as f:
        f.write(latest)

