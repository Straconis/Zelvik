using System.Diagnostics;
using System.Text;
using NAudio.Wave;

namespace Zelvik.Audio;

public sealed class FfmpegAudioSource :
    IAsyncDisposable
{
    private readonly string _ffmpegPath;

    private Process? _process;
    private BufferedWaveProvider? _buffer;

    private CancellationTokenSource? _pumpCancellation;
    private Task? _outputPumpTask;
    private Task? _stderrPumpTask;
    private Task? _completionTask;

    private readonly StringBuilder _stderrBuffer =
        new();

    private readonly object _stderrLock =
        new();

    private bool _stopping;
    private bool _receivedAudio;

    public WaveFormat WaveFormat { get; } =
        new(
            rate: 48000,
            bits: 16,
            channels: 2);

    public bool IsRunning =>
        _process is not null
        && !_process.HasExited;

    public bool ReceivedAudio =>
        _receivedAudio;

    public int? LastExitCode { get; private set; }

    public string LastError
    {
        get
        {
            lock (_stderrLock)
            {
                return _stderrBuffer.ToString();
            }
        }
    }

    public ISampleProvider? SampleProvider =>
        _buffer?.ToSampleProvider();

    public event EventHandler? AudioReceived;
    public event EventHandler? PlaybackEnded;

    public FfmpegAudioSource(
        string? ffmpegPath = null)
    {
        _ffmpegPath =
            string.IsNullOrWhiteSpace(ffmpegPath)
                ? "ffmpeg"
                : ffmpegPath;
    }

    public async Task StartFromFileAsync(
        string mediaFilePath,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(mediaFilePath))
        {
            throw new ArgumentException(
                "A media file path is required.",
                nameof(mediaFilePath));
        }

        if (!File.Exists(mediaFilePath))
        {
            throw new FileNotFoundException(
                "The media file does not exist.",
                mediaFilePath);
        }

        await StopAsync();

        _stopping = false;
        _receivedAudio = false;
        LastExitCode = null;

        lock (_stderrLock)
        {
            _stderrBuffer.Clear();
        }

        var buffer =
            new BufferedWaveProvider(
                WaveFormat)
            {
                DiscardOnBufferOverflow = true,
                ReadFully = true
            };

        var startInfo =
            new ProcessStartInfo
            {
                FileName = _ffmpegPath,

                UseShellExecute = false,

                RedirectStandardOutput = true,
                RedirectStandardError = true,

                CreateNoWindow = true
            };

        startInfo.ArgumentList.Add(
            "-hide_banner");

        startInfo.ArgumentList.Add(
            "-loglevel");

        startInfo.ArgumentList.Add(
            "warning");

        startInfo.ArgumentList.Add(
            "-nostdin");

        /*
         * IMPORTANT:
         *
         * FFmpeg normally decodes a local file as quickly
         * as the CPU can process it.
         *
         * Zelvik needs a real-time PCM source instead.
         *
         * -re tells FFmpeg to read the input at its native
         * playback rate rather than racing through the file.
         */
        startInfo.ArgumentList.Add(
            "-re");

        startInfo.ArgumentList.Add(
            "-i");

        startInfo.ArgumentList.Add(
            mediaFilePath);

        startInfo.ArgumentList.Add(
            "-vn");

        /*
         * Zelvik mixer format:
         *
         * signed 16-bit PCM
         * 48 kHz
         * stereo
         */
        startInfo.ArgumentList.Add(
            "-f");

        startInfo.ArgumentList.Add(
            "s16le");

        startInfo.ArgumentList.Add(
            "-acodec");

        startInfo.ArgumentList.Add(
            "pcm_s16le");

        startInfo.ArgumentList.Add(
            "-ac");

        startInfo.ArgumentList.Add(
            "2");

        startInfo.ArgumentList.Add(
            "-ar");

        startInfo.ArgumentList.Add(
            "48000");

        startInfo.ArgumentList.Add(
            "pipe:1");

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

        var process =
            new Process
            {
                StartInfo = startInfo,
                EnableRaisingEvents = false
            };

        try
        {
            if (!process.Start())
            {
                throw new InvalidOperationException(
                    "FFmpeg could not be started.");
            }

            _buffer =
                buffer;

            _process =
                process;

            _pumpCancellation =
                CancellationTokenSource
                    .CreateLinkedTokenSource(
                        cancellationToken);

            CancellationToken pumpToken =
                _pumpCancellation.Token;

            _outputPumpTask =
                PumpAudioAsync(
                    process.StandardOutput.BaseStream,
                    buffer,
                    pumpToken);

            _stderrPumpTask =
                PumpStandardErrorAsync(
                    process.StandardError,
                    pumpToken);

            _completionTask =
                MonitorProcessAsync(
                    process,
                    _outputPumpTask,
                    _stderrPumpTask);
        }
        catch
        {
            process.Dispose();

            _process = null;
            _buffer = null;

            throw;
        }
    }

    private async Task PumpAudioAsync(
        Stream stream,
        BufferedWaveProvider buffer,
        CancellationToken cancellationToken)
    {
        byte[] readBuffer =
            new byte[32 * 1024];

        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                int bytesRead =
                    await stream.ReadAsync(
                        readBuffer,
                        cancellationToken);

                if (bytesRead == 0)
                    break;

                buffer.AddSamples(
                    readBuffer,
                    0,
                    bytesRead);

                if (!_receivedAudio)
                {
                    _receivedAudio = true;

                    AudioReceived?.Invoke(
                        this,
                        EventArgs.Empty);
                }
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (Exception ex)
        {
            AppendError(
                $"FFmpeg PCM pump error: {ex.Message}");
        }
    }

    private async Task PumpStandardErrorAsync(
        StreamReader reader,
        CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                string? line =
                    await reader.ReadLineAsync(
                        cancellationToken);

                if (line is null)
                    break;

                AppendError(
                    line);

                Debug.WriteLine(
                    $"[FFmpeg] {line}");
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (Exception ex)
        {
            AppendError(
                $"FFmpeg stderr pump error: {ex.Message}");
        }
    }

    private async Task MonitorProcessAsync(
        Process process,
        Task outputPump,
        Task stderrPump)
    {
        try
        {
            await process.WaitForExitAsync();

            LastExitCode =
                process.ExitCode;

            try
            {
                await outputPump;
            }
            catch
            {
            }

            try
            {
                await stderrPump;
            }
            catch
            {
            }

            if (!_stopping)
            {
                PlaybackEnded?.Invoke(
                    this,
                    EventArgs.Empty);
            }
        }
        catch (Exception ex)
        {
            AppendError(
                $"FFmpeg process monitor error: {ex.Message}");

            if (!_stopping)
            {
                PlaybackEnded?.Invoke(
                    this,
                    EventArgs.Empty);
            }
        }
    }

    private void AppendError(
        string message)
    {
        if (string.IsNullOrWhiteSpace(message))
            return;

        lock (_stderrLock)
        {
            if (_stderrBuffer.Length > 0)
            {
                _stderrBuffer.AppendLine();
            }

            _stderrBuffer.Append(
                message);
        }
    }

    public async Task StopAsync()
    {
        _stopping = true;

        Process? process =
            _process;

        _process = null;

        CancellationTokenSource? cancellation =
            _pumpCancellation;

        _pumpCancellation = null;

        Task? completionTask =
            _completionTask;

        _completionTask = null;
        _outputPumpTask = null;
        _stderrPumpTask = null;

        _buffer = null;

        try
        {
            cancellation?.Cancel();
        }
        catch
        {
        }

        if (process is not null)
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
        }

        if (completionTask is not null)
        {
            try
            {
                await completionTask;
            }
            catch
            {
            }
        }

        cancellation?.Dispose();
        process?.Dispose();
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
    }
}