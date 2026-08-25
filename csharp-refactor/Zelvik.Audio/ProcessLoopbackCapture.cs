using System.Runtime.InteropServices;
using NAudio.CoreAudioApi;
using NAudio.Wave;

namespace Zelvik.Audio;

public sealed class ProcessLoopbackCapture
    : IAsyncDisposable
{
    private const float SilenceThreshold = 0.001f;

    private WasapiRecorder? _recorder;
    private BufferedWaveProvider? _bufferedProvider;

    private bool _receivedNonSilentAudio;

    public bool IsRunning =>
        _recorder is not null;

    public bool HasReceivedAudio =>
        _receivedNonSilentAudio;

    public int ProcessId
    {
        get;
        private set;
    }

    public float LastPeak
    {
        get;
        private set;
    }

    public ISampleProvider? SampleProvider =>
        _bufferedProvider?.ToSampleProvider();

    public event EventHandler? AudioReceived;

    public async Task StartAsync(
        int processId)
    {
        if (processId <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(processId));
        }

        await StopAsync();

        var recorder =
            await new WasapiRecorderBuilder()
                .WithProcessLoopback(
                    (uint)processId,
                    ProcessLoopbackMode
                        .IncludeTargetProcessTree)
                .WithFormat(
                    WaveFormat
                        .CreateIeeeFloatWaveFormat(
                            48000,
                            2))
                .BuildAsync();

        var bufferedProvider =
            new BufferedWaveProvider(
                recorder.WaveFormat)
            {
                DiscardOnBufferOverflow = true,
                ReadFully = true
            };

        _receivedNonSilentAudio = false;
        LastPeak = 0.0f;

        recorder.DataAvailable +=
            (
                buffer,
                flags,
                devicePosition,
                qpcPosition) =>
            {
                if (buffer.Length == 0)
                    return;

                byte[] data =
                    buffer.ToArray();

                bufferedProvider.AddSamples(
                    data,
                    0,
                    data.Length);

                if (data.Length < sizeof(float))
                    return;

                ReadOnlySpan<float> samples =
                    MemoryMarshal.Cast<byte, float>(
                        data.AsSpan());

                float peak = 0.0f;

                foreach (float sample in samples)
                {
                    float absolute =
                        Math.Abs(sample);

                    if (absolute > peak)
                    {
                        peak = absolute;
                    }
                }

                LastPeak = peak;

                if (_receivedNonSilentAudio)
                    return;

                if (peak < SilenceThreshold)
                    return;

                _receivedNonSilentAudio = true;

                AudioReceived?.Invoke(
                    this,
                    EventArgs.Empty);
            };

        _bufferedProvider =
            bufferedProvider;

        _recorder =
            recorder;

        ProcessId =
            processId;

        recorder.StartRecording();
    }

    public async Task StopAsync()
    {
        var recorder =
            _recorder;

        if (recorder is null)
            return;

        _recorder = null;
        _bufferedProvider = null;

        ProcessId = 0;
        LastPeak = 0.0f;

        _receivedNonSilentAudio = false;

        try
        {
            recorder.StopRecording();
        }
        catch
        {
            // Best-effort shutdown.
        }

        await recorder.DisposeAsync();
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
    }
}