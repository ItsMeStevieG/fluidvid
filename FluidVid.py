gpu_info_printed = False

import os
import subprocess
import sys
import json
import platform
import time
import logging
import ctypes
from threading import Thread, Event
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box  # For rounded borders

# Initialize Rich console for styled output
console = Console()

# Prompt Toolkit style for the confirmation prompt
prompt_style = Style.from_dict({
    'prompt': 'cyan bold',
})

# Global variables
stop_event = Event()
current_task = ""
total_tasks = 0
completed_tasks = 0
input_filename = ""
output_dir = ""
console_width = 80
console_height = 25
config = {}
selected_gpu_info = ""  # To store GPU info for the header
log_messages = []       # To store log messages for live display

def get_console_size():
    try:
        if platform.system() == "Windows":
            from ctypes import windll, create_string_buffer
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                import struct
                (_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                return right - left + 1, bottom - top + 1
        else:
            import fcntl, termios, struct
            h = fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
            rows, cols = struct.unpack('HHHH', h)[:2]
            return cols, rows
    except:
        return 80, 25  # Default fallback size

def set_console_title(title):
    if platform.system() == "Windows":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleTitleW(title)
    else:
        print(f"\33]0;{title}\a", end='', flush=True)

def load_config():
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        console.print(f"[red]Error loading config.json: {e}[/red]")
        sys.exit(1)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # File handler
    file_handler = logging.FileHandler(os.path.join(output_dir, "fluidvid.log"))
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
    logger.addHandler(file_handler)
    return logger

def detect_gpus():
    gpus = []
    try:
        if platform.system() == "Windows":
            # Try nvidia-smi first
            try:
                nvidia_info = subprocess.check_output(
                    "nvidia-smi --query-gpu=name --format=csv,noheader",
                    shell=True
                ).decode().strip().split("\n")
                for i, gpu_name in enumerate(nvidia_info):
                    if gpu_name.strip():
                        gpus.append({
                            "number": i,
                            "name": gpu_name.strip(),
                            "vendor": "nvidia"
                        })
            except:
                pass

            # Fallback to wmic if no NVIDIA GPUs found
            if not gpus:
                gpu_info = subprocess.check_output(
                    "wmic path win32_VideoController get name,AdapterCompatibility",
                    shell=True
                ).decode().split("\n")[1:-1]
                for i, adapter in enumerate(gpu_info):
                    if not adapter.strip():
                        continue
                    parts = [p.strip() for p in adapter.split(",") if p.strip()]
                    gpu_name = parts[0]
                    vendor = "unknown"
                    if "nvidia" in gpu_name.lower():
                        vendor = "nvidia"
                    elif "amd" in gpu_name.lower():
                        vendor = "amd"
                    elif "intel" in gpu_name.lower():
                        vendor = "intel"
                    gpus.append({
                        "number": i,
                        "name": gpu_name,
                        "vendor": vendor
                    })
    except Exception as e:
        logging.error(f"Could not detect GPUs: {str(e)}")
    return gpus

def select_gpu(gpus):
    global selected_gpu_info
    if not gpus:
        selected_gpu_info = "No GPU detected"
        return None

    # If multiple GPUs detected, prompt the user for a selection
    if len(gpus) > 1:
        console.print("[bold blue]Multiple GPUs detected:[/bold blue]")
        for gpu in gpus:
            console.print(f"  [{gpu['number']}] {gpu['name']} ({gpu['vendor'].upper()})")
        console.print("Enter the number of the GPU to use (default: first): ", end="")
        choice = input().strip()
        if choice.isdigit():
            choice = int(choice)
            for gpu in gpus:
                if gpu["number"] == choice:
                    selected_gpu_info = f"GPU {gpu['number']}: {gpu['name']} ({gpu['vendor'].upper()})"
                    return gpu
    # Fallback to auto-select first GPU if no valid choice was made
    selected_gpu_info = f"GPU {gpus[0]['number']}: {gpus[0]['name']} ({gpus[0]['vendor'].upper()})"
    return gpus[0]

def get_encoder_settings(gpu):
    if gpu and gpu["vendor"] == "nvidia":
        return {
            "mp4": {
                "encoder": "h264_nvenc",
                "params": ["-preset", "p6", "-cq", "23"],
                "description": f"GPU {gpu['number']} (NVENC)"
            },
            "webm": {
                "encoder": "libvpx-vp9",
                "params": ["-speed", "4", "-crf", "32"],
                "description": "VP9 (CPU)"
            }
        }
    else:
        return {
            "mp4": {
                "encoder": "libx264",
                "params": ["-preset", "fast", "-crf", "23"],
                "description": "x264 (CPU)"
            },
            "webm": {
                "encoder": "libvpx-vp9",
                "params": ["-speed", "4", "-crf", "32"],
                "description": "VP9 (CPU)"
            }
        }

def run_ffmpeg(command, task_name):
    global current_task, completed_tasks
    current_task = task_name
    try:
        subprocess.run(
            command,
            check=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        logging.info(f"Completed: {task_name}")
        completed_tasks += 1
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed: {task_name} - {e.stderr}")
        completed_tasks += 1
        return False

def convert_video(input_file, size, encoder_settings, output_file):
    scale = f"scale={size}:-1"
    command = [
        config["ffmpeg_path"], "-y", "-i", input_file,
        "-vf", scale,
        "-c:v", encoder_settings["encoder"],
        *encoder_settings["params"],
        "-an",
        output_file
    ]
    task_name = f"{size}p ({encoder_settings['description']})"
    return run_ffmpeg(command, task_name)

def generate_thumbnail(input_file, output_file):
    command = [
        config["ffmpeg_path"], "-y",
        "-i", input_file,
        "-ss", "00:00:01",
        "-frames:v", "1",
        output_file
    ]
    return run_ffmpeg(command, f"Thumbnail {os.path.basename(output_file)}")

def confirm_conversion():
    # Create a layout for the pre-start screen
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),  # Header takes 3 lines
        Layout(name="prompt", size=3)   # Prompt takes 3 lines
    )
    def update_layout():
        console_width, console_height = get_console_size()
        header_text = Text(f"FluidVid v1.0.0 - Optimising {input_filename} to {output_dir}", style="bold blue")
        gpu_text = Text(selected_gpu_info if selected_gpu_info else "No GPU detected", style="cyan")
        separator = Text("=" * console_width, style="dim")
        layout["header"].update(
            Panel(
                f"{header_text}\n{gpu_text}\n{separator}",
                border_style="bright_blue",
                box=box.ROUNDED,
                padding=0
            )
        )
        prompt_text = f"Proceed with optimising {input_filename} to {output_dir}? (y/n, default: y)"
        layout["prompt"].update(
            Panel(
                prompt_text,
                style="cyan bold",
                border_style="bright_blue",
                box=box.ROUNDED
            )
        )
    with Live(layout, console=console, screen=True, auto_refresh=False) as live:
        update_layout()
        live.refresh()
        session = PromptSession("> ", style=prompt_style)
        response = session.prompt().strip().lower()
    return response in ('', 'y', 'yes')

