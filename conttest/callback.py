import subprocess
from conttest import watch_dir, TIMES


callbacks = {
    "black": "python3 -m black {changed_files}",
    "flake8": "python3 -m flake8 {changed_files}",
    "pytest": "python3 -m pytest tests/",
}


def run_tasks(changed_files):
    for name, cmd in callbacks.items():
        if "{changed_files}" in cmd:
            cmd = cmd.format(changed_files=" ".join(changed_files))

        print(f"Running command `{cmd}`")
        subprocess.call(cmd, shell=True)


def run_callback_on_update(callback):
    try:
        watch_dir(".", callback, method=TIMES)
    except KeyboardInterrupt:
        print


if __name__ == "__main__":
    run_callback_on_update(run_tasks)
