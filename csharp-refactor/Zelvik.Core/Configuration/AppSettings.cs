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
    public string BotToken { get; set; } =
        string.Empty;

    public ulong GuildId { get; set; }

    public ulong VoiceChannelId { get; set; }
}

public sealed class YouTubeSettings
{
    public string ApiKey { get; set; } =
        string.Empty;

    public string CookieFile { get; set; } =
        string.Empty;
}

public sealed class AudioSettings
{
    public float MasterVolume { get; set; } =
        1.0f;

    public float MediaVolume { get; set; } =
        1.0f;

    public float LocalMediaVolume { get; set; } =
        0.85f;

    public float Aux1Volume { get; set; } =
        1.0f;

    public float Aux2Volume { get; set; } =
        1.0f;

    public float VirtualInputVolume { get; set; } =
        1.0f;

    /*
     * Legacy capture-device selections.
     *
     * Aux1Source and Aux2Source remain for compatibility while
     * the routed-input migration is completed.
     */
    public string Aux1Source { get; set; } =
        string.Empty;

    public string Aux2Source { get; set; } =
        string.Empty;

    /*
     * Application-routing selections.
     */
    public string RoutingApplication1 { get; set; } =
        string.Empty;

    public string RoutingApplication2 { get; set; } =
        string.Empty;

    /*
     * Each application route has its own enable state.
     *
     * Default true preserves existing Zelvik behavior when
     * upgrading from a settings file created before these
     * properties existed.
     */
    public bool Routing1Enabled { get; set; } =
        true;

    public bool Routing2Enabled { get; set; } =
        true;

    /*
     * Local monitoring is independent of whether either
     * application route is enabled.
     */
    public string MonitorDevice { get; set; } =
        string.Empty;

    public bool MonitorEnabled { get; set; }
}

public sealed class UiSettings
{
    public bool DarkMode { get; set; } =
        true;
}
