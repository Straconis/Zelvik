# Dark Between Audio

Dark Between Audio is a Windows desktop application for routing music, sound effects, soundboards, local audio files, and YouTube audio into a Discord voice channel through a Discord bot.

It was originally built for tabletop RPG sessions, allowing a GM to add music, ambience, sound effects, and other audio to Discord without mixing everything into their microphone.

## Features

- Discord voice-channel audio bot
- External audio input support
- Works with virtually any soundboard through VB-Audio Virtual Cable
- YouTube audio playback
- YouTube start and stop timestamps
- YouTube looping
- Local audio file playback
- Independent volume controls for:
  - External audio
  - YouTube
  - Local audio
  - Master output
- Stop individual audio sources
- Stop all audio instantly
- Remembers:
  - Selected audio input device
  - Volume settings
  - YouTube loop setting
  - Discord server
  - Discord voice channel
- Dark-mode interface
- Discord bot token stored securely using Windows Credential Manager
- No Voicemeeter required

---

# How It Works

Dark Between Audio acts as the audio source for a Discord bot.

For external programs such as RPG Soundboard, the audio path looks like this:

```text
Soundboard / Audio Program
          |
          v
      CABLE Input
          |
          v
  VB-Audio Virtual Cable
          |
          v
      CABLE Output
          |
          v
   Dark Between Audio
          |
          v
      Discord Bot
          |
          v
 Discord Voice Channel
```

YouTube and local audio files are handled directly by Dark Between Audio and mixed with the external audio source.

---

# Windows Installation

## 1. Download Dark Between Audio

Download the latest Windows release of Dark Between Audio and extract it if necessary.

Run:

```text
DarkBetweenAudio.exe
```

The application does not require Python when using the packaged Windows executable.

You will still need:

- A Discord bot that you create
- VB-Audio Virtual Cable for external soundboard/application audio
- FFmpeg for audio processing and YouTube playback

---

# 2. Install VB-Audio Virtual Cable

Dark Between Audio uses VB-CABLE to receive audio from another Windows application such as RPG Soundboard.

Official VB-Audio page:

https://vb-audio.com/Cable/index.htm

Download the VB-CABLE driver package.

Extract the downloaded archive and run the appropriate VB-CABLE setup program as **Administrator**.

Reboot Windows after installation.

After installation, Windows should expose devices named approximately:

```text
CABLE Input
CABLE Output
```

The naming can seem backwards at first.

Applications SEND audio to:

```text
CABLE Input
```

Dark Between Audio LISTENS to:

```text
CABLE Output
```

VB-Audio describes VB-CABLE as forwarding audio arriving at CABLE Input directly to CABLE Output.

---

# 3. Install FFmpeg

Dark Between Audio uses FFmpeg for audio processing.

Official FFmpeg download page:

https://ffmpeg.org/download.html

Windows users need a Windows build of FFmpeg.

The FFmpeg download page provides links to precompiled Windows builds.

After installing FFmpeg, make sure the directory containing:

```text
ffmpeg.exe
```

is included in the Windows `PATH`.

You can verify FFmpeg from PowerShell:

```powershell
ffmpeg -version
```

If FFmpeg prints version information, it is available to Dark Between Audio.

---

# 4. Create Your Discord Bot

Every Dark Between Audio user should create their **own Discord bot**.

Do not use someone else's bot token.

Open the Discord Developer Portal:

https://discord.com/developers/applications

Sign into Discord if necessary.

## Create the Application

Click:

```text
New Application
```

Give the application a name.

For example:

```text
Dark Between Audio
```

or:

```text
My D&D Audio Bot
```

Create the application.

---

# 5. Configure the Discord Bot

Inside your new Discord application, open:

```text
Bot
```

Create the bot if Discord has not already created one for the application.

You can customize its:

- Username
- Avatar
- Description

These settings only affect how your bot appears in Discord.

## Get Your Bot Token

In the Bot section, locate the bot token controls.

Discord may require you to use:

```text
Reset Token
```

to generate or reveal a token.

Copy the token.

## IMPORTANT: Keep Your Token Private

