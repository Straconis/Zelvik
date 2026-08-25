using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace Zelvik.Audio;

public sealed class AudioMixerService : IDisposable
{
    private const float ActivityThreshold =
        0.001f;

    private readonly object _inputLock =
        new();

    private readonly MixingSampleProvider _mixer;

    private readonly Dictionary<string, MixerInputState> _inputs =
        new(StringComparer.OrdinalIgnoreCase);

    public WaveFormat WaveFormat =>
        _mixer.WaveFormat;

    public float MasterVolume { get; set; } =
        1.0f;

    public float LastOutputPeak { get; private set; }

    public bool HasActiveOutput =>
        LastOutputPeak >= ActivityThreshold;

    public event EventHandler? OutputAudioReceived;

    public AudioMixerService()
    {
        _mixer =
            new MixingSampleProvider(
                WaveFormat.CreateIeeeFloatWaveFormat(
                    48000,
                    2))
            {
                ReadFully = true
            };
    }

    public void AddOrReplaceInput(
        string inputId,
        ISampleProvider source,
        float volume = 1.0f)
    {
        RemoveInput(
            inputId);

        ISampleProvider normalized =
            NormalizeFormat(
                source);

        var volumeProvider =
            new VolumeSampleProvider(
                normalized)
            {
                Volume =
                    ClampInputVolume(
                        volume)
            };

        /*
         * Meter AFTER the source volume control.
         *
         * That means the live meter represents the signal
         * Zelvik is actually feeding into the mixer, not
         * merely the raw source before the user's gain.
         */
        var meterProvider =
            new PeakMeterSampleProvider(
                volumeProvider);

        var state =
            new MixerInputState(
                volumeProvider,
                meterProvider);

        lock (_inputLock)
        {
            _inputs[inputId] =
                state;
        }

        _mixer.AddMixerInput(
            meterProvider);
    }

    public void RemoveInput(
        string inputId)
    {
        MixerInputState? state;

        lock (_inputLock)
        {
            if (!_inputs.TryGetValue(
                    inputId,
                    out state))
            {
                return;
            }

            _inputs.Remove(
                inputId);
        }

        _mixer.RemoveMixerInput(
            state.MeterProvider);
    }

    public void SetInputVolume(
        string inputId,
        float volume)
    {
        lock (_inputLock)
        {
            if (_inputs.TryGetValue(
                    inputId,
                    out var state))
            {
                state.VolumeProvider.Volume =
                    ClampInputVolume(
                        volume);
            }
        }
    }

    public float GetInputPeak(
        string inputId)
    {
        lock (_inputLock)
        {
            if (_inputs.TryGetValue(
                    inputId,
                    out var state))
            {
                return state.MeterProvider.LastPeak;
            }
        }

        return 0.0f;
    }

    public int Read(
        Span<float> buffer)
    {
        int samplesRead =
            _mixer.Read(
                buffer);

        /*
         * Master may eventually support boost independently
         * of the normal 0-100% controls, so permit up to 200%.
         */
        float master =
            Math.Clamp(
                MasterVolume,
                0.0f,
                2.0f);

        float peak =
            0.0f;

        for (int i = 0;
             i < samplesRead;
             i++)
        {
            float sample =
                buffer[i] * master;

            buffer[i] =
                sample;

            float absolute =
                Math.Abs(
                    sample);

            if (absolute > peak)
            {
                peak =
                    absolute;
            }
        }

        LastOutputPeak =
            peak;

        if (peak >= ActivityThreshold)
        {
            OutputAudioReceived?.Invoke(
                this,
                EventArgs.Empty);
        }

        return samplesRead;
    }

    public ISampleProvider GetMixedOutput()
    {
        return new MasterVolumeSampleProvider(
            this);
    }

    private ISampleProvider NormalizeFormat(
        ISampleProvider source)
    {
        ISampleProvider result =
            source;

        if (result.WaveFormat.SampleRate
            != 48000)
        {
            result =
                new WdlResamplingSampleProvider(
                    result,
                    48000);
        }

        if (result.WaveFormat.Channels
            == 1)
        {
            result =
                new MonoToStereoSampleProvider(
                    result);
        }
        else if (
            result.WaveFormat.Channels
            != 2)
        {
            throw new NotSupportedException(
                $"Unsupported channel count: {result.WaveFormat.Channels}");
        }

        return result;
    }

    private static float ClampInputVolume(
        float volume)
    {
        /*
         * 200% is intentional.
         *
         * YouTube can be unusually quiet, so Zelvik supports
         * source gain above unity where the UI permits it.
         */
        return Math.Clamp(
            volume,
            0.0f,
            2.0f);
    }

    public void Dispose()
    {
        string[] inputIds;

        lock (_inputLock)
        {
            inputIds =
                _inputs.Keys.ToArray();
        }

        foreach (string inputId in inputIds)
        {
            RemoveInput(
                inputId);
        }
    }

    private sealed class MixerInputState
    {
        public VolumeSampleProvider VolumeProvider
        {
            get;
        }

        public PeakMeterSampleProvider MeterProvider
        {
            get;
        }

        public MixerInputState(
            VolumeSampleProvider volumeProvider,
            PeakMeterSampleProvider meterProvider)
        {
            VolumeProvider =
                volumeProvider;

            MeterProvider =
                meterProvider;
        }
    }

    private sealed class PeakMeterSampleProvider :
        ISampleProvider
    {
        private readonly ISampleProvider _source;

        public WaveFormat WaveFormat =>
            _source.WaveFormat;

        public float LastPeak { get; private set; }

        public PeakMeterSampleProvider(
            ISampleProvider source)
        {
            _source =
                source;
        }

        public int Read(
            Span<float> buffer)
        {
            int samplesRead =
                _source.Read(
                    buffer);

            float peak =
                0.0f;

            for (int i = 0;
                 i < samplesRead;
                 i++)
            {
                float absolute =
                    Math.Abs(
                        buffer[i]);

                if (absolute > peak)
                {
                    peak =
                        absolute;
                }
            }

            LastPeak =
                peak;

            return samplesRead;
        }
    }

    private sealed class MasterVolumeSampleProvider :
        ISampleProvider
    {
        private readonly AudioMixerService _owner;

        public MasterVolumeSampleProvider(
            AudioMixerService owner)
        {
            _owner =
                owner;
        }

        public WaveFormat WaveFormat =>
            _owner.WaveFormat;

        public int Read(
            Span<float> buffer)
        {
            return _owner.Read(
                buffer);
        }
    }
}
