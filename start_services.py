import subprocess

def run_command(command, cwd=None, background=False):
    """
    Execute a command as a subprocess.
    Args:
    - command: Command to execute.
    - cwd: Directory to execute the command in.
    - background: Run in background if True.
    Uses subprocess.Popen for background tasks, subprocess.run otherwise.
    """
    if background:
        subprocess.Popen(command, cwd=cwd, shell=True)
    else:
        subprocess.run(command, cwd=cwd, shell=True)

def start_flask_app():
    run_command("gunicorn -w 4 -b 0.0.0.0:8000 app:app --log-level info", cwd="/usr/src/app/backend", background=True)

def start_next_js_app():
    run_command("npm start", cwd="/usr/src/app/frontend", background=True)

def start_nginx():
    run_command("nginx -g 'daemon off;'")

def start_asynchronous_tasks():
    run_command("python3 asyncio_script.py", cwd="/usr/src/app/backend", background=False)

if __name__ == "__main__":
    start_flask_app()
    start_next_js_app()
    start_nginx()
    input("Press Enter to exit and stop all servers\n")
