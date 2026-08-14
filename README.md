# Dark Between Audio

Dark Between Audio is a Windows desktop audio bridge for Discord.

It allows soundboards, local audio files, and supported online audio sources to play through a dedicated Discord bot instead of being mixed into your microphone.

The primary use case is tabletop RPGs, soundboards, ambience, music, sound effects, and similar shared audio.

## What It Does

Dark Between Audio can:

- Connect a bot to a Discord voice channel
- Capture audio from a Windows audio input
- Send soundboard audio through the bot
- Play local audio files
- Play YouTube audio
- Mix multiple sources together
- Control individual source volumes
- Apply a master output volume
- Start and stop sources independently
- Remember commonly used settings
- Run from a dark-mode desktop control panel

Example audio path:

```text
RPG Soundboard
      |
      v
VB-Audio Virtual Cable
      |
      v
Dark Between Audio
      |
      +------ Local Files
      |
      +------ YouTube
      |
      v
Audio Mixer
      |
      v
Discord Bot
      |
      v
Discord Voice Channel
```

---

# Requirements

Dark Between Audio currently targets Windows.

## Recommended Python Version

Use:

```text
Python 3.11 or Python 3.12
```

Python 3.10 currently works, but some dependencies have begun deprecating it.

Python 3.13+ is not currently recommended because the audio mixer still uses Python's `audioop` module, which was removed from newer Python versions.

## Required Software

You will need:

- Python 3.11 or 3.12
- FFmpeg
- VB-Audio Virtual Cable
- A Discord bot/application
- Dark Between Audio's Python dependencies

---

# 1. Install Python

Install Python 3.11 or 3.12.

During installation, enable:

```text
Add python.exe to PATH
```

Verify installation in PowerShell:

```powershell
python --version
```

You should see something similar to:

```text
Python 3.12.x
```

---

# 2. Install FFmpeg

Dark Between Audio uses FFmpeg to decode and process audio.

After installing FFmpeg, verify that it is available from PowerShell:

```powershell
ffmpeg -version
```

If FFmpeg displays version information, it is configured correctly.

If Windows reports that `ffmpeg` is not recognized, FFmpeg is not installed or its executable directory is not in your PATH.

---

# 3. Install VB-Audio Virtual Cable

Dark Between Audio can capture normal Windows audio devices, but VB-Audio Virtual Cable provides the simplest way to route a soundboard into the bot without mixing it with your microphone.

Install VB-CABLE and reboot Windows if requested.

After installation, Windows should expose two devices:

```text
CABLE Input
CABLE Output
```

The naming can be confusing:

```text
Application
    |
    v
CABLE Input
    |
    v
VB-CABLE
    |
    v
CABLE Output
    |
    v
Dark Between Audio
```

Your soundboard sends audio TO:

```text
CABLE Input
```

Dark Between Audio listens FROM:

```text
CABLE Output
```

## Example

Configure RPG Soundboard's output device as:

```text
CABLE Input (VB-Audio Virtual Cable)
```

Then select this inside Dark Between Audio:

```text
CABLE Output (VB-Audio Virtual Cable)
```

Press:

```text
Start Input
```

Audio played by the soundboard should now be transmitted by the Discord bot.

---

# 4. Create the Discord Bot

Dark Between Audio requires your own Discord bot token.

Never share your bot token.

Never commit your bot token to GitHub.

## Create the Application

Open the Discord Developer Portal and create a new application.

Give it whatever name you want.

Example:

```text
Dark Between Audio
```

Open the application's:

```text
Bot
```

section and create/configure the bot.

## Bot Permissions

The bot needs only the permissions required to see and speak in voice channels.

Recommended permissions:

```text
View Channels
Connect
Speak
```

Administrator permission is NOT required.

Dark Between Audio does not currently require Message Content Intent because normal operation is controlled through the desktop GUI rather than Discord text commands.

## Install the Bot Into Your Server

In the Discord Developer Portal, configure a Guild Install for the application.

The bot scope should be enabled.

Install the bot into the Discord server where it will be used.

The bot may appear offline until Dark Between Audio is running.

That is normal.

---

# 5. Get Your Discord Bot Token

Open your application in the Discord Developer Portal.

Go to:

```text
Bot
```

Generate or copy the bot token.

IMPORTANT:

```text
DO NOT paste your token into Discord.
DO NOT post it in screenshots.
DO NOT commit it to GitHub.
DO NOT put it directly inside the Python source code.
```

