using NAudio.Wave;

namespace Zelvik.Audio;

public sealed class AudioMixerPump :
    IAsyncDisposable
{
    private readonly object _outputLock =
        new();

    private readonly ISampleProvider _source;

    private readonly Dictionary<string, BufferedWaveProvider>
        _outputs =
            new(StringComparer.OrdinalIgnoreCase);

    private CancellationTokenSource? _cancellation;
    private Task? _pumpTask;

    public bool IsRunning =>
        _pumpTask is not null
        && !_pumpTask.IsCompleted;

    public AudioMixerPump(
        ISampleProvider source)
    {
        _source =
            source
            ?? throw new ArgumentNullException(
                nameof(source));
    }

    public void Start()
    {
        if (IsRunning)
            return;

        _cancellation =
            new CancellationTokenSource();

        _pumpTask =
            Task.Run(
                () =>
                    PumpAsync(
                        _cancellation.Token));
    }

    public ISampleProvider AddOrReplaceOutput(
        string outputId)
    {
        if (string.IsNullOrWhiteSpace(
                outputId))
        {
            throw new ArgumentException(
                "An output ID is required.",
                nameof(outputId));
        }

        var buffer =
            new BufferedWaveProvider(
                _source.WaveFormat)
            {
                DiscardOnBufferOverflow =
                    true,

                ReadFully =
                    true
            };

        lock (_outputLock)
        {
            _outputs[outputId] =
                buffer;
        }

        return buffer.ToSampleProvider();
    }

    public void RemoveOutput(
        string outputId)
    {
        lock (_outputLock)
        {
            _outputs.Remove(
                outputId);
        }
    }

    private async Task PumpAsync(
        CancellationToken cancellationToken)
    {
        const int frameMilliseconds =
            20;

        int samplesPerFrame =
            _source.WaveFormat.SampleRate
            * _source.WaveFormat.Channels
            * frameMilliseconds
            / 1000;

        var samples =
            new float[samplesPerFrame];

        var bytes =
            new byte[
                samplesPerFrame
                * sizeof(float)];

        using var timer =
            new PeriodicTimer(
                TimeSpan.FromMilliseconds(
                    frameMilliseconds));

        try
        {
            while (await timer.WaitForNextTickAsync(
                       cancellationToken))
            {
                int samplesRead =
                    _source.Read(
                        samples.AsSpan());

                if (samplesRead <= 0)
                    continue;

                int byteCount =
                    samplesRead
                    * sizeof(float);

                Buffer.BlockCopy(
                    samples,
                    0,
                    bytes,
                    0,
                    byteCount);

                BufferedWaveProvider[] outputs;

                lock (_outputLock)
                {
                    outputs =
                        _outputs.Values.ToArray();
                }

                foreach (var output in outputs)
                {
                    try
                    {
                        output.AddSamples(
                            bytes,
                            0,
                            byteCount);
                    }
                    catch
                    {
                    }
                }
            }
        }
        catch (OperationCanceledException)
        {
        }
    }

    public async Task StopAsync()
    {
        var cancellation =
            _cancellation;

        var pumpTask =
            _pumpTask;

        _cancellation =
            null;

        _pumpTask =
            null;

        if (cancellation is null)
            return;

        try
        {
            cancellation.Cancel();

            if (pumpTask is not null)
            {
                await pumpTask;
            }
        }
        catch (OperationCanceledException)
        {
        }
        finally
        {
            cancellation.Dispose();
        }

        lock (_outputLock)
        {
            _outputs.Clear();
        }
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
    }
}
