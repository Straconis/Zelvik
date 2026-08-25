using System.IO;
using NAudio.Wave;
using Zelvik.Audio;
using Zelvik.YouTube;

namespace Zelvik.App;

public sealed class YouTubePlaybackService :
    IAsyncDisposable
{
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
         * IMPORTANT:
         *
         * StopAsync no longer deletes the media file.
         * It remains available in the YouTube cache.
         */
        await StopAsync();

        _stopping =
            false;

        /*
         * Development authentication bridge.
         *
         * Later this will be replaced by automatic cookie
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
         * DownloadAudioAsync now performs a cache lookup first.
         *
         * Cache hit:
         *
         *     returns immediately
         *
         * Cache miss:
         *
         *     downloads through yt-dlp and stores the result
         */
        YtDlpMediaFileResult media =
            await _mediaFileService.DownloadAudioAsync(
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
             * Do NOT delete the cached media here.
             *
             * If FFmpeg has a problem, keeping the file makes
             * diagnostics possible and prevents unnecessary
             * redownloads while debugging.
             */
            throw;
        }
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