If your token is ever exposed, immediately reset it in the Discord Developer Portal.

---

# 6. Configure the `.env` File

Dark Between Audio reads the Discord token from a local `.env` file.

Create:

```text
.env
```

in the project directory.

Add:

```text
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
```

Example:

```text
DISCORD_TOKEN=abc123exampletoken
```

Do not add quotes unless they are actually part of the token.

The repository's `.gitignore` should include:

```text
.env
.venv/
__pycache__/
*.pyc
```

This prevents your Discord credentials and Python environment from accidentally being committed.

An `.env.example` file may safely contain:

```text
DISCORD_TOKEN=put_your_discord_bot_token_here
```

but must never contain a real token.

---

# 7. Create the Python Virtual Environment

Open PowerShell in the Dark Between Audio directory.

Example:

```powershell
cd C:\Projects\dark-between-audio
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

The PowerShell prompt should change to something similar to:

```text
(.venv) PS C:\Projects\dark-between-audio>
```

You must activate the virtual environment again whenever you open a new PowerShell window.

---

# 8. Install Python Dependencies

Install the required packages:

```powershell
pip install discord.py python-dotenv pynacl davey PySide6 sounddevice yt-dlp
```

A future release will provide these through:

```powershell
pip install -r requirements.txt
```

The important packages currently include:

```text
discord.py
python-dotenv
PyNaCl
davey
PySide6
sounddevice
yt-dlp
```

---

# 9. Run Dark Between Audio

With the virtual environment active:

```powershell
python main.py
```

The Dark Between Audio control panel should open.

The Discord bot should also appear online in your server.

---

# Using Dark Between Audio

## Discord Connection

At the top of the program:

1. Select your Discord server.
2. Select your voice channel.
3. Press:

```text
Join Channel
```

The bot should enter the selected Discord voice channel.

Press:

```text
Leave Channel
```

to disconnect it.

The program remembers your previously selected Discord server and voice channel.

---

# External Audio Input

The External Audio Input section is intended primarily for soundboards and other applications.

Select:

```text
CABLE Output (VB-Audio Virtual Cable)
```

or another audio capture device.

Then press:

```text
Start Input
```

Play audio through the application routed into VB-CABLE.

The audio should appear in Discord as coming from the Dark Between Audio bot.

Use the Input Volume slider to adjust its level.

Press:

```text
Stop Input
```

to stop only the external audio source.

This will not stop YouTube or local files.

The selected input device is remembered between sessions.

---

# Local File Playback

Dark Between Audio can play local audio files directly.

Supported formats depend on FFmpeg but commonly include:

```text
MP3
WAV
OGG
FLAC
```

Press:

```text
Select Sound
```

Choose the audio file.

Then press:

```text
Play Sound
```

Multiple local sounds can play simultaneously.

Use:

```text
Stop Local Audio
```

to stop local file playback without affecting external input or YouTube.

The Local Volume slider adjusts local-file playback level.

---

# YouTube Playback

Dark Between Audio includes experimental YouTube playback support.

Paste a YouTube URL into the YouTube section and press:

```text
Play YouTube
```

## Start Timestamp

You can optionally specify where playback should begin.

Examples:

```text
10
```

means:

```text
10 seconds
```

```text
01:30
```

means:

```text
1 minute 30 seconds
```

```text
1:02:30
```

means:

```text
1 hour 2 minutes 30 seconds
```

## Stop Timestamp

The Stop field allows playback to automatically stop at a specific point.

Example:

```text
Start: 18:35
Stop:  26:10
```

Only that portion of the source will play.

## Loop

Enable:

```text
Loop
```

to repeat the configured section.

If Start and Stop timestamps are configured, the selected segment is repeated rather than restarting from the beginning.

## YouTube Volume

YouTube sources can vary considerably in loudness.

The YouTube volume control currently allows:

```text
0% - 200%
```

100% represents the source's normal level.

Values above 100% amplify the source and may cause clipping on very loud material.

## Important

You are responsible for ensuring that you have the necessary rights or permissions to play or transmit content.

Dark Between Audio is intended as an audio-routing and playback tool, not as a method for bypassing content protections or distributing copyrighted material.

---

# Master Volume

The Master Output control changes the level of the final mixed Discord stream.

It affects:

```text
External Input
YouTube
Local Files
```

simultaneously.

Individual source volume controls are applied before the Master Volume.

---

# STOP ALL AUDIO

The:

```text
STOP ALL AUDIO
```

button immediately stops all active audio sources.

This includes:

```text
External Input
YouTube
Local Files
```

The Discord bot remains connected to the voice channel.

---

# Exit

Use the:

```text
Exit
```

button or close the window normally.

Dark Between Audio will attempt to:

```text
Stop active audio
Terminate FFmpeg processes
Disconnect from Discord voice
Close the Discord connection
Exit cleanly
```

Using the Exit button is preferable to terminating the application from PowerShell.

---

# Audio Mixing

Dark Between Audio contains a multi-source PCM mixer.

This allows combinations such as:

```text
RPG Soundboard ambience
        +
