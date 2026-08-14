# Dark Between Audio

Dark Between Audio is a Windows desktop audio bridge for Discord.

It allows soundboards, local audio files, and YouTube audio to play through a dedicated Discord bot instead of being mixed into your microphone.

The primary use case is tabletop RPGs, where a DM can send ambience, music, sound effects, soundboard audio, and other audio directly into a Discord voice channel.

## Features

Dark Between Audio can:

- Connect a dedicated bot to a Discord voice channel
- Capture audio from a Windows audio input
- Route virtually any soundboard through VB-CABLE
- Play local audio files
- Play YouTube audio
- Start YouTube playback at a specified timestamp
- Stop YouTube playback at a specified timestamp
- Loop YouTube playback
- Mix multiple audio sources simultaneously
- Control individual source volumes
- Apply a master output volume
- Start and stop sources independently
- Remember commonly used settings
- Run from a dark-mode Windows desktop control panel

## How It Works

A typical soundboard setup looks like this:

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

Dark Between Audio does not require a specific soundboard.

As long as an application can send its audio to a Windows playback device, it can potentially be routed through VB-CABLE and into Dark Between Audio.

---

# Requirements

Dark Between Audio v1 currently targets Windows.

## Recommended Python Version

Use:

```text
Python 3.11 or Python 3.12
```

Python 3.10 may still work, but some of the project's dependencies have begun deprecating support for it.

Python 3.13+ is not currently recommended because the audio mixer uses Python's `audioop` module, which was removed in Python 3.13.

## Required Software

You will need:

- Python 3.11 or 3.12
- FFmpeg
- VB-Audio Virtual Cable if you want to route another application into the bot
- A Discord application/bot
- Dark Between Audio's Python dependencies

---

# 1. Install Python

Download Python from the official Python website:

https://www.python.org/downloads/

Python 3.11 or 3.12 is currently recommended.

During installation, enable:

```text
Add python.exe to PATH
```

After installation, open PowerShell and verify Python:

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

FFmpeg's official website is:

https://ffmpeg.org/

Windows builds are available from several providers linked by the FFmpeg project.

One commonly used Windows build provider is:

https://www.gyan.dev/ffmpeg/builds/

After installing FFmpeg, make sure its `bin` directory is available in your Windows PATH.

Verify the installation from PowerShell:

```powershell
ffmpeg -version
```

If FFmpeg displays version information, it is configured correctly.

If Windows reports that `ffmpeg` is not recognized, FFmpeg is either not installed or its executable directory is not in your PATH.

---

# 3. Install VB-Audio Virtual Cable

Dark Between Audio can capture normal Windows audio input devices, but VB-Audio Virtual Cable provides a simple way to route a soundboard or other application into the bot without mixing that audio into your microphone.

Download VB-CABLE from the official VB-Audio website:

https://vb-audio.com/Cable/index.htm

Install VB-CABLE according to the instructions provided by VB-Audio.

A Windows reboot may be required after installation.

After installation, Windows should expose devices named similar to:

```text
CABLE Input
CABLE Output
```

## Understanding CABLE Input and CABLE Output

The naming can initially seem backwards.

Your application sends audio **into**:

```text
CABLE Input
```

Dark Between Audio captures audio **from**:

```text
CABLE Output
```

The route looks like this:

