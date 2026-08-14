# Zelvik

Zelvik is a Windows desktop application for routing music, sound effects, soundboards, local audio files, and YouTube audio into a Discord voice channel through a Discord bot.

Originally developed as Dark Between Audio for tabletop RPG sessions, Zelvik allows a GM, player, streamer, or other Discord user to add music, ambience, sound effects, and other audio without mixing everything into their microphone.

Zelvik handles Discord connectivity, audio mixing, YouTube playback, local audio playback, external application capture, and Windows per-application audio routing from a single interface.

## Features

- Discord voice-channel audio bot
- Windows 10 and Windows 11 support
- External application audio input
- Automatic Windows per-application audio routing
- Select an application and route it directly to a virtual audio cable
- Enable/disable routing from Zelvik
- Restore an application to the Windows default output when routing is disabled
- Live verification of the actual Windows routing state
- Windows Sound Settings fallback
- Works with virtually any Windows soundboard through VB-Audio Virtual Cable
- No Voicemeeter required
- YouTube audio playback
- YouTube start and stop timestamps
- YouTube looping
- Optional YouTube authentication using imported browser cookies
- Managed local copy of imported YouTube cookies
- YouTube authentication status checking
- Automatic retry of transient YouTube playback failures
- Live YouTube activity and error information in the GUI
- Local audio file playback
- Independent volume controls for:
  - External audio
  - YouTube
  - Local audio
  - Master output
- Stop individual audio sources
- Stop all audio instantly
- Live Zelvik Status traffic-light indicators
- Remembers:
  - Selected audio input device
  - Windows routing application
  - Windows routing output device
  - Volume settings
  - YouTube loop setting
  - Discord server
  - Discord voice channel
- Scrollable dark-mode interface
- Discord bot token stored securely using Windows Credential Manager

---

# How It Works

Zelvik acts as the audio source for a Discord bot.

There are two primary audio paths.

## External Application Audio

For external programs such as RPG Soundboard, Zelvik can configure the Windows per-application audio route automatically.

```text
Soundboard / Audio Program
          |
          |  Zelvik configures
          |  the Windows app route
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
        Zelvik
          |
          v
      Discord Bot
          |
          v
 Discord Voice Channel
```

## Internal Audio Sources

YouTube and local audio files are handled directly by Zelvik and do not require Windows application routing.

```text
YouTube --------+
                |
Local File -----+----> Zelvik ----> Discord Bot
```

All active sources are mixed by Zelvik before being sent to Discord.

This keeps music and sound effects separate from the user's microphone.

---

# Windows Installation

## 1. Download Zelvik

Download the latest Windows release of Zelvik and extract it if necessary.

Run:

```text
Zelvik.exe
```

The application does not require Python when using the packaged Windows executable.

You will still need:

- A Discord bot that you create
- VB-Audio Virtual Cable for external soundboard/application audio
- FFmpeg for audio processing and YouTube playback
- Deno for current YouTube extraction support

---

# 2. Install VB-Audio Virtual Cable

Zelvik uses VB-CABLE to receive audio from another Windows application such as RPG Soundboard.

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

Zelvik LISTENS to:

```text
CABLE Output
```

VB-Audio describes VB-CABLE as forwarding audio arriving at CABLE Input directly to CABLE Output.

Additional VB-Audio virtual cable products can also be used.

---

# 3. Install FFmpeg

Zelvik uses FFmpeg for audio processing.

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

If FFmpeg prints version information, it is available to Zelvik.

---

# 4. Install Deno

Current versions of yt-dlp use an external JavaScript runtime when working with YouTube.

Deno is the recommended runtime and is enabled by default by yt-dlp.

Install Deno from PowerShell:

```powershell
irm https://deno.land/install.ps1 | iex
```

After installation, verify it with:

```powershell
deno --version
```

If PowerShell cannot immediately find `deno`, close and reopen PowerShell and try again.

---

# 5. Create Your Discord Bot

