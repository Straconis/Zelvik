using NAudio.CoreAudioApi;

namespace Zelvik.Audio;

public sealed class AudioDeviceService
{
    public IReadOnlyList<AudioDeviceInfo> GetCaptureDevices()
    {
        using var enumerator = new MMDeviceEnumerator();

        var devices = enumerator.EnumerateAudioEndPoints(
            DataFlow.Capture,
            DeviceState.Active);

        return devices
            .Select(device => new AudioDeviceInfo
            {
                Id = device.ID,
                Name = device.FriendlyName
            })
            .OrderBy(device => device.Name)
            .ToList();
    }

    public IReadOnlyList<AudioDeviceInfo> GetRenderDevices()
    {
        using var enumerator = new MMDeviceEnumerator();

        var devices = enumerator.EnumerateAudioEndPoints(
            DataFlow.Render,
            DeviceState.Active);

        return devices
            .Select(device => new AudioDeviceInfo
            {
                Id = device.ID,
                Name = device.FriendlyName
            })
            .OrderBy(device => device.Name)
            .ToList();
    }
}