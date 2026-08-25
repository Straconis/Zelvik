using System.Windows;
using Zelvik.YouTube;

namespace Zelvik.App;

public partial class MainWindow
{
    private readonly YouTubeQueueService _youTubeQueueService =
        new();

    private YouTubeQueueWindow? _youTubeQueueWindow;

    private bool _youTubeQueueIntegrationInitialized;

    private bool _queuePlaybackOwnsCurrentPlayback;

    private bool _queuePlaybackStarting;

    static MainWindow()
    {
        /*
         * MainWindow.xaml.cs is intentionally left untouched.
         *
         * This partial class hooks itself into the WPF Loaded
         * event and initializes the YouTube queue subsystem.
         */
        EventManager.RegisterClassHandler(
            typeof(MainWindow),
            FrameworkElement.LoadedEvent,
            new RoutedEventHandler(
                MainWindow_QueueLoaded));
    }

    private static void MainWindow_QueueLoaded(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not MainWindow window)
            return;

        window.InitializeYouTubeQueueIntegration();
    }

    private void InitializeYouTubeQueueIntegration()
    {
        if (_youTubeQueueIntegrationInitialized)
            return;

        _youTubeQueueIntegrationInitialized =
            true;

        QueueYouTubeButton.Click +=
            QueueYouTubeButton_Click;

        /*
         * Existing MainWindow playback handling remains intact.
         *
         * This second listener deals only with queue advancement.
         * YouTubePlaybackService suppresses PlaybackEnded when
         * StopAsync() is called manually, so this listener fires
         * only for natural FFmpeg completion.
         */
        _youTubePlaybackService.PlaybackEnded +=
            YouTubeQueuePlaybackService_PlaybackEnded;

        /*
         * Direct/manual Play is separate from queue-controlled
         * playback. If the user presses Play YouTube manually,
         * the queue should not claim ownership of that playback.
         */
        PlayYouTubeButton.Click +=
            ManualYouTubePlaybackRequested;

        StopYouTubeButton.Click +=
            ManualYouTubeStopRequested;
    }

    // ------------------------------------------------------------
    // MAIN WINDOW QUEUE BUTTON
    // ------------------------------------------------------------

    private void QueueYouTubeButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        string url =
            YouTubeUrlTextBox.Text.Trim();

        /*
         * If a URL is present, Queue means:
         *
         *     add this URL using the current YouTube volume
         *
         * If the URL box is blank, Queue simply opens the
         * queue window.
         */
        if (!string.IsNullOrWhiteSpace(url))
        {
            if (!LooksLikeYouTubeUrlForQueue(url))
            {
                MessageBox.Show(
                    this,
                    "That does not look like a YouTube URL.",
                    "YouTube Queue",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);

                return;
            }

            float volume =
                Math.Clamp(
                    (float)(
                        MediaVolumeSlider.Value / 100.0),
                    0.0f,
                    2.0f);

            _youTubeQueueService.Enqueue(
                url,
                volume: volume);

            YouTubeActivityTextBox.Text +=
                $"\nQueued: {url}";
        }

        OpenYouTubeQueueWindow();
    }

    private static bool LooksLikeYouTubeUrlForQueue(
        string value)
    {
        if (!Uri.TryCreate(
                value,
                UriKind.Absolute,
                out Uri? uri))
        {
            return false;
        }

        string host =
            uri.Host.ToLowerInvariant();

        return
            host == "youtube.com"
            || host == "www.youtube.com"
            || host == "m.youtube.com"
            || host == "youtu.be"
            || host.EndsWith(
                ".youtube.com",
                StringComparison.OrdinalIgnoreCase);
    }

    // ------------------------------------------------------------
    // QUEUE WINDOW
    // ------------------------------------------------------------

    private void OpenYouTubeQueueWindow()
    {
        if (_youTubeQueueWindow is not null)
        {
            if (_youTubeQueueWindow.WindowState
                == WindowState.Minimized)
            {
                _youTubeQueueWindow.WindowState =
                    WindowState.Normal;
            }

            _youTubeQueueWindow.Activate();

            return;
        }

        _youTubeQueueWindow =
            new YouTubeQueueWindow(
                _youTubeQueueService,
                () =>
                    Math.Clamp(
                        (float)(
                            MediaVolumeSlider.Value / 100.0),
                        0.0f,
                        2.0f))
            {
                Owner =
                    this
            };

        _youTubeQueueWindow.PlayResumeRequested +=
            YouTubeQueueWindow_PlayResumeRequested;

        _youTubeQueueWindow.PlayNextRequested +=
            YouTubeQueueWindow_PlayNextRequested;

        _youTubeQueueWindow.Closed +=
            YouTubeQueueWindow_Closed;

        _youTubeQueueWindow.Show();
    }

    private void YouTubeQueueWindow_Closed(
        object? sender,
        EventArgs e)
    {
        if (_youTubeQueueWindow is null)
            return;

        _youTubeQueueWindow.PlayResumeRequested -=
            YouTubeQueueWindow_PlayResumeRequested;

        _youTubeQueueWindow.PlayNextRequested -=
            YouTubeQueueWindow_PlayNextRequested;

        _youTubeQueueWindow.Closed -=
            YouTubeQueueWindow_Closed;

        _youTubeQueueWindow =
            null;
    }

    // ------------------------------------------------------------
    // PLAY / RESUME
    // ------------------------------------------------------------

    private async void YouTubeQueueWindow_PlayResumeRequested(
        object? sender,
        EventArgs e)
    {
        if (_queuePlaybackStarting)
            return;

        /*
         * If queue-owned playback is already running,
         * Play / Resume has nothing to do.
         */
        if (_queuePlaybackOwnsCurrentPlayback
            &&
            _youTubePlaybackService.IsPlaying)
        {
            return;
        }

        YouTubeQueueItem? item =
            _youTubeQueueService.CurrentItem;

        /*
         * No current item means take the next queued item.
         */
        if (item is null)
        {
            item =
                _youTubeQueueService.TakeNext();
        }

        if (item is null)
        {
            MessageBox.Show(
                this,
                "The YouTube queue is empty.",
                "YouTube Queue",
                MessageBoxButton.OK,
                MessageBoxImage.Information);

            return;
        }

        await PlayQueueItemAsync(
            item);
    }

    // ------------------------------------------------------------
    // PLAY NEXT
    // ------------------------------------------------------------

    private async void YouTubeQueueWindow_PlayNextRequested(
        object? sender,
        EventArgs e)
    {
        if (_queuePlaybackStarting)
            return;

        await PlayNextQueueItemAsync();
    }

    private async Task PlayNextQueueItemAsync()
    {
        /*
         * Explicit Play Next abandons the current queue item.
         */
        _queuePlaybackOwnsCurrentPlayback =
            false;

        _audioMixer.RemoveInput(
            YouTubeMixerId);

        try
        {
            await _youTubePlaybackService.StopAsync();
        }
        catch
        {
        }

        bool loopQueue =
            _youTubeQueueWindow?.LoopQueueEnabled
            == true;

        if (loopQueue)
        {
            _youTubeQueueService.RequeueCurrentAtBack();
        }
        else
        {
            _youTubeQueueService.CompleteCurrent();
        }

        YouTubeQueueItem? next =
            _youTubeQueueService.TakeNext();

        if (next is null)
        {
            YouTubeStatusText.Text =
                "YouTube: Queue finished";

            StopMonitorIfIdle();

            return;
        }

        await PlayQueueItemAsync(
            next);
    }

    // ------------------------------------------------------------
    // QUEUE PLAYBACK
    // ------------------------------------------------------------

    private async Task PlayQueueItemAsync(
        YouTubeQueueItem item)
    {
        if (_queuePlaybackStarting)
            return;

        _queuePlaybackStarting =
            true;

        try
        {
            /*
             * Stop whatever YouTube source is currently attached.
             *
             * This does not remove the cached media file.
             */
            _queuePlaybackOwnsCurrentPlayback =
                false;

            _audioMixer.RemoveInput(
                YouTubeMixerId);

            await _youTubePlaybackService.StopAsync();

            /*
             * Reflect the queued item's volume in the main UI.
             *
             * Queue items preserve the volume that was selected
             * when they were added. Values up to 2.0 represent
             * Zelvik's new 200% YouTube boost.
             */
            MediaVolumeSlider.Value =
                Math.Clamp(
                    item.Volume * 100.0,
                    MediaVolumeSlider.Minimum,
                    MediaVolumeSlider.Maximum);

            YouTubeUrlTextBox.Text =
                item.Url;

            YouTubeStatusText.Text =
                "YouTube: Loading queued item...";

            YouTubeActivityTextBox.Text +=
                $"\n\nQueue playing:\n{item.Url}";

            await _youTubePlaybackService.PlayAsync(
                item.Url);

            var sampleProvider =
                _youTubePlaybackService.SampleProvider
                ?? throw new InvalidOperationException(
                    "Queued YouTube playback started but FFmpeg did not expose an audio stream.");

            _audioMixer.AddOrReplaceInput(
                YouTubeMixerId,
                sampleProvider,
                item.Volume);

            _queuePlaybackOwnsCurrentPlayback =
                true;

            EnsureMonitorRunning();

            YouTubeStatusText.Text =
                "YouTube: Playing queued item";

            YouTubeActivityTextBox.Text +=
                "\nQueued item added to Zelvik mixer.";
        }
        catch (Exception ex)
        {
            _queuePlaybackOwnsCurrentPlayback =
                false;

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
                "YouTube: Queue item failed";

            YouTubeActivityTextBox.Text +=
                "\n\nQUEUE ERROR:\n"
                + ex;

            MessageBox.Show(
                this,
                ex.ToString(),
                "YouTube Queue Playback Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        finally
        {
            _queuePlaybackStarting =
                false;
        }
    }

    // ------------------------------------------------------------
    // AUTOMATIC ADVANCEMENT
    // ------------------------------------------------------------

    private void YouTubeQueuePlaybackService_PlaybackEnded(
        object? sender,
        EventArgs e)
    {
        /*
         * Ignore natural completion unless this playback was
         * actually started by the queue.
         *
         * This prevents normal Play YouTube usage from
         * accidentally consuming queued tracks.
         */
        if (!_queuePlaybackOwnsCurrentPlayback)
            return;

        _queuePlaybackOwnsCurrentPlayback =
            false;

        Dispatcher.BeginInvoke(
            new Action(
                async () =>
                {
                    await HandleQueuePlaybackEndedAsync();
                }));
    }

    private async Task HandleQueuePlaybackEndedAsync()
    {
        YouTubeQueueItem? completed =
            _youTubeQueueService.CurrentItem;

        if (completed is null)
            return;

        /*
         * Queue-level looping.
         *
         * The current queue item simply restarts. Because
         * YouTube media is cached, subsequent loops should
         * start almost immediately.
         */
        if (completed.Loop)
        {
            await PlayQueueItemAsync(
                completed);

            return;
        }

        bool loopQueue =
            _youTubeQueueWindow?.LoopQueueEnabled
            == true;

        if (loopQueue)
        {
            _youTubeQueueService.RequeueCurrentAtBack();
        }
        else
        {
            _youTubeQueueService.CompleteCurrent();
        }

        YouTubeQueueItem? next =
            _youTubeQueueService.TakeNext();

        if (next is null)
        {
            YouTubeStatusText.Text =
                "YouTube: Queue finished";

            YouTubeActivityTextBox.Text +=
                "\nQueue finished.";

            StopMonitorIfIdle();

            return;
        }

        YouTubeActivityTextBox.Text +=
            "\nAdvancing to next queued item.";

        await PlayQueueItemAsync(
            next);
    }

    // ------------------------------------------------------------
    // MANUAL PLAYBACK OWNERSHIP
    // ------------------------------------------------------------

    private void ManualYouTubePlaybackRequested(
        object sender,
        RoutedEventArgs e)
    {
        /*
         * The normal Play YouTube button is intentionally
         * independent of the queue.
         */
        _queuePlaybackOwnsCurrentPlayback =
            false;
    }

    private void ManualYouTubeStopRequested(
        object sender,
        RoutedEventArgs e)
    {
        /*
         * Stop pauses queue progression.
         *
         * CurrentItem remains assigned so Play / Resume in
         * the queue window can restart that item.
         */
        _queuePlaybackOwnsCurrentPlayback =
            false;
    }
}