Every Zelvik user should create their **own Discord bot**.

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
Zelvik
```

or:

```text
My D&D Audio Bot
```

Create the application.

---

# 6. Configure the Discord Bot

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

Zelvik stores the token locally using **Windows Credential Manager**.

---

# 7. Generate Your Discord Bot Installation Link

Your bot needs to be installed on the Discord server where you want to use Zelvik.

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

It may appear offline until Zelvik is running. This is normal.

---

# 8. First Launch

Run:

```text
Zelvik.exe
```

On the first launch, Zelvik will ask for your Discord bot token.

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

Zelvik stores the token securely using Windows Credential Manager.

On future launches, Zelvik will retrieve the saved token automatically.

---

# 9. Changing Your Discord Token

If you:

- Reset your Discord bot token
- Entered the wrong token
- Want to use another bot

click:

```text
Change Discord Token
```

inside Zelvik.

Enter the replacement token and save it.

Restart Zelvik after changing the token.

The new bot token will be used on the next launch.

---

# 10. Connect Zelvik to Discord

After Zelvik connects to Discord, select your:

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

Zelvik remembers the selected server and voice channel for future sessions.

---

# 11. Configure External Application Audio

Zelvik can automatically route audio from a Windows application such as RPG Soundboard into VB-Audio Virtual Cable.

You do not normally need to change the application's output device manually in Windows.

First, launch the soundboard or other audio application you want to use.

Some applications may need to play audio at least once before Windows creates an audio session that Zelvik can detect.

## Select the Application

In Zelvik, locate:

```text
Windows Audio Routing
```

Under:

```text
Application
```

select the application you want to capture.

For example:

```text
rpgsoundboard.exe
```

## Select the Output Device

Select the VB-Audio playback endpoint that should receive the application's audio.

For example:

```text
CABLE Input (VB-Audio Virtual Cable)
```

or another installed VB-Audio cable.

The exact device name may vary depending on your VB-Audio installation and audio driver configuration.

## Enable Routing

Click:

```text
Enable Routing
```

Zelvik configures Windows to send that application's audio to the selected virtual cable.

Zelvik then reads the Windows routing configuration back and verifies the route rather than simply assuming that the operation succeeded.

When the route is verified, the Audio Routed status indicator turns green.

## Configure External Audio Input

Under:

```text
External Audio Input
```

select the corresponding recording side of the virtual cable.

For example:

```text
CABLE Output
```

The device may include additional text depending on the Windows audio API.

For example:

```text
CABLE Output (VB-Audio Virtual Cable) [MME]
```

Click:

```text
Start Input
```

Audio sent by the selected application should now be transmitted through the Discord bot.

Use the External Audio Input volume slider to adjust the level.

---

# Disabling Windows Audio Routing

When you are finished using the external application, click:

```text
Disable Routing
```

Zelvik clears the per-application Windows audio override.

The application then returns to the normal Windows default output device.

This prevents a soundboard or other application from remaining silently routed into a virtual cable after Zelvik is no longer being used.

---

# Windows Sound Settings Fallback

Windows audio routing can occasionally behave differently between Windows versions, audio drivers, and applications.

Zelvik therefore provides:

```text
Open Windows Sound Settings
```

If automatic routing does not behave as expected, use this button to open the Windows application audio settings and configure the application's output manually.

Zelvik checks the actual Windows routing state and updates its status indicator when the expected route is detected.

---

# Zelvik Status

Zelvik provides live traffic-light status indicators for the major parts of the audio path:

```text
Discord Connected
Voice Channel Joined
Audio Routed
Audio Source Started
Good to Go
```

## Green

Green indicates that a required component is ready.

## Yellow

Yellow indicates that Zelvik is still waiting for that component or condition.

## Audio Routed

Windows application routing is required when using an external Windows application as the audio source.

When YouTube or local-file playback is active, the Audio Routed indicator reports:

```text
Not required for current source
```

because those sources are handled directly by Zelvik.

When no source is currently playing, Zelvik continues displaying the actual Windows routing state. This allows the external application route to be prepared and verified before playback begins.

## Audio Source Started

This indicator becomes green when Zelvik detects an active audio source such as:

- External application input
- YouTube playback
- Local audio playback

## Good to Go

Good to Go becomes green when:

- Discord is connected
- The bot has joined the selected voice channel
- An audio source is active
- Any requirements for that particular source have been satisfied

For example, Windows application routing is not required for YouTube playback.

---

# YouTube Playback

Zelvik can play audio from supported YouTube URLs.

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

Zelvik displays YouTube activity directly in the GUI so stream resolution, playback, retries, and failures can be observed without relying entirely on a console window.

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

# YouTube Authentication

Some YouTube videos require an authenticated YouTube session, including some age-restricted content.

Zelvik supports optional YouTube authentication using a Netscape-format `cookies.txt` file exported from a browser session in which you are already signed into YouTube.

Authentication is optional.

For ordinary public videos, authentication does not normally need to be enabled.

## Export Browser Cookies

Export the YouTube cookies from the browser profile in which you are signed into YouTube.

The file must use Netscape `cookies.txt` format.

For current information about using browser cookies with yt-dlp, see:

https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp

Because browser extensions and YouTube behavior change over time, consult the current yt-dlp documentation when choosing a cookie-export method.

## Import Cookies Into Zelvik

In Zelvik, click:

```text
Import cookies.txt
```

Select the exported file.

Zelvik copies the selected cookie file into its own application-data directory.

The GUI displays both:

```text
Original file
Managed copy
```

The managed copy means Zelvik does not depend on the original exported file remaining in your Downloads folder or another temporary location.

After a successful import, moving or deleting the original export does not change the location of Zelvik's managed copy.

## Protect Your Cookies

Browser cookies are authentication data.

Treat the exported and managed cookie files as sensitive.

Never:

- Commit them to GitHub
- Post them publicly
- Include them in screenshots
- Include them in bug reports
- Send them to another person

Zelvik's cookie files should remain excluded from source control.

## Check Authentication

Click:

```text
Check Authentication
```

to test whether the imported cookies are available for authenticated YouTube requests.

Zelvik displays the current authentication status in the GUI.

## Disable Authentication

Click:

```text
Disable Authentication
```

to return YouTube playback to the normal unauthenticated path.

This can also be useful for troubleshooting.

Some ordinary public videos may work more reliably without authenticated cookies, while restricted videos may require authentication.

Zelvik therefore allows authentication to be enabled only when needed.

---

# YouTube Reliability and Retries

YouTube's media delivery system can occasionally reject a resolved media request with an HTTP 403 response.

Zelvik includes retry handling for transient playback failures.

The YouTube Activity panel may display messages such as:

```text
YouTube: Starting...
YouTube: Resolving stream...
YouTube: 403 received — refreshing stream...
YouTube: Resolving stream...
YouTube: Playing — Example Video
```

A retry does not necessarily mean playback has failed.

Zelvik may discard the rejected media request, resolve the original YouTube URL again, and retry playback.

If all retries fail, Zelvik reports the failure in the GUI.

Because YouTube changes its delivery and anti-automation systems independently of Zelvik, not every YouTube URL can be guaranteed to work indefinitely.

---

# Local Audio Playback

Zelvik can also play audio files directly.

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

Local audio playback does not require Windows application routing.

---

# Master Volume

The Master Output volume controls the overall audio level being sent through Zelvik.

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

A typical external soundboard setup is:

```text
RPG Soundboard
      |
      | Zelvik Windows Routing
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
    Zelvik
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

