using System.ComponentModel;
using System.IO;
using System.Windows;
using Microsoft.Win32;
using Zelvik.Audio;

namespace Zelvik.App;

public partial class MainWindow : Window
{
    private const string Input1MixerId =
        "routed-input-1";

    private const string Input2MixerId =
        "external-input-2";

    private const string YouTubeMixerId =
        "youtube";

    private const string LocalMediaMixerId =
        "local-media";

    private static readonly TimeSpan ShutdownTimeout =
        TimeSpan.FromSeconds(2);

    private bool _loadingUi =
        true;

    private bool _shutdownInProgress;

    private bool _localMediaPlaying;

    private readonly AudioSessionService _audioSessionService =
        new();

    private readonly ProcessLoopbackCapture _input1Capture =
        new();

    private readonly ExternalInputCapture _input2Capture =
        new();

    private readonly AudioMixerService _audioMixer =
        new();

    private readonly LocalMonitorOutput _localMonitor =
        new();

    private readonly YouTubePlaybackService _youTubePlaybackService =
        new();

    private readonly LocalFileAudioSource _localFileAudioSource =
        new();

    public MainWindow()
    {
        InitializeComponent();

        LoadSettingsIntoUi();
        WireControls();

        _input1Capture.AudioReceived +=
            Input1Capture_AudioReceived;

        _audioMixer.OutputAudioReceived +=
            AudioMixer_OutputAudioReceived;

        _input2Capture.AudioReceived +=
            Input2Capture_AudioReceived;

        _youTubePlaybackService.AudioReceived +=
            YouTubePlaybackService_AudioReceived;

        _youTubePlaybackService.PlaybackEnded +=
            YouTubePlaybackService_PlaybackEnded;

        _loadingUi =
            false;

        Closing +=
            MainWindow_Closing;
    }

    private void WireControls()
    {
        StartInput1Button.Click +=
            StartInput1Button_Click;

        StopInput1Button.Click +=
            StopInput1Button_Click;

        StartInput2Button.Click +=
            StartInput2Button_Click;

        StopInput2Button.Click +=
            StopInput2Button_Click;

        PlayYouTubeButton.Click +=
            PlayYouTubeButton_Click;

        StopYouTubeButton.Click +=
            StopYouTubeButton_Click;

        SelectSoundButton.Click +=
            SelectSoundButton_Click;

        PlaySoundButton.Click +=
            PlaySoundButton_Click;

        StopLocalAudioButton.Click +=
            StopLocalAudioButton_Click;

        StopAllAudioButton.Click +=
            StopAllAudioButton_Click;
    }

    private void LoadSettingsIntoUi()
    {
        var settings =
            App.SettingsManager.Settings;

        Input1VolumeSlider.Value =
            settings.Audio.Aux1Volume * 100.0;

        Input2VolumeSlider.Value =
            settings.Audio.Aux2Volume * 100.0;

        MediaVolumeSlider.Value =
            settings.Audio.MediaVolume * 100.0;

        LocalMediaVolumeSlider.Value =
            settings.Audio.LocalMediaVolume * 100.0;

        VirtualInputVolumeSlider.Value =
            settings.Audio.VirtualInputVolume * 100.0;

        MasterVolumeSlider.Value =
            settings.Audio.MasterVolume * 100.0;

        _audioMixer.MasterVolume =
            settings.Audio.MasterVolume;

        App.ApplyTheme(
            settings.Ui.DarkMode);

        UpdateVolumeLabels();
    }

    // ------------------------------------------------------------
    // INPUT 1
    // ------------------------------------------------------------

    private async void StartInput1Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        var settings =
            App.SettingsManager.Settings.Audio;

        string processName =
            settings.RoutingApplication1;

        Input1StatusText.Text =
            "Input 1: Looking for audio session...";

        if (string.IsNullOrWhiteSpace(processName))
        {
            Input1StatusText.Text =
                "Input 1: No application configured";

            MessageBox.Show(
                "Select an application for Input 1 in Settings first.",
                "Input 1",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);

            return;
        }

        StartInput1Button.IsEnabled =
            false;

