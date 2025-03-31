# 🎥 FluidVid v1.0.0

FluidVid is a modern, lightweight, and GPU-accelerated video optimisation and thumbnail generation tool written in Python. It uses **FFmpeg** under the hood and features a fully interactive, visually polished terminal interface powered by **Rich** and **Prompt Toolkit**.

---

## 🚀 Features

✅ Auto GPU Detection & NVENC Encoding (NVIDIA)  
✅ Supports MP4 (H.264) and WebM (VP9) outputs  
✅ Generates adaptive thumbnails per resolution  
✅ Smooth, modern terminal UI with rounded panels  
✅ Confirmation pre-start screen  
✅ Progress tracker with current task indicator  
✅ Detailed logging to `fluidvid.log`

---

## 📝 Requirements & Prerequisites

- **Python 3.10+**

  - Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - Ensure Python is added to your `PATH` during installation.

- **FFmpeg** (Required for video processing)

  - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
  - Recommended build: [Gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/)
  - Example path (Windows):  
    `C:\ffmpeg\bin\ffmpeg.exe`

- **Python Dependencies:**
  - `rich`
  - `prompt_toolkit`

Install Python dependencies with:

```bash
pip install rich prompt_toolkit
```

---

## ⚙️ Configuration

Configuration is done via a `config.json` file located in the same folder as `FluidVid.py`.

### Full Example

```json
{
  "ffmpeg_path": "C:\\ffmpeg\\bin\\ffmpeg.exe",
  "output_dir": "./output",
  "sizes": [576, 768, 1200, 1600, 1920],
  "encoders": {
    "default": "libx264",
    "nvenc": "h264_nvenc",
    "qsv": "h264_qsv",
    "amf": "h264_amf",
    "hevc_nvenc": "hevc_nvenc",
    "hevc_qsv": "hevc_qsv",
    "hevc_amf": "hevc_amf",
    "av1_nvenc": "av1_nvenc",
    "av1_qsv": "av1_qsv",
    "av1_amf": "av1_amf"
  },
  "preferred_encoder_priority": ["nvenc", "qsv", "amf"]
}
```

### Configuration Breakdown

| Key                          | Type     | Description                                                                                                 |
| ---------------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `ffmpeg_path`                | `string` | **Required.** Full path to your FFmpeg executable.                                                          |
| `output_dir`                 | `string` | Default output folder for converted videos and thumbnails.                                                  |
| `sizes`                      | `array`  | List of output video widths in pixels. Videos will be resized accordingly.                                  |
| `encoders`                   | `object` | Available encoder mappings for NVIDIA (NVENC), Intel (QSV), AMD (AMF), and default software encoder.        |
| `preferred_encoder_priority` | `array`  | The order in which FluidVid will try to use hardware encoders. Defaults to `nvenc`, then `qsv`, then `amf`. |

**💡 Example:**
If you want to change the output directory and resolutions:

```json
{
  "output_dir": "./myvideos",
  "sizes": [720, 1080, 1440]
}
```

**🔍 How to check available encoders in your FFmpeg build:**
You can list all available encoders by running:

```bash
ffmpeg -encoders
```

You should see output similar to:

```
ffmpeg version 7.1.1-full_build-www.gyan.dev Copyright (c) 2000-2025 the FFmpeg developers
built with gcc 14.2.0 (Rev1, Built by MSYS2 project)
configuration: --enable-gpl --enable-version3 --enable-static ...

Encoders:
 V..... = Video
 A..... = Audio
 S..... = Subtitle
 ...
 V....D libx264              libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (codec h264)
 V....D h264_nvenc           NVIDIA NVENC H.264 encoder (codec h264)
 V..... h264_qsv             H.264 (Intel Quick Sync Video acceleration) (codec h264)
 V....D h264_amf             AMD AMF H.264 encoder (codec h264)
 V....D hevc_nvenc           NVIDIA NVENC HEVC encoder (codec hevc)
 V..... hevc_qsv             HEVC (Intel Quick Sync Video acceleration) (codec hevc)
 V....D hevc_amf             AMD AMF HEVC encoder (codec hevc)
 V....D av1_nvenc            NVIDIA NVENC AV1 encoder (codec av1)
 V..... av1_qsv              AV1 (Intel Quick Sync Video acceleration) (codec av1)
 V....D av1_amf              AMD AMF AV1 encoder (codec av1)
```

This helps you verify if your system supports hardware acceleration.

**💡 Note:**
Ensure your `ffmpeg_path` is correctly set. Example paths:

- Windows: `C:\ffmpeg\bin\ffmpeg.exe`
- Linux: `/usr/bin/ffmpeg`
- macOS (using Homebrew): `/opt/homebrew/bin/ffmpeg`

---

## 💻 Installation & Setup

### 🪟 Windows

1. Download and install **Python 3.10+** from [https://www.python.org/downloads/](https://www.python.org/downloads/).
2. Download **FFmpeg** from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) and extract it to `C:\ffmpeg`.
3. Add Python and FFmpeg to your `PATH` environment variable _(optional but recommended)_.
4. Clone this repo and navigate to the folder.
5. Install dependencies:

```bash
pip install rich prompt_toolkit
```

6. Configure your `config.json` file.

### 🍎 macOS

1. Install **Homebrew** if you haven’t already:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install Python & FFmpeg:

```bash
brew install python ffmpeg
```

3. Clone this repo and install dependencies:

```bash
pip3 install rich prompt_toolkit
```

4. Set `ffmpeg_path` to `/opt/homebrew/bin/ffmpeg` (Apple Silicon) or `/usr/local/bin/ffmpeg` (Intel).

### 🐧 Linux

1. Install Python & FFmpeg:

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

2. Clone this repo and install dependencies:

```bash
pip3 install rich prompt_toolkit
```

3. Set `ffmpeg_path` to `/usr/bin/ffmpeg`.

---

## 💻 Usage

### Command Line

```bash
python FluidVid.py "input_video.mp4"
```

You can also supply an output directory:

```bash
python FluidVid.py "input_video.mp4" "./myoutput"
```

### No Parameters Supplied?

If you run FluidVid without any parameters:

```bash
python FluidVid.py
```

It will prompt you interactively to:

- Enter input file path
- Enter output directory (optional, defaults to `./output`)
- Select GPU if multiple detected

---

## 🔥 Demo Screenshots

**Pre-Start Confirmation Screen**

![Pre-Start Screen](./screenshots/pre-start.png)

**Live Progress Screen**

![Progress Screen](./screenshots/progress.png)

---

## 📄 Log File

A detailed log is saved in your output directory:  
`fluidvid.log`

---

## ❤️ Credits

Built by **Stevie G** 🇦🇺  
Optimised for NVIDIA NVENC GPUs 🎮  
Terminal UI crafted with **Rich** & **Prompt Toolkit** ✨

---

## ☕ Support

If you like this project, give it a ⭐️ on GitHub!

---

## 🔓 License

MIT License. See [LICENSE](./LICENSE) file.
