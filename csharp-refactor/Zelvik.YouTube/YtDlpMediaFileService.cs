using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;

namespace Zelvik.YouTube;

public sealed class YtDlpMediaFileResult
{
    public bool Success { get; init; }

    public bool WasCached { get; init; }

    public int ExitCode { get; init; }

    public string FilePath { get; init; } =
        string.Empty;

    public string StandardOutput { get; init; } =
        string.Empty;

    public string StandardError { get; init; } =
        string.Empty;
}

public sealed class YtDlpMediaFileService
{
    private readonly string _ytDlpPath;

    public YtDlpMediaFileService(
        string? ytDlpPath = null)
    {
        _ytDlpPath =
            string.IsNullOrWhiteSpace(ytDlpPath)
                ? "yt-dlp"
                : ytDlpPath;
    }

    public async Task<YtDlpMediaFileResult> DownloadAudioAsync(
        string videoUrl,
        string? cookieFile = null,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(videoUrl))
        {
            throw new ArgumentException(
                "A YouTube URL is required.",
                nameof(videoUrl));
        }

        string cacheDirectory =
            GetCacheDirectory();

        Directory.CreateDirectory(
            cacheDirectory);

        /*
         * For normal YouTube URLs this becomes the actual
         * YouTube video ID.
         *
         * Example:
         *
         *     BLbtr0Esl-Q
         *
         * Different URL forms for the same video therefore
         * resolve to the exact same cached media file.
         */
        string cacheKey =
            GetCacheKey(
                videoUrl);

        /*
         * CACHE HIT
         *
         * If we've successfully downloaded this video before,
         * reuse it instead of contacting YouTube again.
         */
        string? cachedFile =
            FindCompletedMediaFile(
                cacheDirectory,
                cacheKey);

        if (IsUsableMediaFile(
                cachedFile))
        {
            return new YtDlpMediaFileResult
            {
                Success = true,
                WasCached = true,
                ExitCode = 0,
                FilePath = cachedFile!,
                StandardOutput =
                    $"YouTube cache hit: {cachedFile}"
            };
        }

        /*
         * Remove abandoned partial files from an interrupted
         * download before trying again.
         */
        DeleteIncompleteFiles(
            cacheDirectory,
            cacheKey);

        /*
         * yt-dlp selects the extension.
         *
         * Examples:
         *
         *     BLbtr0Esl-Q.webm
         *     BLbtr0Esl-Q.m4a
         *     BLbtr0Esl-Q.mp4
         *
         * We deliberately do NOT force a container format.
         */
        string outputTemplate =
            Path.Combine(
                cacheDirectory,
                cacheKey + ".%(ext)s");

        var startInfo =
            new ProcessStartInfo
            {
                FileName =
                    _ytDlpPath,

                UseShellExecute =
                    false,

                RedirectStandardOutput =
                    true,

                RedirectStandardError =
                    true,

                CreateNoWindow =
                    true
            };

        startInfo.ArgumentList.Add(
            "--no-playlist");

        startInfo.ArgumentList.Add(
            "--no-progress");

        startInfo.ArgumentList.Add(
            "--no-warnings");

        /*
         * Prefer audio-only.
         *
         * "best" remains the fallback because YouTube may
         * sometimes expose only a combined HLS stream.
         *
         * FFmpeg handles either case afterward.
         */
        startInfo.ArgumentList.Add(
            "-f");

        startInfo.ArgumentList.Add(
            "bestaudio/best");

        startInfo.ArgumentList.Add(
            "-o");

        startInfo.ArgumentList.Add(
            outputTemplate);

        if (!string.IsNullOrWhiteSpace(
                cookieFile))
        {
            startInfo.ArgumentList.Add(
                "--cookies");

            startInfo.ArgumentList.Add(
                cookieFile);
        }

        startInfo.ArgumentList.Add(
            videoUrl);

        string tempRoot =
            GetZelvikTempRoot();

        startInfo.Environment["TEMP"] =
            tempRoot;

        startInfo.Environment["TMP"] =
            tempRoot;

        using var process =
            new Process
            {
                StartInfo =
                    startInfo
            };

        try
        {
            if (!process.Start())
            {
                return new YtDlpMediaFileResult
                {
                    Success = false,
                    WasCached = false,
                    ExitCode = -1,
                    StandardError =
                        "yt-dlp could not be started."
                };
            }
        }
        catch (Exception ex)
        {
            return new YtDlpMediaFileResult
            {
                Success = false,
                WasCached = false,
                ExitCode = -1,
                StandardError =
                    $"Failed to start yt-dlp: {ex.Message}"
            };
        }