Your Discord bot token is effectively the password for your bot.

Never:

- Post it publicly
- Put it in screenshots
- Commit it to GitHub
- Send it to another person
- Include it in bug reports

If you accidentally expose the token, return to the Discord Developer Portal and reset it immediately.

Dark Between Audio stores the token locally using **Windows Credential Manager**.

---

# 6. Generate Your Discord Bot Installation Link

Your bot needs to be installed on the Discord server where you want to use Dark Between Audio.

Inside the Discord Developer Portal, configure your application's installation/OAuth2 settings.

The exact Discord Developer Portal interface may change over time, but your goal is to create an installation link for your bot.

The bot needs permission to:

```text
View Channels
Connect
Speak
```

Generate or copy the installation/authorization link for **your own application**.

Open that link in your browser.

Select the Discord server where you want to install the bot and authorize it.

You must have sufficient permissions on that Discord server to install applications/bots.

Once authorized, your bot should appear as a member of the server.

It may appear offline until Dark Between Audio is running. This is normal.

---

# 7. First Launch

Run:

```text
DarkBetweenAudio.exe
```

On the first launch, Dark Between Audio will ask for your Discord bot token.

Paste the token you copied from the Discord Developer Portal.

The token field is hidden by default.

You can use:

```text
Show token
```

to verify the token before saving it.

Click:

```text
Save & Connect
```

Dark Between Audio stores the token using Windows Credential Manager.

You do not need to create a `.env` file when using the normal Windows EXE.

On future launches, Dark Between Audio will retrieve the saved token automatically.

---

# 8. Changing Your Discord Token

If you:

- Reset your Discord bot token
- Entered the wrong token
- Want to use another bot

click:

```text
Change Discord Token
```

inside Dark Between Audio.

Enter the replacement token and save it.

Restart Dark Between Audio after changing the token.

The new bot token will be used on the next launch.

---

# 9. Connect Dark Between Audio to Discord

After the application connects to Discord, select your:

```text
Server
```

and:

```text
Voice Channel
```

Then click:

```text
Join Channel
```

The bot should join the selected Discord voice channel.

Dark Between Audio remembers the selected server and voice channel for future sessions.

---

# 10. Configure a Soundboard

Dark Between Audio does not require a particular soundboard.

Any Windows application capable of sending audio to VB-CABLE can potentially be used.

In your soundboard or audio program, set its output device to:

```text
CABLE Input
```

Then open Dark Between Audio.

Under:

```text
External Audio Input
```

select:

```text
CABLE Output
```

The device may include additional text depending on the Windows audio API.

For example:

```text
CABLE Output (VB-Audio Virtual Cable) [MME]
```

Dark Between Audio remembers the selected input device.

Click:

```text
Start Input
```

Audio sent by the soundboard to CABLE Input should now be transmitted through the Discord bot.

Use the External Audio Input volume slider to adjust the level.

---

# YouTube Playback

Dark Between Audio can play audio from supported YouTube URLs.

Paste a YouTube URL into:

```text
YouTube URL
```

Then click:

```text
Play YouTube
```

Use:

```text
Stop YouTube
```

to stop YouTube playback without stopping your other audio sources.

## Start Timestamp

You can begin playback at a specific point.

Supported formats include:

```text
90
```

```text
1:30
```

```text
01:30
```

```text
1:02:30
```

## Stop Timestamp

You can optionally specify when playback should stop.

For example:

```text
Start: 1:30
Stop: 2:15
```

Only that section of the source will be played.

The stop timestamp must occur after the start timestamp.

## Loop

Enable:

```text
Loop
```

to repeat the selected YouTube audio.

This is useful for:

- Background music
- Combat music
- Ambience
- Environmental audio
- TTRPG scenes

## YouTube Volume

The YouTube volume control can be adjusted independently of:

- External audio
- Local audio
- Master output

---

# Local Audio Playback

Dark Between Audio can also play audio files directly.

Click:

```text
Select Sound
```

Select an audio file.

Supported file selections currently include:

```text
MP3
WAV
OGG
FLAC
```

Click:

```text
Play Sound
```

to play the file through Discord.

Use:

```text
Stop Local Audio
```

to stop local playback without stopping the external input or YouTube.

The Local Audio volume control is independent of the other audio sources.

---

# Master Volume

The Master Output volume controls the overall audio level being sent through Dark Between Audio.

Individual sources can still be adjusted separately.

This allows a setup such as:

```text
External Soundboard: 100%
YouTube Music:         70%
Local Audio:          120%
Master Output:         90%
```

---

# Stop All Audio

The:

```text
STOP ALL AUDIO
```

button immediately stops active audio sources.

This is useful during a game if you need everything to become silent immediately.

---

# Recommended TTRPG Setup

A typical setup is:

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
      +---- YouTube
      |
      +---- Local Audio Files
      |
      v
Discord Bot
      |
      v
Discord Voice Channel
```

This keeps the GM's microphone separate from music and sound effects.

That can also make Discord recordings and post-session transcription easier because the audio bot appears as its own Discord participant rather than being mixed into the GM's microphone.

---

# Troubleshooting

## The Bot Does Not Connect

Verify that:

- The bot is installed on your Discord server
- The bot token is correct
- The bot has permission to view and connect to the voice channel
- Your internet connection is working

If you reset the token in the Discord Developer Portal, use:

```text
Change Discord Token
```

and restart Dark Between Audio.

---

## The Bot Is Offline in Discord

The bot only connects to Discord while Dark Between Audio is running.

If Dark Between Audio is closed, the bot appearing offline is normal.

---

## The Bot Connects but Does Not Join Voice

Verify that the bot has:

```text
View Channels
Connect
Speak
```

permissions for the selected voice channel.

Also verify that you selected the correct server and channel inside Dark Between Audio.

---

## Soundboard Audio Is Not Reaching Discord

Verify the complete audio path.

Your soundboard should output to:

```text
CABLE Input
```

Dark Between Audio should listen to:

```text
CABLE Output
```

Then click:

```text
Start Input
```

Also verify that the bot has already joined the Discord voice channel.

---

## CABLE Input / CABLE Output Do Not Appear

Reinstall VB-Audio Virtual Cable from:

https://vb-audio.com/Cable/index.htm

Run the installer as Administrator and reboot Windows afterward.

---

## YouTube Does Not Play

Verify that FFmpeg is installed:

```powershell
ffmpeg -version
```

If PowerShell cannot find FFmpeg, add the FFmpeg `bin` directory to your Windows PATH.

YouTube playback also depends on yt-dlp when running the project from source.

Because YouTube changes frequently, updating yt-dlp may resolve playback problems for source installations:

```powershell
python -m pip install --upgrade yt-dlp
```

---

## Audio Is Too Quiet

Dark Between Audio provides separate volume controls for:

```text
External Input
YouTube
Local Audio
Master Output
```

Some sources may require a level above 100%.

External, YouTube, and local audio controls support amplification above 100%.

Be careful when increasing volume substantially, as clipping or distortion may occur.

---

# Running From Source

The Windows EXE is recommended for normal users.

Developers can run Dark Between Audio directly from Python.

## Requirements

Recommended:

```text
Windows 10 or Windows 11
Python 3.11+
FFmpeg
VB-Audio Virtual Cable
```

Clone the repository and enter the project directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run Dark Between Audio:

```powershell
python main.py
```

---

# Developer Token Configuration

Developers may use the same Windows Credential Manager setup as EXE users.

Dark Between Audio also supports:

```text
DISCORD_TOKEN
```

from a `.env` file or environment variable.

For example:

```text
DISCORD_TOKEN=your_bot_token_here
```

If `DISCORD_TOKEN` is present in the environment or `.env`, it takes priority over the token stored in Windows Credential Manager.

Never commit `.env` files containing tokens to source control.

Your `.gitignore` should include:

```text
.env
.venv/
__pycache__/
build/
dist/
```

---

# Updating Dependencies

With the virtual environment activated:

```powershell
pip install --upgrade pip
```

To refresh the project's dependency list:

```powershell
pip freeze > requirements.txt
```

---

# Building the Windows EXE

Dark Between Audio can be packaged using PyInstaller.

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install PyInstaller if necessary:

```powershell
pip install pyinstaller
```

## Diagnostic Build

Create a console-enabled build first:

```powershell
pyinstaller --clean --onefile --name "DarkBetweenAudio" main.py
```

The executable will be created at:

```text
dist\DarkBetweenAudio.exe
```

Run it:

```powershell
.\dist\DarkBetweenAudio.exe
```

The diagnostic build leaves the console visible so startup errors and dependency problems can be inspected.

Test:

- First-run Discord token setup
- Windows Credential Manager token persistence
- Discord connection
- Server selection
- Voice-channel selection
- Voice connection
- VB-CABLE input
- External audio
- YouTube playback
- YouTube timestamps
- YouTube looping
- Local file playback
- Individual volume controls
- Master volume
- Stop controls
- Change Discord Token
- Application shutdown

---

# Release Build

After the diagnostic build passes, create the GUI-only release build:

```powershell
pyinstaller --clean --onefile --windowed --name "DarkBetweenAudio" main.py
```

The finished executable will be:

```text
dist\DarkBetweenAudio.exe
```

The `--onefile` option creates a single executable.

The `--windowed` option prevents the Python console window from appearing when the GUI starts.

The `--clean` option clears PyInstaller's build cache before creating the build.

---

# Testing the Release Build

Do not test the release EXE only from inside the source repository.

Copy it to a separate directory:

```powershell
New-Item C:\Temp\DarkBetweenAudioTest -ItemType Directory -Force
Copy-Item .\dist\DarkBetweenAudio.exe C:\Temp\DarkBetweenAudioTest\
Set-Location C:\Temp\DarkBetweenAudioTest
.\DarkBetweenAudio.exe
```

This helps identify dependencies that may accidentally be available only because the EXE was launched from the development directory.

A clean-machine test is strongly recommended before publishing a release.

---

# Project Philosophy

Dark Between Audio is intended to solve a simple problem:

> Get soundboard audio, music, ambience, and sound effects into Discord without forcing everything through the user's microphone or requiring a complicated audio-mixing setup.

VB-Audio Virtual Cable provides the bridge for external applications, while Dark Between Audio handles Discord, YouTube, local audio, mixing, and volume control.

The goal is to keep the workflow simple enough that a GM can spend time running the game instead of fighting with audio-routing software.

---

# Security

Dark Between Audio does not require your Discord account password.

It uses a Discord **bot token** belonging to a bot application you create.

For normal Windows installations, the token is stored using Windows Credential Manager.

Treat your bot token as a password.

If it is ever exposed:

1. Open the Discord Developer Portal.
2. Select your application.
3. Open the Bot section.
4. Reset the token.
5. Copy the replacement token.
6. Open Dark Between Audio.
7. Click `Change Discord Token`.
8. Save the replacement token.
9. Restart Dark Between Audio.

Never publish a working Discord bot token in GitHub.

---

# Third-Party Software

Dark Between Audio uses or interoperates with several third-party projects.

## Discord

https://discord.com/developers/applications

Used for Discord bot applications and voice-channel connectivity.

## VB-Audio Virtual Cable

https://vb-audio.com/Cable/index.htm

Provides the virtual Windows audio connection used to route external soundboard/application audio into Dark Between Audio.

VB-CABLE is developed by VB-Audio Software.

## FFmpeg

https://ffmpeg.org/

Used for audio processing.

## yt-dlp

https://github.com/yt-dlp/yt-dlp

Used for resolving supported online media sources.

## PySide6

https://doc.qt.io/qtforpython-6/

Used for the Windows graphical interface.

## PyInstaller

https://pyinstaller.org/

Used to package Dark Between Audio as a Windows executable.

---

# Disclaimer

Dark Between Audio is an independent project and is not affiliated with or endorsed by Discord, VB-Audio, FFmpeg, YouTube, Google, or the developers of any third-party soundboard software.

Users are responsible for complying with the terms of service, copyright rules, licenses, and laws applicable to the media and services they use with Dark Between Audio.

Dark Between Audio does not grant rights to copyrighted audio or video content.