        try
        {
            var session =
                _audioSessionService.FindActiveSession(
                    processName);

            if (session is null)
            {
                throw new InvalidOperationException(
                    $"No active Windows audio session was found for '{processName}'. " +
                    "Make sure the application is running and has played audio, then refresh it in Settings.");
            }

            Input1StatusText.Text =
                $"Input 1: Session found - {session.ProcessName} (PID {session.ProcessId})";

            _audioMixer.RemoveInput(
                Input1MixerId);

            await _input1Capture.StopAsync();

            await _input1Capture.StartAsync(
                session.ProcessId);

            var sampleProvider =
                _input1Capture.SampleProvider
                ?? throw new InvalidOperationException(
                    "Input 1 process capture started but did not expose an audio stream.");

            _audioMixer.AddOrReplaceInput(
                Input1MixerId,
                sampleProvider,
                (float)(
                    Input1VolumeSlider.Value / 100.0));

            EnsureMonitorRunning();

            Input1StatusText.Text =
                $"Input 1: Capturing - {session.ProcessName} (PID {session.ProcessId})";
        }
        catch (Exception ex)
        {
            _audioMixer.RemoveInput(
                Input1MixerId);

            try
            {
                await _input1Capture.StopAsync();
            }
            catch
            {
            }

            StopMonitorIfIdle();

            Input1StatusText.Text =
                "Input 1: Failed";

            MessageBox.Show(
                ex.ToString(),
                "Input 1 Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        finally
        {
            StartInput1Button.IsEnabled =
                true;
        }
    }

    private async void StopInput1Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        await StopInput1Async();
    }

    private void Input1Capture_AudioReceived(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(() =>
        {
            string processName =
                App.SettingsManager.Settings.Audio.RoutingApplication1;

            Input1StatusText.Text =
                $"Input 1: Receiving audio - {processName}";
        });
    }

    private void AudioMixer_OutputAudioReceived(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(() =>
        {
            string processName =
                App.SettingsManager.Settings.Audio.RoutingApplication1;

            Input1StatusText.Text =
                $"Input 1: Mixer output active - {processName}";
        });
    }

    private async Task StopInput1Async()
    {
        _audioMixer.RemoveInput(
            Input1MixerId);

        await _input1Capture.StopAsync();

        Input1StatusText.Text =
            "Input 1: Stopped";

        StopMonitorIfIdle();
    }

    // ------------------------------------------------------------
    // INPUT 2
    // ------------------------------------------------------------

    private void StartInput2Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        var settings =
            App.SettingsManager.Settings.Audio;

        Input2StatusText.Text =
            "Input 2: Start requested";

        if (string.IsNullOrWhiteSpace(
                settings.Aux2Source))
        {
            Input2StatusText.Text =
                "Input 2: No device configured";

            MessageBox.Show(
                "Input 2 does not have a configured capture device.",
                "Input 2",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);

            return;
        }

