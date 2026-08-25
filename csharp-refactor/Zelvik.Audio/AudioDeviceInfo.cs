namespace Zelvik.Audio;

public sealed class AudioDeviceInfo
{
    public string Id { get; init; } = string.Empty;

    public string Name { get; init; } = string.Empty;

    public override string ToString()
    {
        return Name;
    }
}