and restart Zelvik.

---

## The Bot Is Offline in Discord

The bot only connects to Discord while Zelvik is running.

If Zelvik is closed, the bot appearing offline is normal.

---

## The Bot Connects but Does Not Join Voice

Verify that the bot has:

```text
View Channels
Connect
Speak
```

permissions for the selected voice channel.

Also verify that you selected the correct server and channel inside Zelvik.

---

## My Soundboard Does Not Appear in the Application List

Windows applications generally need an active audio session before they can be detected as audio applications.

Try:

1. Launch the soundboard.
2. Play a sound from it.
3. Return to Zelvik.
4. Click `Refresh Applications / Devices`.

The application should then appear if Windows exposes an audio session for it.

---

## Automatic Routing Does Not Work

Verify that:

- The external application is running
- The application has created an audio session
- The correct application is selected
- The correct VB-Audio output device is selected

Try playing audio from the application before enabling the route.

You can also click:

```text
Refresh Applications / Devices
```

If necessary, click:

```text
Open Windows Sound Settings
```

and inspect the application's output manually.

Zelvik verifies the Windows routing state after attempting to change it.

---

## Routing Is Enabled but Audio Is Not Reaching Discord

Remember that routing and capturing are separate parts of the audio path.

The application should be routed to:

```text
CABLE Input
```

