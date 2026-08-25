using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;

namespace Zelvik.App;

public partial class MainWindow
{
    private const string VirtualInputMixerId =
        "virtual-input";

    private readonly Dictionary<ProgressBar, MeterBinding>
        _audioMeterBindings =
            new();

    private DispatcherTimer? _audioMeterTimer;

    protected override void OnContentRendered(
        EventArgs e)
    {
        base.OnContentRendered(e);

        if (_audioMeterTimer is not null)
            return;

        CreateAudioMeters();

        _audioMeterTimer =
            new DispatcherTimer(
                DispatcherPriority.Background)
            {
                Interval = TimeSpan.FromMilliseconds(50)
            };

        _audioMeterTimer.Tick += AudioMeterTimer_Tick;
        _audioMeterTimer.Start();
    }

    private void CreateAudioMeters()
    {
        AddAudioMeter(
            Input1VolumeSlider,
            () => _audioMixer.GetInputPeak(Input1MixerId),
            "#FF9800");

        AddAudioMeter(
            Input2VolumeSlider,
            () => _audioMixer.GetInputPeak(Input2MixerId),
            "#3B9CFF");

        AddAudioMeter(
            MediaVolumeSlider,
            () => _audioMixer.GetInputPeak(YouTubeMixerId),
            "#FF4D4D");

        AddAudioMeter(
            LocalMediaVolumeSlider,
            () => _audioMixer.GetInputPeak(LocalMediaMixerId),
            "#32CD70");

        AddAudioMeter(
            VirtualInputVolumeSlider,
            () => _audioMixer.GetInputPeak(VirtualInputMixerId),
            "#B26CFF");

        AddAudioMeter(
            MasterVolumeSlider,
            () => _audioMixer.LastOutputPeak,
            "#D0D0D0");
    }

    private void AddAudioMeter(
        Slider slider,
        Func<float> peakReader,
        string color)
    {
        if (slider.Parent is not Panel parent)
            return;

        int sliderIndex =
            parent.Children.IndexOf(slider);

        if (sliderIndex < 0)
            return;

        Thickness oldMargin =
            slider.Margin;

        slider.Margin =
            new Thickness(
                oldMargin.Left,
                oldMargin.Top,
                oldMargin.Right,
                2);

        var meter =
            new ProgressBar
            {
                Minimum = 0,
                Maximum = 100,
                Value = 0,
                Height = 8,
                IsHitTestVisible = false,
                Focusable = false,

                Margin =
                    new Thickness(
                        oldMargin.Left,
                        0,
                        oldMargin.Right,
                        oldMargin.Bottom),

                Background =
                    new SolidColorBrush(
                        Color.FromRgb(35, 35, 35)),

                Foreground =
                    new SolidColorBrush(
                        (Color)ColorConverter.ConvertFromString(color))
            };

        parent.Children.Insert(
            sliderIndex + 1,
            meter);

        _audioMeterBindings[meter] =
            new MeterBinding(peakReader);
    }

    private void AudioMeterTimer_Tick(
        object? sender,
        EventArgs e)
    {
        foreach (var pair in _audioMeterBindings)
        {
            ProgressBar meter = pair.Key;
            MeterBinding binding = pair.Value;

            float peak;

            try
            {
                peak = binding.PeakReader();
            }
            catch
            {
                peak = 0.0f;
            }

            double target =
                PeakToMeterPercent(peak);

            if (target >= binding.DisplayedLevel)
            {
                binding.DisplayedLevel = target;
            }
            else
            {
                binding.DisplayedLevel *= 0.78;

                if (binding.DisplayedLevel < 0.25)
                    binding.DisplayedLevel = 0.0;
            }

            meter.Value =
                binding.DisplayedLevel;
        }
    }

    private static double PeakToMeterPercent(
        float peak)
    {
        if (peak <= 0.000001f)
            return 0.0;

        double db =
            20.0 * Math.Log10(peak);

        db =
            Math.Clamp(
                db,
                -60.0,
                0.0);

        return
            ((db + 60.0) / 60.0)
            * 100.0;
    }

    private sealed class MeterBinding
    {
        public Func<float> PeakReader { get; }

        public double DisplayedLevel
        {
            get;
            set;
        }

        public MeterBinding(
            Func<float> peakReader)
        {
            PeakReader = peakReader;
        }
    }
}
