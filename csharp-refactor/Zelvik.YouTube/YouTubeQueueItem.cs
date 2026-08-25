namespace Zelvik.YouTube;

public sealed class YouTubeQueueItem
{
    public Guid Id { get; init; } =
        Guid.NewGuid();

    public required string Url { get; init; }

    public string? Title { get; set; }

    public float Volume { get; set; } =
        1.0f;

    public bool Loop { get; set; }

    public TimeSpan? StartTime { get; set; }

    public TimeSpan? StopTime { get; set; }

    public DateTimeOffset AddedAt { get; init; } =
        DateTimeOffset.UtcNow;

    public override string ToString()
    {
        if (!string.IsNullOrWhiteSpace(Title))
        {
            return Title;
        }

        return Url;
    }
}
