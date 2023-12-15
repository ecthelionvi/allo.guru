import subprocess
import signal
import sys

def run_command(command, cwd=None, background=False):
    if background:
        return subprocess.Popen(command, cwd=cwd, shell=True)
    else:
        return subprocess.run(command, cwd=cwd, shell=True)

def start_flask_app():
    return run_command("gunicorn -w 4 -b 0.0.0.0:8000 app:app --log-level info", cwd="/usr/src/app/backend", background=True)

def start_next_js_app():
    return run_command("npm start", cwd="/usr/src/app/frontend", background=True)

def start_asynchronous_tasks():
    return run_command("python3 asyncio_script.py", cwd="/usr/src/app/backend", background=True)

def start_nginx():
    # Run Nginx in the foreground
    run_command("nginx -g 'daemon off;'", background=False)

def signal_handler(sig, frame):
    print("Stopping servers...")
    for process in background_processes:
        process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    background_processes = [
        start_flask_app(),
        start_next_js_app(),
        start_asynchronous_tasks()
    ]

    # Nginx is run last and in the foreground to keep the script alive.
    start_nginx()
