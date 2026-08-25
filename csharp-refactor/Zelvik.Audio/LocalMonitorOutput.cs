using NAudio.CoreAudioApi;
using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace Zelvik.Audio;

public sealed class LocalMonitorOutput : IDisposable
{
    private WasapiPlayer? _player;
    private MMDevice? _device;

    public bool IsRunning =>
        _player is not null;

    public string DeviceName =>
        _player?.DeviceFriendlyName
        ?? string.Empty;

    public int LatencyMilliseconds =>
        _player?.LatencyMilliseconds
        ?? 0;

    public bool LowLatencyActive =>
        _player?.LowLatencyActive
        ?? false;

    public void Start(
        ISampleProvider source,
        string? deviceId = null)
    {
        Stop();

        var waveProvider =
            new SampleToWaveProvider(source);

        WasapiPlayer player;

        if (string.IsNullOrWhiteSpace(deviceId))
        {
            player =
                new WasapiPlayerBuilder()
                    .WithSharedMode()
                    .WithEventSync()
                    .WithLatency(100)
                    .Build();
        }
        else
        {
            using var enumerator =
                new MMDeviceEnumerator();

            var device =
                enumerator.GetDevice(deviceId);

            try
            {
                player =
                    new WasapiPlayerBuilder()
                        .WithDevice(device)
                        .WithSharedMode()
                        .WithEventSync()
                        .WithLatency(100)
                        .Build();

                // WasapiPlayer retains the MMDevice internally.
                // Keep our MMDevice alive for the lifetime
                // of the player instead of disposing it here.
                _device =
                    device;
            }
            catch
            {
                device.Dispose();
                throw;
            }
        }

        try
        {
            player.Init(
                waveProvider);

            _player =
                player;

            player.Play();
        }
        catch
        {
            player.Dispose();

            _device?.Dispose();
            _device = null;

            throw;
        }
    }

    public void Stop()
    {
        var player =
            _player;

        _player = null;

        if (player is not null)
        {
            try
            {
                player.Stop();
            }
            catch
            {
                // Best-effort shutdown.
            }

            try
            {
                player.Dispose();
            }
            catch
            {
            }
        }

        var device =
            _device;

        _device = null;

        if (device is not null)
        {
            try
            {
                device.Dispose();
            }
            catch
            {
            }
        }
    }

    public void Dispose()
    {
        Stop();
    }
}