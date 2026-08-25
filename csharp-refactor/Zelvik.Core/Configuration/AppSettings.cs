namespace Zelvik.Core.Configuration;

public sealed class AppSettings
{
    public DiscordSettings Discord { get; set; } = new();
    public YouTubeSettings YouTube { get; set; } = new();
    public AudioSettings Audio { get; set; } = new();
    public UiSettings Ui { get; set; } = new();
}

public sealed class DiscordSettings
{
    public string BotToken { get; set; } = string.Empty;
    public ulong GuildId { get; set; }
    public ulong VoiceChannelId { get; set; }
}

public sealed class YouTubeSettings
{
    public string ApiKey { get; set; } = string.Empty;
    public string CookieFile { get; set; } = string.Empty;
}

public sealed class AudioSettings
{
    public float MasterVolume { get; set; } = 1.0f;

    public float MediaVolume { get; set; } = 1.0f;
    public float LocalMediaVolume { get; set; } = 0.85f;

    public float Aux1Volume { get; set; } = 1.0f;
    public float Aux2Volume { get; set; } = 1.0f;

    public float VirtualInputVolume { get; set; } = 1.0f;

    // Legacy capture-device selections.
    // We will phase these out as routed application inputs take over.
    public string Aux1Source { get; set; } = string.Empty;
    public string Aux2Source { get; set; } = string.Empty;

    // Routed application inputs.
    public string RoutingApplication1 { get; set; } = string.Empty;
    public string RoutingApplication2 { get; set; } = string.Empty;

    public string MonitorDevice { get; set; } = string.Empty;
    public bool MonitorEnabled { get; set; }
}

public sealed class UiSettings
{
    public bool DarkMode { get; set; } = true;
}