```text
Soundboard / Application
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

## Example: RPG Soundboard

Configure RPG Soundboard's output device as:

```text
CABLE Input (VB-Audio Virtual Cable)
```

Then select this device inside Dark Between Audio:

```text
CABLE Output (VB-Audio Virtual Cable)
```

Press:

```text
Start Input
```

Audio played by RPG Soundboard should now be transmitted through the Dark Between Audio Discord bot.

The same basic setup can be used with other soundboards or applications that allow you to select their Windows audio output device.

---

# 4. Create a Discord Application

Dark Between Audio uses your own Discord bot to transmit audio.

Open the Discord Developer Portal:

https://discord.com/developers/applications

Sign in with your Discord account and select:

```text
New Application
```

Give the application a name.

For example:

```text
Dark Between Audio
```

After creating the application, open its:

```text
Bot
```

section.

Create or configure the bot associated with the application.

---

# 5. Configure Discord Bot Permissions

Dark Between Audio does not need Administrator access to your Discord server.

The bot needs permission to:

```text
View Channels
Connect
Speak
```

The bot must have these permissions in any voice channel where you want Dark Between Audio to operate.

Dark Between Audio v1 is controlled through its Windows GUI rather than Discord text commands, so normal operation does not require Message Content Intent.

---

# 6. Add the Bot to Your Discord Server

Use the installation settings in the Discord Developer Portal to install the application into your Discord server.

The bot should be granted the permissions listed above:

```text
View Channels
Connect
Speak
```

After installation, the bot should appear in your server's member list.

The bot will normally appear offline when Dark Between Audio is not running.

That is expected.

When Dark Between Audio starts and successfully connects to Discord, the bot should appear online.

---

# 7. Get Your Discord Bot Token

Your Discord bot token is effectively the password for your bot.

Treat it like a password.

In the Discord Developer Portal:

1. Open your Dark Between Audio application.
2. Open the `Bot` section.
3. Generate, reset, or copy the bot token.
4. Store it only in your local `.env` file.

## IMPORTANT SECURITY WARNING

Never:

```text
Post your bot token in Discord
Share your bot token with another person
Include your bot token in screenshots
Commit your bot token to GitHub
Put your bot token directly into the Python source code
```

If your token is ever exposed, immediately reset it through the Discord Developer Portal.

The old token will stop working after it has been reset.

---

# 8. Configure the `.env` File

Dark Between Audio reads your Discord bot token from a local `.env` file.

In the root Dark Between Audio directory, create:

```text
.env
```

Add:

```text
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
```

For example:

```text
DISCORD_TOKEN=abc123exampletoken
```

Do not use the example token above.

Use the actual token generated for your Discord bot.

Do not add quotes around the token unless they are actually part of the value.

The repository includes an `.env.example` file that can be used as a template.

Your real `.env` file should never be committed to Git.

The project's `.gitignore` should include:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# 9. Download Dark Between Audio

Clone the repository using Git:

```powershell
git clone https://github.com/Straconis/dark-between-audio.git
```

Enter the project directory:

```powershell
cd dark-between-audio
```

Alternatively, download the repository as a ZIP file from GitHub and extract it to a folder on your computer.

---

# 10. Create the Python Virtual Environment

Open PowerShell in the Dark Between Audio directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your PowerShell prompt should change to something similar to:

```text
(.venv) PS C:\Projects\dark-between-audio>
```

You must activate the virtual environment again whenever you open a new PowerShell window.

## PowerShell Execution Policy

If Windows prevents `Activate.ps1` from running because script execution is disabled, you may need to adjust the PowerShell execution policy for your user account.

Consult Microsoft's PowerShell documentation before changing security settings on your system.

---

# 11. Install Python Dependencies

With the virtual environment active, install the required Python packages:

```powershell
pip install -r requirements.txt
```

Dark Between Audio currently uses packages including:

```text
discord.py
python-dotenv
PyNaCl
davey
PySide6
sounddevice
yt-dlp
```

The exact dependency versions used by the project are listed in:

```text
requirements.txt
```

---

# 12. Run Dark Between Audio

Make sure the virtual environment is active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then start Dark Between Audio:

```powershell
python main.py
```

The Dark Between Audio control panel should open.

If the Discord token is valid, the bot should connect to Discord and appear online.

---

# Using Dark Between Audio

## Discord Connection

At the top of the application:

1. Select your Discord server.
2. Select the desired voice channel.
3. Press `Join Channel`.

The bot should enter the selected Discord voice channel.

Press:

```text
Leave Channel
```

to disconnect it.

Dark Between Audio remembers the previously selected Discord server and voice channel.

---

# External Audio Input

The External Audio Input section is intended for soundboards and other applications.

For a standard VB-CABLE configuration, select:

```text
CABLE Output (VB-Audio Virtual Cable)
```

Then press:

```text
Start Input
```

Play audio through the application that has been routed to:

```text
CABLE Input
```

The audio should now be transmitted to Discord through the Dark Between Audio bot.

## Input Volume

Use the Input Volume slider to adjust the level of the external audio source.

Values above 100% amplify the source and may cause clipping if pushed too high.

## Stop Input

Press:

```text
Stop Input
```

to stop only the external audio source.

This does not stop:

```text
YouTube
Local audio files
```

The selected input device and volume are remembered between sessions.

---

# Local File Playback

Dark Between Audio can play local audio files directly.

Commonly supported formats include:

```text
MP3
WAV
OGG
FLAC
```

Actual format support depends on FFmpeg.

Press:

```text
Select Sound
```

and choose an audio file.

Then press:

```text
Play Sound
```

Multiple local sounds can play simultaneously.

This is useful for layering sound effects over ambience or music.

## Local Volume

Use the Local Volume slider to control local-file playback volume.

## Stop Local Audio

Press:

```text
Stop Local Audio
```

to stop local files without affecting:

```text
External Input
YouTube
```

---

# YouTube Playback

Dark Between Audio includes YouTube audio playback support.

Paste a YouTube URL into the YouTube URL field.

Then press:

```text
Play YouTube
```

Dark Between Audio uses `yt-dlp` and FFmpeg as part of the playback pipeline.

## Start Timestamp

You can optionally specify where playback should begin.

Supported examples:

```text
10
```

means:

```text
10 seconds
```

This:

```text
01:30
```

means:

```text
1 minute 30 seconds
```

And:

```text
1:02:30
```

means:

```text
1 hour 2 minutes 30 seconds
```

## Stop Timestamp

The Stop field allows playback to stop at a specified point.

For example:

```text
Start: 18:35
Stop:  26:10
```

Only the selected portion should play.

The Stop timestamp must occur after the Start timestamp.

## Loop

Enable:

```text
Loop
```

to repeat playback.

When Start and Stop timestamps are configured, the selected section can be repeated.

## YouTube Volume

YouTube sources can vary considerably in loudness.

The YouTube volume control allows amplification above the original source level.

```text
100% = normal source level
```

Values above 100% amplify the audio.

High amplification can introduce clipping or distortion.

## Stop YouTube

Press:

```text
Stop YouTube
```

to stop YouTube playback without stopping:

```text
External Input
Local audio files
```

---

# Content and Copyright

Dark Between Audio is an audio-routing and playback utility.

You are responsible for ensuring that you have the appropriate rights, licenses, or permissions to play, stream, transmit, or otherwise use content through the software.

Dark Between Audio is not intended to bypass DRM, access controls, subscription restrictions, or other content protections.

YouTube and other third-party services have their own terms of service and usage requirements.

---

# Master Volume

The Master Output control adjusts the level of the final mixed Discord audio stream.

It affects:

```text
External Input
YouTube
Local Files
```

Individual source volume controls are applied separately from the master output level.

For example:

```text
Soundboard Volume
        +
