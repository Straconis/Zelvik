namespace Zelvik.YouTube;

public sealed class YouTubeQueueService
{
    private readonly object _syncRoot =
        new();

    private readonly List<YouTubeQueueItem> _queue =
        new();

    public YouTubeQueueItem? CurrentItem { get; private set; }

    public event EventHandler? QueueChanged;

    public event EventHandler<YouTubeQueueItem?>?
        CurrentItemChanged;

    public int Count
    {
        get
        {
            lock (_syncRoot)
            {
                return _queue.Count;
            }
        }
    }

    public bool HasCurrentItem =>
        CurrentItem is not null;

    public bool HasQueuedItems =>
        Count > 0;

    public IReadOnlyList<YouTubeQueueItem> GetSnapshot()
    {
        lock (_syncRoot)
        {
            return _queue.ToList();
        }
    }

    public YouTubeQueueItem Enqueue(
        string url,
        float volume = 1.0f,
        bool loop = false,
        TimeSpan? startTime = null,
        TimeSpan? stopTime = null,
        string? title = null)
    {
        if (string.IsNullOrWhiteSpace(url))
        {
            throw new ArgumentException(
                "A YouTube URL is required.",
                nameof(url));
        }

        var item =
            new YouTubeQueueItem
            {
                Url = url.Trim(),
                Title = title,
                Volume = Math.Clamp(
                    volume,
                    0.0f,
                    2.0f),
                Loop = loop,
                StartTime = startTime,
                StopTime = stopTime
            };

        lock (_syncRoot)
        {
            _queue.Add(item);
        }

        OnQueueChanged();

        return item;
    }

    public bool Remove(Guid id)
    {
        bool removed;

        lock (_syncRoot)
        {
            int index =
                _queue.FindIndex(
                    item => item.Id == id);

            if (index < 0)
            {
                return false;
            }

            _queue.RemoveAt(index);

            removed = true;
        }

        if (removed)
        {
            OnQueueChanged();
        }

        return removed;
    }

    public void Clear()
    {
        bool changed;

        lock (_syncRoot)
        {
            changed =
                _queue.Count > 0;

            _queue.Clear();
        }

        if (changed)
        {
            OnQueueChanged();
        }
    }

    public bool Move(
        Guid id,
        int newIndex)
    {
        lock (_syncRoot)
        {
            int oldIndex =
                _queue.FindIndex(
                    item => item.Id == id);

            if (oldIndex < 0)
            {
                return false;
            }

            if (_queue.Count <= 1)
            {
                return true;
            }

            newIndex =
                Math.Clamp(
                    newIndex,
                    0,
                    _queue.Count - 1);

            if (oldIndex == newIndex)
            {
                return true;
            }

            YouTubeQueueItem item =
                _queue[oldIndex];

            _queue.RemoveAt(oldIndex);

            _queue.Insert(
                newIndex,
                item);
        }

        OnQueueChanged();

        return true;
    }

    public bool SetOrder(
        IEnumerable<Guid> orderedIds)
    {
        ArgumentNullException.ThrowIfNull(
            orderedIds);

        List<Guid> ids =
            orderedIds.ToList();

        lock (_syncRoot)
        {
            if (ids.Count != _queue.Count)
            {
                return false;
            }

            if (ids.Distinct().Count()
                != ids.Count)
            {
                return false;
            }

            Dictionary<Guid, YouTubeQueueItem> items =
                _queue.ToDictionary(
                    item => item.Id);

            if (ids.Any(
                    id => !items.ContainsKey(id)))
            {
                return false;
            }

            _queue.Clear();

            foreach (Guid id in ids)
            {
                _queue.Add(
                    items[id]);
            }
        }

        OnQueueChanged();

        return true;
    }

    public YouTubeQueueItem? TakeNext()
    {
        YouTubeQueueItem? next;

        lock (_syncRoot)
        {
            if (_queue.Count == 0)
            {
                next = null;
            }
            else
            {
                next =
                    _queue[0];

                _queue.RemoveAt(0);
            }

            CurrentItem =
                next;
        }

        OnQueueChanged();
        OnCurrentItemChanged();

        return next;
    }

    public void SetCurrent(
        YouTubeQueueItem? item)
    {
        lock (_syncRoot)
        {
            CurrentItem =
                item;
        }

        OnCurrentItemChanged();
    }

    public void CompleteCurrent()
    {
        bool changed;

        lock (_syncRoot)
        {
            changed =
                CurrentItem is not null;

            CurrentItem =
                null;
        }

        if (changed)
        {
            OnCurrentItemChanged();
        }
    }

    public void RequeueCurrentAtFront()
    {
        lock (_syncRoot)
        {
            if (CurrentItem is null)
            {
                return;
            }

            _queue.Insert(
                0,
                CurrentItem);

            CurrentItem =
                null;
        }

        OnQueueChanged();
        OnCurrentItemChanged();
    }

    private void OnQueueChanged()
    {
        QueueChanged?.Invoke(
            this,
            EventArgs.Empty);
    }

    private void OnCurrentItemChanged()
    {
        CurrentItemChanged?.Invoke(
            this,
            CurrentItem);
    }
}
