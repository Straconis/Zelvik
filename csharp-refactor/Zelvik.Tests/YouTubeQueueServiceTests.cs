using Xunit;
using Zelvik.YouTube;

namespace Zelvik.Tests;

public sealed class YouTubeQueueServiceTests
{
    [Fact]
    public void Enqueue_AddsItem()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem item =
            queue.Enqueue("https://youtu.be/test");

        Assert.Equal(1, queue.Count);
        Assert.Equal("https://youtu.be/test", item.Url);
    }

    [Fact]
    public void Enqueue_AllowsYouTubeBoostVolume()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem item =
            queue.Enqueue(
                "https://youtu.be/test",
                volume: 1.75f);

        Assert.Equal(1.75f, item.Volume);
    }

    [Fact]
    public void Enqueue_ClampsVolumeToTwoHundredPercent()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem item =
            queue.Enqueue(
                "https://youtu.be/test",
                volume: 5.0f);

        Assert.Equal(2.0f, item.Volume);
    }

    [Fact]
    public void TakeNext_RemovesFirstQueuedItem()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem first =
            queue.Enqueue("https://youtu.be/first");

        queue.Enqueue("https://youtu.be/second");

        YouTubeQueueItem? current =
            queue.TakeNext();

        Assert.NotNull(current);
        Assert.Equal(first.Id, current.Id);
        Assert.Equal(first.Id, queue.CurrentItem?.Id);
        Assert.Equal(1, queue.Count);
    }

    [Fact]
    public void Remove_RemovesSelectedItem()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem first =
            queue.Enqueue("https://youtu.be/first");

        YouTubeQueueItem second =
            queue.Enqueue("https://youtu.be/second");

        bool removed =
            queue.Remove(first.Id);

        Assert.True(removed);
        Assert.Equal(1, queue.Count);
        Assert.Equal(
            second.Id,
            queue.GetSnapshot()[0].Id);
    }

    [Fact]
    public void Clear_RemovesUpcomingItems()
    {
        var queue = new YouTubeQueueService();

        queue.Enqueue("https://youtu.be/first");
        queue.Enqueue("https://youtu.be/second");

        queue.Clear();

        Assert.Equal(0, queue.Count);
    }

    [Fact]
    public void Move_ReordersQueue()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem first =
            queue.Enqueue("https://youtu.be/first");

        YouTubeQueueItem second =
            queue.Enqueue("https://youtu.be/second");

        YouTubeQueueItem third =
            queue.Enqueue("https://youtu.be/third");

        bool moved =
            queue.Move(third.Id, 0);

        IReadOnlyList<YouTubeQueueItem> snapshot =
            queue.GetSnapshot();

        Assert.True(moved);
        Assert.Equal(third.Id, snapshot[0].Id);
        Assert.Equal(first.Id, snapshot[1].Id);
        Assert.Equal(second.Id, snapshot[2].Id);
    }

    [Fact]
    public void SetOrder_ReordersEntireQueue()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem first =
            queue.Enqueue("https://youtu.be/first");

        YouTubeQueueItem second =
            queue.Enqueue("https://youtu.be/second");

        YouTubeQueueItem third =
            queue.Enqueue("https://youtu.be/third");

        bool reordered =
            queue.SetOrder(
                new[]
                {
                    second.Id,
                    third.Id,
                    first.Id
                });

        IReadOnlyList<YouTubeQueueItem> snapshot =
            queue.GetSnapshot();

        Assert.True(reordered);
        Assert.Equal(second.Id, snapshot[0].Id);
        Assert.Equal(third.Id, snapshot[1].Id);
        Assert.Equal(first.Id, snapshot[2].Id);
    }

    [Fact]
    public void CompleteCurrent_ClearsCurrentItem()
    {
        var queue = new YouTubeQueueService();

        queue.Enqueue("https://youtu.be/test");
        queue.TakeNext();

        Assert.NotNull(queue.CurrentItem);

        queue.CompleteCurrent();

        Assert.Null(queue.CurrentItem);
    }

    [Fact]
    public void RequeueCurrentAtFront_ReturnsCurrentToQueue()
    {
        var queue = new YouTubeQueueService();

        YouTubeQueueItem first =
            queue.Enqueue("https://youtu.be/first");

        YouTubeQueueItem second =
            queue.Enqueue("https://youtu.be/second");

        queue.TakeNext();
        queue.RequeueCurrentAtFront();

        IReadOnlyList<YouTubeQueueItem> snapshot =
            queue.GetSnapshot();

        Assert.Null(queue.CurrentItem);
        Assert.Equal(2, snapshot.Count);
        Assert.Equal(first.Id, snapshot[0].Id);
        Assert.Equal(second.Id, snapshot[1].Id);
    }
}