Zelvik should listen to:

```text
CABLE Output
```

Then click:

```text
Start Input
```

Also verify that the Discord bot has joined the voice channel.

---

## CABLE Input / CABLE Output Do Not Appear

Reinstall VB-Audio Virtual Cable from:

https://vb-audio.com/Cable/index.htm

Run the installer as Administrator and reboot Windows afterward.

---

## YouTube Does Not Play

First verify FFmpeg:

```powershell
ffmpeg -version
```

Then verify Deno:

```powershell
deno --version
```

When running Zelvik from source, update yt-dlp and its default dependencies:

```powershell
python -m pip install --upgrade "yt-dlp[default]"
```

Zelvik displays YouTube activity directly in the GUI, including stream resolution, playback, retries, and failures.

YouTube may occasionally reject a media request with HTTP 403.

Zelvik automatically retries transient failures.

If a public video repeatedly fails while YouTube authentication is enabled, try:

```text
Disable Authentication
```

and play the video again.

If the video requires authentication, import a current `cookies.txt` file and enable authentication.

Because YouTube changes frequently, playback behavior may change independently of Zelvik.

---

## Authentication Is Available but a Public Video Does Not Play

Try disabling YouTube authentication.

Authenticated and unauthenticated YouTube requests can behave differently.

If the video does not require authentication, the normal unauthenticated playback path may work better.

---

## Authentication Does Not Work

Verify that:

- The cookie file was exported from a browser session signed into YouTube
- The cookies are still valid
- The file uses Netscape `cookies.txt` format
- Zelvik successfully created its managed copy

Try exporting a fresh cookie file and importing it again.

---

## Audio Is Too Quiet

Zelvik provides separate volume controls for:

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

Developers can run Zelvik directly from Python.

## Requirements

Recommended:

```text
Windows 10 or Windows 11
Python 3.11+
FFmpeg
Deno 2.0+
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

Run Zelvik:

```powershell
python main.py
```

---

# Developer Token Configuration

Developers running Zelvik from source use the same token setup as packaged EXE users.

On the first launch, Zelvik asks for the Discord bot token and stores it securely using **Windows Credential Manager**.

Run:

```powershell
python main.py
```

Enter the bot token when prompted and click:

```text
Save & Connect
```

On future launches, Zelvik retrieves the saved token automatically.

If the bot token is reset or you want to use a different bot, use:

```text
Change Discord Token
```

inside Zelvik, save the replacement token, and restart the application.

Never hard-code a Discord bot token into the source code or commit a working token to source control.

---

# Updating Dependencies

With the virtual environment activated:

```powershell
pip install --upgrade pip
```

To update yt-dlp and its standard dependencies:

```powershell
python -m pip install --upgrade "yt-dlp[default]"
```

To refresh the project's dependency list:

```powershell
pip freeze > requirements.txt
```

Review changes to `requirements.txt` before committing them.

---

# Building the Windows EXE

Zelvik can be packaged using PyInstaller.

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
pyinstaller --clean --onefile --name "Zelvik" main.py
```

The executable will be created at:

```text
dist\Zelvik.exe
```

Run it:

```powershell
.\dist\Zelvik.exe
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
- Windows application discovery
- Windows output-device discovery
- Automatic application routing
- Routing verification
- Disable Routing / restoration to Windows default
- Windows Sound Settings fallback
- External audio
- Zelvik Status indicators
- YouTube playback
- YouTube activity display
- YouTube retry behavior
- YouTube authentication import
- Managed cookie-file storage
- Authentication check
- Authentication disable
- Age-restricted YouTube playback where permitted
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
pyinstaller --clean --onefile --windowed --name "Zelvik" main.py
```

