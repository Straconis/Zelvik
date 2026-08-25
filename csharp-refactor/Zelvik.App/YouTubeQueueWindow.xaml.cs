using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Zelvik.YouTube;

namespace Zelvik.App;

public partial class YouTubeQueueWindow : Window
{
    private readonly YouTubeQueueService _queueService;
    private readonly Func<float> _volumeProvider;

    private Point _dragStartPoint;

    public event EventHandler? PlayResumeRequested;
    public event EventHandler? PlayNextRequested;

    public YouTubeQueueWindow(
        YouTubeQueueService queueService,
        Func<float>? volumeProvider = null)
    {
        _queueService =
            queueService
            ?? throw new ArgumentNullException(
                nameof(queueService));

        _volumeProvider =
            volumeProvider
            ?? (() => 1.0f);

        InitializeComponent();

        AddQueueItemButton.Click +=
            AddQueueItemButton_Click;

        PlayResumeButton.Click +=
            PlayResumeButton_Click;

        PlayNextButton.Click +=
            PlayNextButton_Click;

        RemoveSelectedButton.Click +=
            RemoveSelectedButton_Click;

        ClearQueueButton.Click +=
            ClearQueueButton_Click;

        QueueUrlTextBox.KeyDown +=
            QueueUrlTextBox_KeyDown;

        _queueService.QueueChanged +=
            QueueService_QueueChanged;

        _queueService.CurrentItemChanged +=
            QueueService_CurrentItemChanged;

        Closed +=
            YouTubeQueueWindow_Closed;

        RefreshQueue();
    }

    private void QueueUrlTextBox_KeyDown(
        object sender,
        KeyEventArgs e)
    {
        if (e.Key != Key.Enter)
            return;

        AddQueueItem();

        e.Handled =
            true;
    }