YouTube Volume
        +
Local File Volume
        |
        v
     Mixer
        |
        v
 Master Volume
        |
        v
     Discord
```

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

This is useful as an emergency silence button during a session.

---

# Exit

Use the:

```text
Exit
```

button or close the application window normally.

Dark Between Audio will attempt to:

```text
Stop active audio
Terminate active audio processes
Disconnect from Discord voice
Close the Discord connection
Exit cleanly
```

Using the application's Exit button is preferable to terminating the application with `Ctrl+C`.

---

# Audio Mixing

Dark Between Audio contains a multi-source PCM audio mixer.

This allows combinations such as:

```text
RPG Soundboard ambience
        +
YouTube music
        +
Local sound effect
        |
        v
One Discord bot audio stream
```

Sources operate independently.

Stopping one source should not stop the others.

For example, you can:

1. Run continuous ambience from RPG Soundboard through VB-CABLE.
2. Start YouTube music over the ambience.
3. Trigger a local sound effect.
4. Stop the YouTube music.
5. Leave the ambience running.

---

# Saved Settings

Dark Between Audio remembers several settings between sessions.

These currently include:

```text
Audio input device
Discord server
Discord voice channel
External input volume
YouTube volume
Local-file volume
Master volume
YouTube loop setting
```

The Discord bot token is intentionally handled separately through `.env`.

The application does not save the token through its normal GUI settings.

---

# Project Structure

```text
dark-between-audio/
|
|-- main.py
|-- .env
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- README.md
|
|-- audio/
|   |-- __init__.py
|   |-- mixer.py
|   |-- source.py
|   |-- input_source.py
|   `-- youtube_source.py
|
|-- bot/
|   |-- __init__.py
|   `-- discord_client.py
|
`-- gui/
    |-- __init__.py
    `-- main_window.py
```

Your `.env` and `.venv` directories should remain local and should not be committed to the repository.

---

# Troubleshooting

## `ModuleNotFoundError`

For example:

```text
ModuleNotFoundError: No module named 'PySide6'
```

The most common cause is that the project's virtual environment is not active or the dependencies have not been installed.

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install dependencies if necessary:

```powershell
pip install -r requirements.txt
```

Run the application:

```powershell
python main.py
```

---

## Bot Is Offline

The bot is normally offline when Dark Between Audio is not running.

Start the application:

```powershell
python main.py
```

If the bot remains offline, verify that:

```text
.env
```

exists and contains:

```text
DISCORD_TOKEN=your_actual_token
```

Also verify that the token has not been reset in the Discord Developer Portal.

---

## Bot Cannot Join the Voice Channel

Verify that the bot has permission to:

```text
View Channels
Connect
Speak
```

in the target voice channel.

Discord channel-specific permission overrides can prevent a bot from connecting even when its server-level role normally allows it.

---

## Privileged Intents Error

If you modify Dark Between Audio to use privileged Discord gateway intents, those intents must also be enabled for the bot in the Discord Developer Portal.

The standard v1 GUI-controlled audio functionality should not require Message Content Intent.

---

## `davey library needed in order to use voice`

If you receive an error similar to:

```text
RuntimeError: davey library needed in order to use voice
```

make sure the virtual environment is active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install the project's dependencies:

```powershell
pip install -r requirements.txt
```

Or install `davey` directly:

```powershell
pip install davey
```

Restart Dark Between Audio afterward.

---

## No Sound From a Soundboard

Check the complete audio route:

```text
Soundboard
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

