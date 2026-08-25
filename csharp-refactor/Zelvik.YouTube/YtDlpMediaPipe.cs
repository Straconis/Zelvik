using System.Diagnostics;
using System.Text;

namespace Zelvik.YouTube;

public sealed class YtDlpMediaPipe :
    IAsyncDisposable
{
    private readonly string _ytDlpPath;

    private readonly StringBuilder _stderr =
        new();

    private readonly object _stderrLock =
        new();

    private Process? _process;
    private Task? _stderrTask;

    public bool IsRunning =>
        _process is not null
        && !_process.HasExited;

    public Stream? OutputStream =>
        _process?.StandardOutput.BaseStream;

    public int? LastExitCode { get; private set; }

    public string LastError
    {
        get
        {
            lock (_stderrLock)
            {
                return _stderr.ToString();
            }
        }
    }

    public YtDlpMediaPipe(
        string? ytDlpPath = null)
    {
        _ytDlpPath =
            string.IsNullOrWhiteSpace(
                ytDlpPath)
                ? "yt-dlp"
                : ytDlpPath;
    }

    public async Task StartAsync(
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

        await StopAsync();

        LastExitCode = null;

        lock (_stderrLock)
        {
            _stderr.Clear();
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
         * IMPORTANT:
         *
         * stdout must contain MEDIA BYTES ONLY.
         *
         * FFmpeg reads this stream directly. Any yt-dlp
         * status/progress text written to stdout will corrupt
         * the stream and cause:
         *
         *     Invalid data found when processing input
         */

        startInfo.ArgumentList.Add(
            "--quiet");

        startInfo.ArgumentList.Add(
            "--no-warnings");

        startInfo.ArgumentList.Add(
            "--no-progress");

        startInfo.ArgumentList.Add(
            "--no-playlist");

        /*
         * Force a real download even though the output is stdout.
         */
        startInfo.ArgumentList.Add(
            "--no-simulate");

        /*
         * Prefer one audio-only stream so FFmpeg receives one
         * continuous media container rather than a multi-format
         * merge operation.
         */
        startInfo.ArgumentList.Add(
            "-f");

        startInfo.ArgumentList.Add(
            "bestaudio[ext=webm]/bestaudio");

        /*
         * "-" means write downloaded media bytes to stdout.
         */
        startInfo.ArgumentList.Add(
            "-o");

        startInfo.ArgumentList.Add(
            "-");

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
         * Development workaround for the nearly-full C: drive.
         */
        string preferredTemp =
            @"D:\ZelvikTemp";

        string tempPath =
            Directory.Exists(
                preferredTemp)
                ? preferredTemp
                : Path.GetTempPath();

        startInfo.Environment["TEMP"] =
            tempPath;

        startInfo.Environment["TMP"] =
            tempPath;

        var process =
            new Process
            {
                StartInfo =
                    startInfo,

                EnableRaisingEvents =
                    false
            };

        try
        {
            if (!process.Start())
            {
                throw new InvalidOperationException(
                    "yt-dlp could not be started.");
            }

            _process =
                process;

            _stderrTask =
                CaptureStandardErrorAsync(
                    process,
                    cancellationToken);

            _ =
                MonitorProcessAsync(
                    process);
        }
        catch
        {
            process.Dispose();

            _process = null;

            throw;
        }
    }

    private async Task CaptureStandardErrorAsync(
        Process process,
        CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken
                       .IsCancellationRequested)
            {
                string? line =
                    await process.StandardError
                        .ReadLineAsync(
                            cancellationToken);

                if (line is null)
                    break;

                lock (_stderrLock)
                {
                    if (_stderr.Length > 0)
                    {
                        _stderr.AppendLine();
                    }

                    _stderr.Append(
                        line);
                }
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (Exception ex)
        {
            lock (_stderrLock)
            {
                if (_stderr.Length > 0)
                {
                    _stderr.AppendLine();
                }

                _stderr.Append(
                    $"yt-dlp stderr error: {ex.Message}");
            }
        }
    }

    private async Task MonitorProcessAsync(
        Process process)
    {
        try
        {
            await process.WaitForExitAsync();

            LastExitCode =
                process.ExitCode;
        }
        catch
        {
        }
    }

    public async Task StopAsync()
    {
        Process? process =
            _process;

        _process = null;

        Task? stderrTask =
            _stderrTask;

        _stderrTask = null;

        if (process is null)
            return;

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

        try
        {
            await process.WaitForExitAsync();
        }
        catch
        {
        }

        if (stderrTask is not null)
        {
            try
            {
                await stderrTask;
            }
            catch
            {
            }
        }

        try
        {
            LastExitCode =
                process.ExitCode;
        }
        catch
        {
        }

        process.Dispose();
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
    }
}