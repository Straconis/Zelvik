using NAudio.CoreAudioApi;
using NAudio.Wave;

namespace Zelvik.Audio;

public sealed class ExternalInputCapture : IDisposable
{
    private WasapiCapture? _capture;
    private BufferedWaveProvider? _bufferedProvider;
    private bool _receivedAudio;

    public bool IsRunning => _capture is not null;

    public string DeviceName { get; private set; } = string.Empty;

    public WaveFormat? WaveFormat =>
        _bufferedProvider?.WaveFormat;

    public IWaveProvider? WaveProvider =>
        _bufferedProvider;

    public event EventHandler? AudioReceived;

    public void Start(string deviceId)
    {
        if (string.IsNullOrWhiteSpace(deviceId))
        {
            throw new InvalidOperationException(
                "No audio input device has been configured.");
        }

        Stop();

        using var enumerator = new MMDeviceEnumerator();
        var device = enumerator.GetDevice(deviceId);

        DeviceName = device.FriendlyName;
        _receivedAudio = false;

        var capture = new WasapiCapture(device);

        var bufferedProvider =
            new BufferedWaveProvider(capture.WaveFormat)
            {
                DiscardOnBufferOverflow = true,
                ReadFully = true
            };

        _bufferedProvider = bufferedProvider;

        capture.DataAvailable += Capture_DataAvailable;
        capture.RecordingStopped += Capture_RecordingStopped;

        _capture = capture;

        capture.StartRecording();
    }

    public void Stop()
    {
        var capture = _capture;

        if (capture is null)
            return;

        _capture = null;

        try
        {
            capture.StopRecording();
        }
        catch
        {
            // Device may already have stopped or disappeared.
        }

        capture.DataAvailable -= Capture_DataAvailable;
        capture.RecordingStopped -= Capture_RecordingStopped;

        capture.Dispose();

        _bufferedProvider = null;
        DeviceName = string.Empty;
        _receivedAudio = false;
    }

    public ISampleProvider GetSampleProvider()
    {
        if (_bufferedProvider is null)
        {
            throw new InvalidOperationException(
                "The capture device is not running.");
        }

        return _bufferedProvider.ToSampleProvider();
    }

    private void Capture_DataAvailable(
        object? sender,
        WaveInEventArgs e)
    {
        if (e.BytesRecorded <= 0)
            return;

        _bufferedProvider?.AddSamples(
            e.Buffer,
            0,
            e.BytesRecorded);

        if (_receivedAudio)
            return;

        _receivedAudio = true;

        AudioReceived?.Invoke(
            this,
            EventArgs.Empty);
    }

    private void Capture_RecordingStopped(
        object? sender,
        StoppedEventArgs e)
    {
        // Detailed fault reporting can be added later.
    }

    public void Dispose()
    {
        Stop();
    }
}