YouTube music
        +
Local sound effect
        ↓
One Discord bot stream
```

Sources run independently rather than stopping one another.

---

# Settings

Dark Between Audio currently remembers several settings between runs, including:

```text
Input device
Discord server
Discord voice channel
Input volume
YouTube volume
Local-file volume
Master volume
YouTube loop setting
```

Discord bot credentials are NOT stored through the application's normal settings system.

The bot token remains in `.env`.

---

# Project Structure

```text
dark-between-audio/
│
├── main.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
│
├── audio/
│   ├── __init__.py
│   ├── mixer.py
│   ├── source.py
│   ├── input_source.py
│   └── youtube_source.py
│
├── bot/
│   ├── __init__.py
│   └── discord_client.py
│
└── gui/
    ├── __init__.py
    └── main_window.py
```

---

# Troubleshooting

## `ModuleNotFoundError`

Example:

```text
ModuleNotFoundError: No module named 'PySide6'
```

The most common cause is that the virtual environment is not active.

Run:

```powershell
cd C:\Projects\dark-between-audio
.\.venv\Scripts\Activate.ps1
python main.py
```

---

## Bot Is Offline

Make sure Dark Between Audio is running.

The bot is expected to be offline whenever the Python application is not running.

Also verify:

```text
DISCORD_TOKEN
```

is correctly configured in `.env`.

---

## Bot Cannot Join Voice

Verify the bot has:

```text
View Channels
Connect
Speak
```

permissions for the target Discord voice channel.

---

## `davey library needed in order to use voice`

Install:

```powershell
pip install davey
```

Then restart Dark Between Audio.

---

## No Sound From RPG Soundboard

Check the entire route:

```text
RPG Soundboard
    |
    v
CABLE Input
    |
    v
VB-CABLE
    |
    v
CABLE Output
    |
    v
Dark Between Audio
    |
    v
Discord
```

Confirm:

1. RPG Soundboard is outputting to `CABLE Input`.
2. Dark Between Audio is capturing `CABLE Output`.
3. `Start Input` has been pressed.
4. The Discord bot is connected to a voice channel.
5. Input volume is not set to 0%.

---

## Audio Device Appears Multiple Times

Windows exposes audio devices through several APIs such as:

```text
MME
DirectSound
WASAPI
WDM-KS
```

Dark Between Audio attempts to hide duplicate versions and prefer a sensible Windows backend.

---

## YouTube Is Very Quiet

Increase the YouTube volume control.

Some sources may require levels above 100%.

Be aware that aggressive amplification may cause clipping.

---

## FFmpeg Is Not Found

Run:

```powershell
ffmpeg -version
```

If the command fails, install FFmpeg or add its executable directory to your Windows PATH.

---

# Security

Never publish your `.env` file.

Never publish your Discord bot token.

The repository should always ignore:

```text
.env
```

If a token is accidentally exposed:

1. Open the Discord Developer Portal.
2. Reset the bot token.
3. Update `.env`.
4. Restart Dark Between Audio.

---

# Development Status

Dark Between Audio v1 currently has a complete working audio pipeline.

Core functionality includes:

```text
Discord voice connection
Multi-source PCM mixing
External audio capture
VB-CABLE soundboard routing
Local-file playback
YouTube playback
Independent source controls
Per-source volume
Master volume
Persistent settings
Dark-mode GUI
Clean shutdown
```

Future improvements may include:

```text
Packaged Windows executable
Installer
Improved error reporting
Audio level meters
Limiter / clipping protection
Automatic prerequisite checks
More polished status indicators
```

---

# License

License information will be added before the first public release.

VB-Audio Virtual Cable, FFmpeg, Discord, YouTube, and other third-party software are separate projects and are governed by their respective licenses and terms.

Dark Between Audio does not include or claim ownership of those third-party projects.