        Task<string> stdoutTask =
            process.StandardOutput
                .ReadToEndAsync(
                    cancellationToken);

        Task<string> stderrTask =
            process.StandardError
                .ReadToEndAsync(
                    cancellationToken);

        try
        {
            await process.WaitForExitAsync(
                cancellationToken);
        }
        catch (OperationCanceledException)
        {
            try
            {
                if (!process.HasExited)
                {
                    process.Kill(
                        entireProcessTree: true);
                }
            }
            catch
            {
            }

            DeleteIncompleteFiles(
                cacheDirectory,
                cacheKey);

            throw;
        }

        string stdout =
            await stdoutTask;

        string stderr =
            await stderrTask;

        string? mediaFile =
            FindCompletedMediaFile(
                cacheDirectory,
                cacheKey);

        bool success =
            process.ExitCode == 0
            && IsUsableMediaFile(
                mediaFile);

        if (!success)
        {
            /*
             * Do not leave a corrupt "cached" file behind.
             */
            DeleteAllCacheFilesForKey(
                cacheDirectory,
                cacheKey);
        }

        return new YtDlpMediaFileResult
        {
            Success =
                success,

            WasCached =
                false,

            ExitCode =
                process.ExitCode,

            FilePath =
                success
                    ? mediaFile!
                    : string.Empty,

            StandardOutput =
                stdout,

            StandardError =
                stderr
        };
    }

    public static string GetCacheDirectory()
    {
        return Path.Combine(
            GetZelvikTempRoot(),
            "Zelvik",
            "YouTube",
            "Cache");
    }

    public static void ClearCache()
    {
        string cacheDirectory =
            GetCacheDirectory();

        if (!Directory.Exists(
                cacheDirectory))
        {
            return;
        }

        foreach (
            string file
            in Directory.EnumerateFiles(
                cacheDirectory,
                "*",
                SearchOption.TopDirectoryOnly))
        {
            try
            {
                File.Delete(
                    file);
            }
            catch
            {
                /*
                 * Best-effort cleanup.
                 *
                 * A file currently being played by FFmpeg
                 * may temporarily be locked.
                 */
            }
        }
    }

    public static long GetCacheSizeBytes()
    {
        string cacheDirectory =
            GetCacheDirectory();

        if (!Directory.Exists(
                cacheDirectory))
        {
            return 0;
        }

        long total =
            0;

        foreach (
            string file
            in Directory.EnumerateFiles(
                cacheDirectory,
                "*",
                SearchOption.TopDirectoryOnly))
        {
            try
            {
                total +=
                    new FileInfo(
                        file).Length;
            }
            catch
            {
            }
        }

        return total;
    }

    private static bool IsUsableMediaFile(
        string? filePath)
    {
        if (string.IsNullOrWhiteSpace(
                filePath))
        {
            return false;
        }

        try
        {
            if (!File.Exists(filePath))
            {
                return false;
            }

            return new FileInfo(
                       filePath)
                   .Length
                   > 1024;
        }
        catch
        {
            return false;
        }
    }

    private static string? FindCompletedMediaFile(
        string cacheDirectory,
        string cacheKey)
    {
        if (!Directory.Exists(
                cacheDirectory))
        {
            return null;
        }

        return Directory
            .EnumerateFiles(
                cacheDirectory,
                cacheKey + ".*",
                SearchOption.TopDirectoryOnly)
            .Where(
                path =>
                    !IsTemporaryYtDlpFile(
                        path))
            .Where(
                IsUsableMediaFile)
            .OrderByDescending(
                path =>
                {
                    try
                    {
                        return new FileInfo(
                            path).Length;
                    }
                    catch
                    {
                        return 0;
                    }
                })
            .FirstOrDefault();
    }

    private static bool IsTemporaryYtDlpFile(
        string filePath)
    {
        string extension =
            Path.GetExtension(
                filePath);

        if (extension.Equals(
                ".part",
                StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        if (extension.Equals(
                ".ytdl",
                StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        if (extension.Equals(
                ".temp",
                StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        string fileName =
            Path.GetFileName(
                filePath);

        if (fileName.Contains(
                ".temp.",
                StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return false;
    }

    private static void DeleteIncompleteFiles(
        string cacheDirectory,
        string cacheKey)
    {
        if (!Directory.Exists(
                cacheDirectory))
        {
            return;
        }

        foreach (
            string file
            in Directory.EnumerateFiles(
                cacheDirectory,
                cacheKey + ".*",
                SearchOption.TopDirectoryOnly))
        {
            if (!IsTemporaryYtDlpFile(file))
                continue;

            TryDelete(
                file);
        }
    }

    private static void DeleteAllCacheFilesForKey(
        string cacheDirectory,
        string cacheKey)
    {
        if (!Directory.Exists(
                cacheDirectory))
        {
            return;
        }

        foreach (
            string file
            in Directory.EnumerateFiles(
                cacheDirectory,
                cacheKey + ".*",
                SearchOption.TopDirectoryOnly))
        {
            TryDelete(
                file);
        }
    }

    private static void TryDelete(
        string filePath)
    {
        try
        {
            if (File.Exists(filePath))
            {
                File.Delete(
                    filePath);
            }
        }
        catch
        {
        }
    }

    private static string GetCacheKey(
        string videoUrl)
    {
        string? videoId =
            TryGetYouTubeVideoId(
                videoUrl);

        if (!string.IsNullOrWhiteSpace(
                videoId))
        {
            return videoId;
        }

        /*
         * Fallback for unusual URLs.
         *
         * Never use GetHashCode() for persistent cache keys
         * because its value is not intended to be stable
         * across processes/runtime versions.
         */
        byte[] urlBytes =
            Encoding.UTF8.GetBytes(
                videoUrl.Trim());

        byte[] hash =
            SHA256.HashData(
                urlBytes);

        return "url-"
            + Convert.ToHexString(hash)
                .ToLowerInvariant();
    }

    private static string? TryGetYouTubeVideoId(
        string videoUrl)
    {
        if (!Uri.TryCreate(
                videoUrl,
                UriKind.Absolute,
                out Uri? uri))
        {
            return null;
        }

        string host =
            uri.Host
                .ToLowerInvariant();

        /*
         * youtu.be/VIDEO_ID
         */
        if (host == "youtu.be"
            || host.EndsWith(
                ".youtu.be",
                StringComparison.Ordinal))
        {
            string id =
                uri.AbsolutePath
                    .Trim('/');

            return SanitizeVideoId(
                id);
        }

        bool youtubeHost =
            host == "youtube.com"
            || host == "www.youtube.com"
            || host == "m.youtube.com"
            || host.EndsWith(
                ".youtube.com",
                StringComparison.Ordinal);

        if (!youtubeHost)
        {
            return null;
        }

        string[] segments =
            uri.AbsolutePath
                .Split(
                    '/',
                    StringSplitOptions.RemoveEmptyEntries);

        /*
         * youtube.com/shorts/VIDEO_ID
         * youtube.com/embed/VIDEO_ID
         * youtube.com/live/VIDEO_ID
         */
        if (segments.Length >= 2)
        {
            if (segments[0].Equals(
                    "shorts",
                    StringComparison.OrdinalIgnoreCase)
                ||
                segments[0].Equals(
                    "embed",
                    StringComparison.OrdinalIgnoreCase)
                ||
                segments[0].Equals(
                    "live",
                    StringComparison.OrdinalIgnoreCase))
            {
                return SanitizeVideoId(
                    segments[1]);
            }
        }

        /*
         * youtube.com/watch?v=VIDEO_ID
         */
        if (uri.AbsolutePath.Equals(
                "/watch",
                StringComparison.OrdinalIgnoreCase))
        {
            string query =
                uri.Query.TrimStart('?');

            foreach (
                string item
                in query.Split(
                    '&',
                    StringSplitOptions.RemoveEmptyEntries))
            {
                string[] pair =
                    item.Split(
                        '=',
                        2);

                if (pair.Length != 2)
                    continue;

                if (!pair[0].Equals(
                        "v",
                        StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                return SanitizeVideoId(
                    Uri.UnescapeDataString(
                        pair[1]));
            }
        }

        return null;
    }

    private static string? SanitizeVideoId(
        string? videoId)
    {
        if (string.IsNullOrWhiteSpace(
                videoId))
        {
            return null;
        }

        string cleaned =
            new(
                videoId
                    .Where(
                        character =>
                            char.IsLetterOrDigit(
                                character)
                            || character == '-'
                            || character == '_')
                    .ToArray());

        if (string.IsNullOrWhiteSpace(
                cleaned))
        {
            return null;
        }

        return cleaned;
    }

    private static string GetZelvikTempRoot()
    {
        const string preferredTemp =
            @"D:\ZelvikTemp";

        if (Directory.Exists(
                preferredTemp))
        {
            return preferredTemp;
        }

        return Path.GetTempPath();
    }
}