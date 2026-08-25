using System.IO;
using NAudio.Wave;
using Zelvik.Audio;
using Zelvik.YouTube;

namespace Zelvik.App;

public sealed class YouTubePlaybackService :
    IAsyncDisposable
{
    /*
     * Match the retry behavior from the original
     * Python Zelvik implementation.
     *
     * This is the number of retries AFTER the
     * initial attempt.
     *
     * Total possible attempts:
     *
     *     initial + 3 retries = 4 attempts
     */
    private const int MaxDownloadRetries =
        3;

    private static readonly TimeSpan DownloadRetryDelay =
        TimeSpan.FromSeconds(1.5);

    private readonly YtDlpMediaFileService _mediaFileService;
    private readonly FfmpegAudioSource _ffmpegAudioSource;

    private string? _currentMediaFile;
    private bool _stopping;

    public bool IsPlaying =>
        _ffmpegAudioSource.IsRunning;

    public bool ReceivedAudio =>
        _ffmpegAudioSource.ReceivedAudio;

    public int? LastFfmpegExitCode =>
        _ffmpegAudioSource.LastExitCode;

    public string LastFfmpegError =>
        _ffmpegAudioSource.LastError;

    public string CurrentMediaFile =>
        _currentMediaFile
        ?? string.Empty;

    public ISampleProvider? SampleProvider =>
        _ffmpegAudioSource.SampleProvider;

    public event EventHandler? AudioReceived;

    public event EventHandler? PlaybackEnded;

    /*
     * Allows the UI to report:
     *
     *     YouTube: Download failed — retrying 1/3...
     *
     * We don't have to consume this event immediately,
     * but exposing it here keeps retry behavior in the
     * playback layer instead of coupling it to MainWindow.
     */
    public event EventHandler<YouTubeRetryEventArgs>?
        DownloadRetrying;

    public YouTubePlaybackService(
        string? ytDlpPath = null,
        string? ffmpegPath = null)
    {
        _mediaFileService =
            new YtDlpMediaFileService(
                ytDlpPath);

        _ffmpegAudioSource =
            new FfmpegAudioSource(
                ffmpegPath);

        _ffmpegAudioSource.AudioReceived +=
            FfmpegAudioSource_AudioReceived;

        _ffmpegAudioSource.PlaybackEnded +=
            FfmpegAudioSource_PlaybackEnded;
    }

    public async Task PlayAsync(
        string videoUrl,
        string? cookieFile = null,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(
                videoUrl))
        {
            throw new ArgumentException(
                "A YouTube URL is required.",
                nameof(videoUrl));
        }

        /*
         * Stop the previous FFmpeg process.
         *
         * StopAsync intentionally does NOT remove cached
         * media from disk.
         */
        await StopAsync();

        cancellationToken.ThrowIfCancellationRequested();

        _stopping =
            false;

        /*
         * Development authentication bridge.
         *
         * For now Zelvik can use the cookie file supplied by
         * ZELVIK_TEST_COOKIE_FILE.
         *
         * Later this can be replaced by automatic cookie
         * generation from Zelvik's WebView2 login session.
         */
        if (string.IsNullOrWhiteSpace(
                cookieFile))
        {
            string? configuredCookieFile =
                Environment.GetEnvironmentVariable(
                    "ZELVIK_TEST_COOKIE_FILE");

            if (!string.IsNullOrWhiteSpace(
                    configuredCookieFile)
                &&
                File.Exists(
                    configuredCookieFile))
            {
                cookieFile =
                    configuredCookieFile;
            }
        }

        /*
         * Cache lookup + resilient download.
         *
         * A cache hit should return successfully on the first
         * attempt without touching YouTube.
         *
         * A cache miss may encounter transient YouTube errors
         * such as HTTP 403. Those are retried using the same
         * strategy as the Python Zelvik implementation.
         */
        YtDlpMediaFileResult media =
            await DownloadWithRetryAsync(
                videoUrl,
                cookieFile,
                cancellationToken);

        if (!media.Success)
        {
            string authState =
                string.IsNullOrWhiteSpace(
                    cookieFile)
                    ? "No authenticated Zelvik cookie file was supplied."
                    : "Authenticated Zelvik cookies were supplied.";

            throw new InvalidOperationException(
                "yt-dlp could not prepare the YouTube audio.\n\n"
                + authState
                + "\n\n"
                + $"Exit code: {media.ExitCode}\n\n"
                + $"STDOUT:\n{media.StandardOutput}\n\n"
                + $"STDERR:\n{media.StandardError}");
        }

        _currentMediaFile =
            media.FilePath;

        try
        {
            await _ffmpegAudioSource.StartFromFileAsync(
                _currentMediaFile,
                cancellationToken);
        }
        catch
        {
            /*
             * Do NOT delete the cached media.
             *
             * Keeping failed media makes diagnostics possible
             * and avoids unnecessary redownloads.
             */
            throw;
        }
    }

    private async Task<YtDlpMediaFileResult>
        DownloadWithRetryAsync(
            string videoUrl,
            string? cookieFile,
            CancellationToken cancellationToken)
    {
        int retryCount =
            0;

        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();

            YtDlpMediaFileResult media =
                await _mediaFileService.DownloadAudioAsync(
                    videoUrl,
                    cookieFile,
                    cancellationToken);

            if (media.Success)
            {
                return media;
            }

            bool retryable =
                IsRetryableDownloadFailure(
                    media);

            if (!retryable
                ||
                retryCount >= MaxDownloadRetries)
            {
                return media;
            }

            retryCount++;

            DownloadRetrying?.Invoke(
                this,
                new YouTubeRetryEventArgs(
                    retryCount,
                    MaxDownloadRetries,
                    GetRetryReason(
                        media)));

            await Task.Delay(
                DownloadRetryDelay,
                cancellationToken);
        }
    }

    private static bool IsRetryableDownloadFailure(
        YtDlpMediaFileResult media)
    {
        string details =
            string.Join(
                "\n",
                media.StandardOutput
                    ?? string.Empty,
                media.StandardError
                    ?? string.Empty)
            .ToLowerInvariant();

        /*
         * Permanent/unavailable failures should not be
         * hammered repeatedly.
         */
        string[] permanentTerms =
        {
            "video unavailable",
            "this video is unavailable",
            "private video",
            "video is private",
            "removed by the uploader",
            "has been removed",
            "copyright",
            "this video is not available"
        };

        foreach (string term in permanentTerms)
        {
            if (details.Contains(
                    term,
                    StringComparison.Ordinal))
            {
                return false;
            }
        }

        /*
         * Authentication failures are not fixed by immediately
         * repeating the exact same request.
         *
         * If cookies have already been supplied, retrying a
         * genuine login-required response just wastes time.
         */
        string[] authenticationTerms =
        {
            "sign in to confirm",
            "login required",
            "log in to confirm",
            "authentication required",
            "confirm your age",
            "age-restricted",
            "age restricted"
        };

        foreach (string term in authenticationTerms)
        {
            if (details.Contains(
                    term,
                    StringComparison.Ordinal))
            {
                return false;
            }
        }

        /*
         * The important transient cases from Python Zelvik.
         */
        string[] retryableTerms =
        {
            "http error 403",
            "403 forbidden",
            "forbidden",
            "access denied",

            "requested format is not available",

            "http error 429",
            "too many requests",

            "http error 500",
            "http error 502",
            "http error 503",
            "http error 504",

            "timed out",
            "timeout",
            "connection reset",
            "connection refused",
            "temporary failure",
            "temporarily unavailable",
            "network is unreachable"
        };

        foreach (string term in retryableTerms)
        {
            if (details.Contains(
                    term,
                    StringComparison.Ordinal))
            {
                return true;
            }
        }

        /*
         * Unknown yt-dlp failures stay non-retryable.
         *
         * We don't want Zelvik blindly retrying malformed URLs,
         * unsupported sites, configuration errors, etc.
         */
        return false;
    }

    private static string GetRetryReason(
        YtDlpMediaFileResult media)
    {
        string details =
            string.Join(
                "\n",
                media.StandardOutput
                    ?? string.Empty,
                media.StandardError
                    ?? string.Empty)
            .ToLowerInvariant();

        if (details.Contains("403")
            ||
            details.Contains("forbidden")
            ||
            details.Contains("access denied"))
        {
            return "YouTube returned HTTP 403 Forbidden.";
        }

        if (details.Contains(
                "requested format is not available"))
        {
            return "The selected YouTube format was temporarily unavailable.";
        }

        if (details.Contains("429")
            ||
            details.Contains("too many requests"))
        {
            return "YouTube temporarily rate-limited the request.";
        }

        if (details.Contains("timeout")
            ||
            details.Contains("timed out"))
        {
            return "The YouTube request timed out.";
        }

        if (details.Contains(
                "connection reset"))
        {
            return "The network connection was reset.";
        }

        if (details.Contains(
                "temporarily unavailable"))
        {
            return "YouTube temporarily reported the media unavailable.";
        }

        return "A temporary YouTube download error occurred.";
    }

    public async Task StopAsync()
    {
        _stopping =
            true;

        /*
         * Stop playback only.
         *
         * The downloaded media remains cached.
         */
        await _ffmpegAudioSource.StopAsync();

        _currentMediaFile =
            null;
    }

    private void FfmpegAudioSource_AudioReceived(
        object? sender,
        EventArgs e)
    {
        AudioReceived?.Invoke(
            this,
            EventArgs.Empty);
    }

    private void FfmpegAudioSource_PlaybackEnded(
        object? sender,
        EventArgs e)
    {
        if (_stopping)
            return;

        /*
         * Natural end of playback.
         *
         * Do not delete the cached media.
         */
        _currentMediaFile =
            null;

        PlaybackEnded?.Invoke(
            this,
            EventArgs.Empty);
    }

    public static void ClearYouTubeCache()
    {
        YtDlpMediaFileService
            .ClearCache();
    }

    public static long GetYouTubeCacheSizeBytes()
    {
        return YtDlpMediaFileService
            .GetCacheSizeBytes();
    }

    public async ValueTask DisposeAsync()
    {
        _ffmpegAudioSource.AudioReceived -=
            FfmpegAudioSource_AudioReceived;

        _ffmpegAudioSource.PlaybackEnded -=
            FfmpegAudioSource_PlaybackEnded;

        await StopAsync();

        await _ffmpegAudioSource.DisposeAsync();

        /*
         * Intentionally do NOT clear the YouTube cache here.
         *
         * Closing Zelvik should not cause the next launch to
         * redownload everything.
         */
    }
}

public sealed class YouTubeRetryEventArgs :
    EventArgs
{
    public int RetryNumber { get; }

    public int MaximumRetries { get; }

    public string Reason { get; }

    public YouTubeRetryEventArgs(
        int retryNumber,
        int maximumRetries,
        string reason)
    {
        RetryNumber =
            retryNumber;

        MaximumRetries =
            maximumRetries;

        Reason =
            reason;
    }
}