Confirm that:

1. Your soundboard is outputting to `CABLE Input`.
2. Dark Between Audio is capturing `CABLE Output`.
3. `Start Input` has been pressed.
4. The Discord bot has joined a voice channel.
5. Input volume is not set to 0%.
6. Master volume is not set to 0%.

---

## I Cannot Hear the Soundboard Locally

When an application's output is routed exclusively to VB-CABLE, Windows may no longer send that application's audio directly to your speakers or headset.

This does not necessarily mean Dark Between Audio is malfunctioning.

The important signal path for the bot is:

```text
Application -> CABLE Input -> CABLE Output -> Dark Between Audio
```

Local monitoring may require additional Windows audio routing depending on your desired configuration.

---

## Audio Device Appears Multiple Times

Windows exposes audio devices through multiple audio APIs, including:

```text
MME
DirectSound
WASAPI
WDM-KS
```

This can make the same physical or virtual audio device appear several times.

Dark Between Audio attempts to remove duplicate entries and prefer a sensible Windows audio backend.

---

## YouTube Is Very Quiet

Increase the YouTube volume slider.

Some sources have significantly lower playback levels than others.

Values above 100% amplify the audio.

If the volume is increased too far, clipping or distortion may occur.

---

## YouTube Does Not Play

First verify that FFmpeg works:

```powershell
ffmpeg -version
```

Then verify that `yt-dlp` is installed:

```powershell
yt-dlp --version
```

If necessary, update `yt-dlp`:

```powershell
python -m pip install -U yt-dlp
```

YouTube periodically changes its delivery systems, so an outdated `yt-dlp` version may stop resolving some sources.

---

## FFmpeg Is Not Found

Run:

```powershell
ffmpeg -version
```

If Windows reports that the command does not exist, FFmpeg is either not installed or its executable directory is not included in your Windows PATH.

See:

https://ffmpeg.org/

---

## PowerShell Does Not Show `(.venv)`

If your prompt looks like:

```text
PS C:\Projects\dark-between-audio>
```

instead of:

```text
(.venv) PS C:\Projects\dark-between-audio>
```

activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python main.py
```

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
2. Open your application.
3. Open the Bot section.
4. Reset the bot token.
5. Replace the old token in `.env`.
6. Restart Dark Between Audio.

A Discord bot token that has been committed to Git should be considered compromised even if the commit is later deleted.

Reset the token rather than relying only on removing it from Git history.

---

# Development

To start a development session:

```powershell
cd C:\Projects\dark-between-audio
.\.venv\Scripts\Activate.ps1
python main.py
```

Check the current Git branch:

```powershell
git branch --show-current
```

Check repository status:

```powershell
git status
```

---

# Dark Between Audio v1

The v1 audio pipeline includes:

```text
Discord voice connection
Multi-source PCM mixing
External Windows audio capture
VB-CABLE soundboard routing
Local-file playback
YouTube playback
YouTube start/stop timestamps
YouTube looping
Independent source controls
Per-source volume controls
Master volume control
Persistent settings
Dark-mode GUI
Clean application shutdown
```

---

# Future Improvements

Possible future improvements include:

- Packaged Windows executable
- Windows installer
- Automatic prerequisite checks
- Improved GUI error reporting
- More accurate source-status reporting
- Audio level meters
- Master mute
- Limiter / clipping protection
- Additional audio routing options
- Improved YouTube metadata/status display

The goal is to keep Dark Between Audio relatively simple rather than turning it into a full digital audio workstation.

---

# Third-Party Software and Services

Dark Between Audio interacts with or depends on third-party software and services including:

- Discord
- FFmpeg
- VB-Audio Virtual Cable
- Python
- yt-dlp
- PySide6
- PortAudio / sounddevice

These projects are separate from Dark Between Audio and are governed by their own licenses, terms, and policies.

Official VB-Audio Virtual Cable page:

https://vb-audio.com/Cable/index.htm

Official FFmpeg website:

https://ffmpeg.org/

Official Python website:

https://www.python.org/

Discord Developer Portal:

https://discord.com/developers/applications

---

# License

License information will be added before the first public release.

Dark Between Audio does not include or claim ownership of Discord, YouTube, VB-Audio Virtual Cable, FFmpeg, Python, yt-dlp, PySide6, or other third-party projects used alongside it.