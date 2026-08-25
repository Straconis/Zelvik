using System.Diagnostics;

namespace Zelvik.YouTube;

public sealed class YtDlpResult
{
    public bool Success { get; init; }

    public int ExitCode { get; init; }

    public string StandardOutput { get; init; } =
        string.Empty;

    public string StandardError { get; init; } =
        string.Empty;

    public IReadOnlyList<string> StreamUrls { get; init; } =
        Array.Empty<string>();
}

public sealed class YtDlpMetadataResult
{
    public bool Success { get; init; }

    public int ExitCode { get; init; }

    public string Title { get; init; } =
        string.Empty;

    public string StandardError { get; init; } =
        string.Empty;
}
public sealed class YtDlpService
{
    private readonly string _ytDlpPath;

    public YtDlpService(
        string? ytDlpPath = null)
    {
        _ytDlpPath =
            string.IsNullOrWhiteSpace(ytDlpPath)
                ? "yt-dlp"
                : ytDlpPath;
    }

    public async Task<YtDlpResult> ResolveStreamAsync(
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

        /*
         * We want yt-dlp to resolve the actual media URL,
         * not download the file.
         *
         * -g / --get-url prints the resolved media URL.
         *
         * bestaudio/best keeps this useful for Zelvik's
         * audio playback path.
         */
        startInfo.ArgumentList.Add(
            "--no-playlist");

        startInfo.ArgumentList.Add(
            "--no-warnings");

        startInfo.ArgumentList.Add(
            "-f");

        startInfo.ArgumentList.Add(
            "bestaudio/best");

        startInfo.ArgumentList.Add(
            "-g");

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

        /*
         * Zelvik should control its own temporary working
         * directory rather than depending blindly on the
         * user's system TEMP.
         *
         * For now this uses D:\ZelvikTemp if it exists,
         * otherwise it falls back to the normal temp path.
         */
        string preferredTemp =
            @"D:\ZelvikTemp";

        string tempPath =
            Directory.Exists(preferredTemp)
                ? preferredTemp
                : Path.GetTempPath();

        startInfo.Environment["TEMP"] =
            tempPath;

        startInfo.Environment["TMP"] =
            tempPath;

        using var process =
            new Process
            {
                StartInfo =
                    startInfo,

                EnableRaisingEvents =
                    true
            };

        try
        {
            if (!process.Start())
            {
                throw new InvalidOperationException(
                    "yt-dlp could not be started.");
            }
        }
        catch (Exception ex)
        {
            return new YtDlpResult
            {
                Success =
                    false,

                ExitCode =
                    -1,

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

            throw;
        }

        string standardOutput =
            await stdoutTask;

        string standardError =
            await stderrTask;

        var streamUrls =
            standardOutput
                .Split(
                    new[]
                    {
                        '\r',
                        '\n'
                    },
                    StringSplitOptions
                        .RemoveEmptyEntries)
                .Select(
                    line =>
                        line.Trim())
                .Where(
                    line =>
                        Uri.TryCreate(
                            line,
                            UriKind.Absolute,
                            out _))
                .ToList();

        return new YtDlpResult
        {
            Success =
                process.ExitCode == 0
                &&
                streamUrls.Count > 0,

            ExitCode =
                process.ExitCode,

            StandardOutput =
                standardOutput,

            StandardError =
                standardError,

            StreamUrls =
                streamUrls
        };
    }
    public async Task<YtDlpMetadataResult> ResolveTitleAsync(
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
            "--no-warnings");

        startInfo.ArgumentList.Add(
            "--get-title");

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

        string preferredTemp =
            @"D:\ZelvikTemp";

        string tempPath =
            Directory.Exists(preferredTemp)
                ? preferredTemp
                : Path.GetTempPath();

        startInfo.Environment["TEMP"] =
            tempPath;

        startInfo.Environment["TMP"] =
            tempPath;

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
                throw new InvalidOperationException(
                    "yt-dlp could not be started.");
            }
        }
        catch (Exception ex)
        {
            return new YtDlpMetadataResult
            {
                Success =
                    false,

                ExitCode =
                    -1,

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

            throw;
        }

        string standardOutput =
            await stdoutTask;

        string standardError =
            await stderrTask;

        string title =
            standardOutput.Trim();

        return new YtDlpMetadataResult
        {
            Success =
                process.ExitCode == 0
                &&
                !string.IsNullOrWhiteSpace(
                    title),

            ExitCode =
                process.ExitCode,

            Title =
                title,

            StandardError =
                standardError
        };
    }
}