    private void AddQueueItemButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        AddQueueItem();
    }

    private void AddQueueItem()
    {
        string url =
            QueueUrlTextBox.Text.Trim();

        if (string.IsNullOrWhiteSpace(url))
            return;

        if (!LooksLikeYouTubeUrl(url))
        {
            MessageBox.Show(
                this,
                "That does not look like a YouTube URL.",
                "YouTube Queue",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);

            return;
        }

        float volume =
            Math.Clamp(
                _volumeProvider(),
                0.0f,
                2.0f);

        _queueService.Enqueue(
            url,
            volume: volume);

        QueueUrlTextBox.Clear();

        QueueUrlTextBox.Focus();
    }

    private static bool LooksLikeYouTubeUrl(
        string value)
    {
        if (!Uri.TryCreate(
                value,
                UriKind.Absolute,
                out Uri? uri))
        {
            return false;
        }

        string host =
            uri.Host.ToLowerInvariant();

        return
            host == "youtube.com"
            || host == "www.youtube.com"
            || host == "m.youtube.com"
            || host == "youtu.be"
            || host.EndsWith(
                ".youtube.com",
                StringComparison.OrdinalIgnoreCase);
    }

    private void PlayResumeButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        PlayResumeRequested?.Invoke(
            this,
            EventArgs.Empty);
    }

    private void PlayNextButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        PlayNextRequested?.Invoke(
            this,
            EventArgs.Empty);
    }

    private void RemoveSelectedButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (QueueListBox.SelectedItem
            is not QueueDisplayItem selected)
        {
            return;
        }

        _queueService.Remove(
            selected.Id);
    }

    private void ClearQueueButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_queueService.Count == 0)
            return;

        MessageBoxResult result =
            MessageBox.Show(
                this,
                "Remove every upcoming YouTube item from the queue?",
                "Clear YouTube Queue",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question,
                MessageBoxResult.No);

        if (result != MessageBoxResult.Yes)
            return;

        _queueService.Clear();
    }

    private void QueueService_QueueChanged(
        object? sender,
        EventArgs e)
    {
        Dispatcher.Invoke(
            RefreshQueue);
    }

    private void QueueService_CurrentItemChanged(
        object? sender,
        YouTubeQueueItem? e)
    {
        Dispatcher.Invoke(
            RefreshQueue);
    }

    private void RefreshQueue()
    {
        YouTubeQueueItem? current =
            _queueService.CurrentItem;

        NowPlayingText.Text =
            current is null
                ? "Nothing playing"
                : BuildDisplayText(
                    current);

        Guid? selectedId =
            (QueueListBox.SelectedItem
                as QueueDisplayItem)?.Id;

        IReadOnlyList<YouTubeQueueItem> snapshot =
            _queueService.GetSnapshot();

        QueueListBox.Items.Clear();

        for (int index = 0;
             index < snapshot.Count;
             index++)
        {
            YouTubeQueueItem item =
                snapshot[index];

            var display =
                new QueueDisplayItem(
                    item.Id,
                    item.Url,
                    $"{index + 1}. {BuildDisplayText(item)}");

            QueueListBox.Items.Add(
                display);

            if (selectedId == item.Id)
            {
                QueueListBox.SelectedItem =
                    display;
            }
        }
    }

    private static string BuildDisplayText(
        YouTubeQueueItem item)
    {
        if (!string.IsNullOrWhiteSpace(
                item.Title))
        {
            return item.Title;
        }

        return item.Url;
    }

    private void QueueListBox_MouseDoubleClick(
        object sender,
        MouseButtonEventArgs e)
    {
        if (QueueListBox.SelectedItem
            is not QueueDisplayItem selected)
        {
            return;
        }

        try
        {
            Process.Start(
                new ProcessStartInfo
                {
                    FileName =
                        selected.Url,

                    UseShellExecute =
                        true
                });
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                this,
                ex.Message,
                "Open YouTube",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void QueueListBox_PreviewMouseLeftButtonDown(
        object sender,
        MouseButtonEventArgs e)
    {
        _dragStartPoint =
            e.GetPosition(
                null);
    }

    private void QueueListBox_PreviewMouseMove(
        object sender,
        MouseEventArgs e)
    {
        if (e.LeftButton
            != MouseButtonState.Pressed)
        {
            return;
        }

        Point position =
            e.GetPosition(
                null);

        Vector difference =
            _dragStartPoint
            - position;

        if (Math.Abs(difference.X)
                < SystemParameters.MinimumHorizontalDragDistance
            &&
            Math.Abs(difference.Y)
                < SystemParameters.MinimumVerticalDragDistance)
        {
            return;
        }

        if (QueueListBox.SelectedItem
            is not QueueDisplayItem selected)
        {
            return;
        }

        DragDrop.DoDragDrop(
            QueueListBox,
            selected,
            DragDropEffects.Move);
    }

    private void QueueListBox_Drop(
        object sender,
        DragEventArgs e)
    {
        if (!e.Data.GetDataPresent(
                typeof(QueueDisplayItem)))
        {
            return;
        }

        if (e.Data.GetData(
                typeof(QueueDisplayItem))
            is not QueueDisplayItem dragged)
        {
            return;
        }

        int targetIndex =
            GetDropIndex(
                e.GetPosition(
                    QueueListBox));

        if (targetIndex < 0)
        {
            targetIndex =
                Math.Max(
                    0,
                    QueueListBox.Items.Count - 1);
        }

        _queueService.Move(
            dragged.Id,
            targetIndex);
    }

    private int GetDropIndex(
        Point position)
    {
        for (int index = 0;
             index < QueueListBox.Items.Count;
             index++)
        {
            if (QueueListBox.ItemContainerGenerator
                    .ContainerFromIndex(index)
                is not ListBoxItem container)
            {
                continue;
            }

            Point itemPosition =
                container.TranslatePoint(
                    new Point(0, 0),
                    QueueListBox);

            double midpoint =
                itemPosition.Y
                + (container.ActualHeight / 2.0);

            if (position.Y < midpoint)
            {
                return index;
            }
        }

        return QueueListBox.Items.Count - 1;
    }

    private void YouTubeQueueWindow_Closed(
        object? sender,
        EventArgs e)
    {
        _queueService.QueueChanged -=
            QueueService_QueueChanged;

        _queueService.CurrentItemChanged -=
            QueueService_CurrentItemChanged;
    }

    private sealed class QueueDisplayItem
    {
        public Guid Id { get; }

        public string Url { get; }

        public string DisplayText { get; }

        public QueueDisplayItem(
            Guid id,
            string url,
            string displayText)
        {
            Id =
                id;

            Url =
                url;

            DisplayText =
                displayText;
        }

        public override string ToString()
        {
            return DisplayText;
        }
    }
}