        try
        {
            _audioMixer.RemoveInput(
                Input2MixerId);

            _input2Capture.Start(
                settings.Aux2Source);

            _audioMixer.AddOrReplaceInput(
                Input2MixerId,
                _input2Capture.GetSampleProvider(),
                (float)(
                    Input2VolumeSlider.Value / 100.0));

            EnsureMonitorRunning();

            Input2StatusText.Text =
                $"Input 2: Running - {_input2Capture.DeviceName}";
        }
        catch (Exception ex)
        {
            _audioMixer.RemoveInput(
                Input2MixerId);

            _input2Capture.Stop();

            StopMonitorIfIdle();

            Input2StatusText.Text =
                "Input 2: Failed";

            MessageBox.Show(
                ex.ToString(),
                "Input 2 Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void StopInput2Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        StopInput2();
    }

    private void Input2Capture_AudioReceived(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(() =>
        {
            Input2StatusText.Text =
                $"Input 2: Receiving audio - {_input2Capture.DeviceName}";
        });
    }

    private void StopInput2()
    {
        _audioMixer.RemoveInput(
            Input2MixerId);

        _input2Capture.Stop();

        Input2StatusText.Text =
            "Input 2: Stopped";

        StopMonitorIfIdle();
    }

    // ------------------------------------------------------------
    // YOUTUBE
    // ------------------------------------------------------------

    private async void PlayYouTubeButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        string videoUrl =
            YouTubeUrlTextBox.Text.Trim();

        if (string.IsNullOrWhiteSpace(videoUrl))
        {
            MessageBox.Show(
                "Enter a YouTube URL first.",
                "YouTube",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);

            return;
        }

        PlayYouTubeButton.IsEnabled =
            false;

        YouTubeStatusText.Text =
            "YouTube: Resolving stream...";

        YouTubeActivityTextBox.Text =
            $"Resolving:\n{videoUrl}";

        try
        {
            await StopYouTubeAsync();

            YouTubeStatusText.Text =
                "YouTube: Starting FFmpeg...";

            await _youTubePlaybackService.PlayAsync(
                videoUrl);

            var sampleProvider =
                _youTubePlaybackService.SampleProvider
                ?? throw new InvalidOperationException(
                    "YouTube playback started but FFmpeg did not expose an audio stream.");

            _audioMixer.AddOrReplaceInput(
                YouTubeMixerId,
                sampleProvider,
                (float)(
                    MediaVolumeSlider.Value / 100.0));

            EnsureMonitorRunning();

            YouTubeStatusText.Text =
                "YouTube: Playing";

            YouTubeActivityTextBox.Text +=
                "\n\nStream resolved successfully." +
                "\nFFmpeg started successfully." +
                "\nYouTube added to Zelvik mixer.";
        }
        catch (Exception ex)
        {
            _audioMixer.RemoveInput(
                YouTubeMixerId);

            try
            {
                await _youTubePlaybackService.StopAsync();
            }
            catch
            {
            }

            StopMonitorIfIdle();

            YouTubeStatusText.Text =
                "YouTube: Failed";

            YouTubeActivityTextBox.Text +=
                "\n\nERROR:\n" +
                ex;

            MessageBox.Show(
                ex.ToString(),
                "YouTube Playback Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        finally
        {
            PlayYouTubeButton.IsEnabled =
                true;
        }
    }

    private async void StopYouTubeButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        await StopYouTubeAsync();
    }

    private async Task StopYouTubeAsync()
    {
        _audioMixer.RemoveInput(
            YouTubeMixerId);

        await _youTubePlaybackService.StopAsync();

        YouTubeStatusText.Text =
            "YouTube: Stopped";

        StopMonitorIfIdle();
    }

    private void YouTubePlaybackService_AudioReceived(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(() =>
        {
            YouTubeStatusText.Text =
                "YouTube: Receiving decoded audio";

            YouTubeActivityTextBox.Text +=
                "\nFFmpeg audio received.";
        });
    }

    private void YouTubePlaybackService_PlaybackEnded(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(() =>
        {
            _audioMixer.RemoveInput(
                YouTubeMixerId);

            bool receivedAudio =
                _youTubePlaybackService.ReceivedAudio;

            int? exitCode =
                _youTubePlaybackService.LastFfmpegExitCode;

            string error =
                _youTubePlaybackService.LastFfmpegError;

            if (!receivedAudio)
            {
                YouTubeStatusText.Text =
                    "YouTube: FFmpeg failed";

                YouTubeActivityTextBox.Text +=
                    "\n\nFFmpeg exited before producing audio." +
                    $"\nExit code: {exitCode?.ToString() ?? "unknown"}";

                if (!string.IsNullOrWhiteSpace(error))
                {
                    YouTubeActivityTextBox.Text +=
                        "\n\nFFmpeg output:\n" +
                        error;
                }
            }
            else
            {
                YouTubeStatusText.Text =
                    "YouTube: Playback ended";

                YouTubeActivityTextBox.Text +=
                    "\nPlayback ended.";
            }

            StopMonitorIfIdle();
        });
    }

    // ------------------------------------------------------------
    // LOCAL FILE PLAYBACK
    // ------------------------------------------------------------

    private void SelectSoundButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        var dialog =
            new OpenFileDialog
            {
                Title =
                    "Select Audio File",

                Filter =
                    "Audio Files|*.mp3;*.wav;*.wma;*.aac;*.m4a|" +
                    "MP3 Files|*.mp3|" +
                    "Wave Files|*.wav|" +
                    "Windows Media Audio|*.wma|" +
                    "AAC / M4A Files|*.aac;*.m4a|" +
                    "All Files|*.*",

                CheckFileExists =
                    true,

                Multiselect =
                    false
            };

        if (dialog.ShowDialog(this) != true)
        {
            return;
        }

        try
        {
            _audioMixer.RemoveInput(
                LocalMediaMixerId);

            _localMediaPlaying =
                false;

            _localFileAudioSource.Load(
                dialog.FileName);

            LocalFileNameText.Text =
                Path.GetFileName(
                    dialog.FileName);

            LocalMediaStatusText.Text =
                "Local Audio: Ready";

            StopMonitorIfIdle();
        }
        catch (Exception ex)
        {
            _audioMixer.RemoveInput(
                LocalMediaMixerId);

            _localMediaPlaying =
                false;

            LocalFileNameText.Text =
                "No sound selected";

            LocalMediaStatusText.Text =
                "Local Audio: Failed";

            StopMonitorIfIdle();

            MessageBox.Show(
                ex.ToString(),
                "Local Audio Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void PlaySoundButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            if (!_localFileAudioSource.IsLoaded)
            {
                MessageBox.Show(
                    "Select a sound file first.",
                    "Local Audio",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);

                return;
            }

            _audioMixer.RemoveInput(
                LocalMediaMixerId);

            _localMediaPlaying =
                false;

            _localFileAudioSource.Restart();

            var sampleProvider =
                _localFileAudioSource.SampleProvider
                ?? throw new InvalidOperationException(
                    "The local audio file did not expose an audio stream.");

            _audioMixer.AddOrReplaceInput(
                LocalMediaMixerId,
                sampleProvider,
                (float)(
                    LocalMediaVolumeSlider.Value / 100.0));

            _localMediaPlaying =
                true;

            EnsureMonitorRunning();

            LocalMediaStatusText.Text =
                "Local Audio: Playing";
        }
        catch (Exception ex)
        {
            _audioMixer.RemoveInput(
                LocalMediaMixerId);

            _localMediaPlaying =
                false;

            StopMonitorIfIdle();

            LocalMediaStatusText.Text =
                "Local Audio: Failed";

            MessageBox.Show(
                ex.ToString(),
                "Local Audio Playback Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void StopLocalAudioButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        StopLocalAudio();
    }

    private void StopLocalAudio()
    {
        _audioMixer.RemoveInput(
            LocalMediaMixerId);

        _localMediaPlaying =
            false;

        _localFileAudioSource.Stop();

        LocalMediaStatusText.Text =
            "Local Audio: Stopped";

        StopMonitorIfIdle();
    }

    // ------------------------------------------------------------
    // MONITOR
    // ------------------------------------------------------------

    private void EnsureMonitorRunning()
    {
        var settings =
            App.SettingsManager.Settings.Audio;

        if (!settings.MonitorEnabled)
            return;

        if (_localMonitor.IsRunning)
            return;

        _localMonitor.Start(
            _audioMixer.GetMixedOutput(),
            settings.MonitorDevice);
    }

    private void StopMonitorIfIdle()
    {
        if (_input1Capture.IsRunning)
            return;

        if (_input2Capture.IsRunning)
            return;

        if (_youTubePlaybackService.IsPlaying)
            return;

        if (_localMediaPlaying)
            return;

        _localMonitor.Stop();
    }

    // ------------------------------------------------------------
    // STOP ALL
    // ------------------------------------------------------------

    private async void StopAllAudioButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            await StopInput1Async();
        }
        catch
        {
        }

        try
        {
            StopInput2();
        }
        catch
        {
        }

        try
        {
            await StopYouTubeAsync();
        }
        catch
        {
        }

        try
        {
            StopLocalAudio();
        }
        catch
        {
        }

        _localMonitor.Stop();

        LocalMediaStatusText.Text =
            "Local Audio: Stopped";
    }

    // ------------------------------------------------------------
    // VOLUME
    // ------------------------------------------------------------

    private void VolumeSlider_ValueChanged(
        object sender,
        RoutedPropertyChangedEventArgs<double> e)
    {
        if (_loadingUi)
            return;

        UpdateVolumeLabels();
        UpdateMixerVolumes();
    }

    private void UpdateMixerVolumes()
    {
        _audioMixer.SetInputVolume(
            Input1MixerId,
            (float)(
                Input1VolumeSlider.Value / 100.0));

        _audioMixer.SetInputVolume(
            Input2MixerId,
            (float)(
                Input2VolumeSlider.Value / 100.0));

        _audioMixer.SetInputVolume(
            YouTubeMixerId,
            (float)(
                MediaVolumeSlider.Value / 100.0));

        _audioMixer.SetInputVolume(
            LocalMediaMixerId,
            (float)(
                LocalMediaVolumeSlider.Value / 100.0));

        _audioMixer.MasterVolume =
            (float)(
                MasterVolumeSlider.Value / 100.0);
    }

    private void UpdateVolumeLabels()
    {
        if (Input1VolumeLabel is null)
            return;

        Input1VolumeLabel.Text =
            $"Input 1 Volume: {(int)Input1VolumeSlider.Value}%";

        Input2VolumeLabel.Text =
            $"Input 2 Volume: {(int)Input2VolumeSlider.Value}%";

        YouTubeVolumeLabel.Text =
            $"Volume: {(int)MediaVolumeSlider.Value}%";

        LocalMediaVolumeLabel.Text =
            $"Volume: {(int)LocalMediaVolumeSlider.Value}%";

        VirtualInputVolumeLabel.Text =
            $"Volume: {(int)VirtualInputVolumeSlider.Value}%";

        MasterVolumeLabel.Text =
            $"Master: {(int)MasterVolumeSlider.Value}%";
    }

    // ------------------------------------------------------------
    // SETTINGS / EXIT
    // ------------------------------------------------------------

    private void SettingsButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_shutdownInProgress)
            return;