def display_updater():
    """
    Uses a Rich Layout to show a modern, rounded style interface
    while tasks are being processed, all with bright_blue borders.
    """
    global console_width, console_height, completed_tasks
    last_log_size = 0
    displayed_messages = set()
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="content", ratio=1),
        Layout(name="footer", size=3)
    )
    log_file = os.path.join(output_dir, "fluidvid.log")
    with Live(layout, console=console, screen=True, refresh_per_second=5) as live:
        while not stop_event.is_set():
            try:
                console_width, console_height = get_console_size()
                header_text = Text(f"FluidVid v1.0.0 - Optimising {input_filename} to {output_dir}", style="bold blue")
                gpu_text = Text(selected_gpu_info if selected_gpu_info else "No GPU detected", style="cyan")
                header_panel = Panel(
                    f"{header_text}\n{gpu_text}",
                    border_style="bright_blue",
                    box=box.ROUNDED
                )
                layout["header"].update(header_panel)
                if os.path.exists(log_file):
                    current_log_size = os.path.getsize(log_file)
                    if current_log_size != last_log_size:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                        last_log_size = current_log_size
                        for line in lines:
                            msg = line.split("]: ")[-1] if "]: " in line else line
                            msg = msg.strip()
                            if msg not in displayed_messages:
                                displayed_messages.add(msg)
                sorted_logs = list(displayed_messages)
                content_height = console_height - 6
                if content_height < 1:
                    content_height = 1
                display_lines = sorted_logs[-content_height:]
                log_content = []
                for line in display_lines:
                    if len(line) > console_width - 2:
                        line = line[:console_width - 5] + "..."
                    if "Completed:" in line:
                        log_content.append(f"[green]✔ {line}[/green]")
                    elif "Failed:" in line:
                        log_content.append(f"[red]✘ {line}[/red]")
                    else:
                        log_content.append(line)
                content_panel = Panel(
                    "\n".join(log_content),
                    border_style="bright_blue",
                    box=box.ROUNDED
                )
                layout["content"].update(content_panel)
                progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                bar_length = 50
                filled = int(bar_length * progress_percentage / 100)
                progress_bar = "█" * filled + "░" * (bar_length - filled)
                task_info = f"Tasks: {completed_tasks}/{total_tasks} ({progress_percentage:.1f}%)"
                current_task_text = f"Current: {current_task}" if current_task else ""
                footer_text = f"[bold green]{task_info} [{progress_bar}] {current_task_text}[/bold green]"
                footer_panel = Panel(
                    footer_text,
                    border_style="bright_blue",
                    box=box.ROUNDED
                )
                layout["footer"].update(footer_panel)
                live.update(layout)
                time.sleep(0.2)
            except Exception as e:
                time.sleep(0.5)