The finished executable will be:

```text
dist\Zelvik.exe
```

The `--onefile` option creates a single executable.

The `--windowed` option prevents the Python console window from appearing when the GUI starts.

The `--clean` option clears PyInstaller's build cache before creating the build.

---

# Testing the Release Build

Do not test the release EXE only from inside the source repository.

Copy it to a separate directory:

```powershell
New-Item C:\Temp\ZelvikTest -ItemType Directory -Force
Copy-Item .\dist\Zelvik.exe C:\Temp\ZelvikTest\
Set-Location C:\Temp\ZelvikTest
.\Zelvik.exe
```

This helps identify dependencies that may accidentally be available only because the EXE was launched from the development directory.

A clean-machine test is strongly recommended before publishing a release.

Windows 10 and Windows 11 should both be tested before a release when possible because the Windows audio-settings interface and routing behavior differ between versions.

---

# Project Philosophy

Zelvik is intended to solve a simple problem:

> Get soundboard audio, music, ambience, and sound effects into Discord without forcing everything through the user's microphone or requiring a complicated audio-mixing setup.

VB-Audio Virtual Cable provides the bridge for external applications.

Zelvik handles:

- Windows application routing
- External audio capture
- Discord connectivity
- YouTube
- Local audio
- Audio mixing
- Volume control
- Playback status
- Routing verification

The goal is to keep the workflow simple enough that a GM can spend time running the game instead of fighting with audio-routing software.

---

# Security

Zelvik does not require your Discord account password.

It uses a Discord **bot token** belonging to a bot application you create.

For normal Windows installations, the token is stored using Windows Credential Manager.

Treat your bot token as a password.

If it is ever exposed:

1. Open the Discord Developer Portal.
2. Select your application.
3. Open the Bot section.
4. Reset the token.
5. Copy the replacement token.
6. Open Zelvik.
7. Click `Change Discord Token`.
8. Save the replacement token.
9. Restart Zelvik.

Never publish a working Discord bot token in GitHub.

## YouTube Cookie Security

Imported YouTube cookies are also authentication credentials.

Zelvik maintains its own managed copy so the original export does not need to remain in its original location.

Cookie files must never be committed to GitHub or distributed with Zelvik.

If you believe an exported cookie file has been exposed, invalidate the affected browser session through your Google account and export fresh cookies if authentication is still required.

---

# Third-Party Software

Zelvik uses or interoperates with several third-party projects.

## Discord

https://discord.com/developers/applications

Used for Discord bot applications and voice-channel connectivity.

## VB-Audio Virtual Cable

https://vb-audio.com/Cable/index.htm

Provides the virtual Windows audio connection used to route external soundboard/application audio into Zelvik.

VB-CABLE is developed by VB-Audio Software.

## FFmpeg

https://ffmpeg.org/

Used for audio processing.

## yt-dlp

https://github.com/yt-dlp/yt-dlp

Used for resolving supported online media sources.

## Deno

https://deno.com/

Provides the JavaScript runtime used by yt-dlp for current YouTube extraction requirements.

## PySide6

https://doc.qt.io/qtforpython-6/

Used for the Windows graphical interface.

## PyInstaller

https://pyinstaller.org/

Used to package Zelvik as a Windows executable.

## winappaudiorouter

Used by Zelvik to interact with Windows per-application audio routing.

---

# Disclaimer

Zelvik is an independent project and is not affiliated with or endorsed by Discord, VB-Audio, FFmpeg, YouTube, Google, Deno, yt-dlp, Microsoft, or the developers of any third-party soundboard software.

Users are responsible for complying with the terms of service, copyright rules, licenses, and laws applicable to the media and services they use with Zelvik.

YouTube authentication support is intended to allow users to access content through their own authenticated sessions where they are otherwise authorized to access that content.

Zelvik does not grant rights to copyrighted audio or video content and does not circumvent DRM.