        var settingsWindow =
            new SettingsWindow
            {
                Owner =
                    this
            };

        settingsWindow.ShowDialog();
    }

    private void ExitButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        Close();
    }

    // ------------------------------------------------------------
    // SHUTDOWN
    // ------------------------------------------------------------

    private async void MainWindow_Closing(
        object? sender,
        CancelEventArgs e)
    {
        if (_shutdownInProgress)
            return;

        e.Cancel =
            true;

        _shutdownInProgress =
            true;

        IsEnabled =
            false;

        try
        {
            try
            {
                _audioMixer.RemoveInput(
                    Input1MixerId);
            }
            catch
            {
            }

            try
            {
                _audioMixer.RemoveInput(
                    Input2MixerId);
            }
            catch
            {
            }

            try
            {
                _audioMixer.RemoveInput(
                    YouTubeMixerId);
            }
            catch
            {
            }

            try
            {
                _audioMixer.RemoveInput(
                    LocalMediaMixerId);

                _localMediaPlaying =
                    false;
            }
            catch
            {
            }

            try
            {
                _localMonitor.Stop();
            }
            catch
            {
            }

            try
            {
                _input2Capture.Stop();
            }
            catch
            {
            }

            try
            {
                Task stopTask =
                    _input1Capture.StopAsync();

                Task completedTask =
                    await Task.WhenAny(
                        stopTask,
                        Task.Delay(
                            ShutdownTimeout));

                if (completedTask == stopTask)
                {
                    await stopTask;
                }
            }
            catch
            {
            }

            try
            {
                Task stopYouTubeTask =
                    _youTubePlaybackService.StopAsync();

                Task completedTask =
                    await Task.WhenAny(
                        stopYouTubeTask,
                        Task.Delay(
                            ShutdownTimeout));

                if (completedTask == stopYouTubeTask)
                {
                    await stopYouTubeTask;
                }
            }
            catch
            {
            }

            try
            {
                SaveCurrentSettings();
            }
            catch
            {
            }

            try
            {
                _input2Capture.Dispose();
            }
            catch
            {
            }

            try
            {
                _localFileAudioSource.Dispose();
            }
            catch
            {
            }

            try
            {
                await _youTubePlaybackService.DisposeAsync();
            }
            catch
            {
            }

            try
            {
                _localMonitor.Dispose();
            }
            catch
            {
            }

            try
            {
                _audioMixer.Dispose();
            }
            catch
            {
            }
        }
        finally
        {
            Closing -=
                MainWindow_Closing;

            Close();
        }
    }

    private void SaveCurrentSettings()
    {
        var settings =
            App.SettingsManager.Settings;

        settings.Audio.Aux1Volume =
            (float)(
                Input1VolumeSlider.Value / 100.0);

        settings.Audio.Aux2Volume =
            (float)(
                Input2VolumeSlider.Value / 100.0);

        settings.Audio.MediaVolume =
            (float)(
                MediaVolumeSlider.Value / 100.0);

        settings.Audio.LocalMediaVolume =
            (float)(
                LocalMediaVolumeSlider.Value / 100.0);

        settings.Audio.VirtualInputVolume =
            (float)(
                VirtualInputVolumeSlider.Value / 100.0);

        settings.Audio.MasterVolume =
            (float)(
                MasterVolumeSlider.Value / 100.0);

        App.SettingsManager.Save();
    }
}