def main(input_file):
    global config, input_filename, output_dir, total_tasks, completed_tasks
    print("\033[?1049h")  # Enable alternate buffer
    print("\033[?25l")    # Hide cursor
    config = load_config()
    # Override config output directory if provided as second parameter
    if len(sys.argv) > 2:
        config["output_dir"] = sys.argv[2]
    input_filename = os.path.basename(input_file.strip('"'))
    output_dir = os.path.abspath(config["output_dir"])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    set_console_title(f"FluidVid v1.0.0 - {input_filename}")
    setup_logging()
    if not os.path.exists(input_file):
        logging.error("Input file not found")
        stop_event.set()
        sys.exit(1)
    gpus = detect_gpus()
    selected_gpu = select_gpu(gpus)
    encoder_settings = get_encoder_settings(selected_gpu)
    total_tasks = len(config["sizes"]) * 3  # Thumbnail + MP4 + WebM for each size
    if not confirm_conversion():
        console.print("\n[red]Conversion aborted by user.[/red]")
        print("\033[?1049l")  # Disable alternate buffer
        print("\033[?25h")    # Show cursor
        sys.exit(0)
    display_thread = Thread(target=display_updater)
    display_thread.daemon = True
    display_thread.start()
    for size in config["sizes"]:
        mp4_output = os.path.join(output_dir, f"video-{size}p.mp4")
        webm_output = os.path.join(output_dir, f"video-{size}p.webm")
        poster_file = os.path.join(output_dir, f"video-{size}p-poster.jpg")
        generate_thumbnail(input_file, poster_file)
        convert_video(input_file, size, encoder_settings["mp4"], mp4_output)
        convert_video(input_file, size, encoder_settings["webm"], webm_output)
    stop_event.set()
    display_thread.join()
    print("\033[?1049l")  # Disable alternate buffer
    print("\033[?25h")    # Show cursor
    console_width, _ = get_console_size()
    console.print("\n" + "-" * console_width)
    console.print("[bold green]✔ All conversions completed successfully![/bold green]")
    console.print(f"[bold cyan]📁 Output directory: {output_dir}[/bold cyan]")
    console.print("-" * console_width + "\n")

if __name__ == "__main__":
    # If no parameters are supplied, prompt the user for the input file and output directory.
    if len(sys.argv) < 2:
        console.print("[bold blue]No parameters supplied. Please provide the input file and output directory.[/bold blue]")
        inp = input("Enter input file path: ").strip()
        outp = input("Enter output directory (press Enter to use default './output'): ").strip()
        if not outp:
            outp = "./output"
        sys.argv.extend([inp, outp])
    import logging
    main(sys.argv[1])
