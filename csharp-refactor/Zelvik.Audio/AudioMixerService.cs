using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace Zelvik.Audio;

public sealed class AudioMixerService : IDisposable
{
    private const float ActivityThreshold = 0.001f;

    private readonly MixingSampleProvider _mixer;

    private readonly Dictionary<string, VolumeSampleProvider> _inputs =
        new(StringComparer.OrdinalIgnoreCase);

    private bool _outputActive;

    public WaveFormat WaveFormat =>
        _mixer.WaveFormat;

    public float MasterVolume { get; set; } = 1.0f;

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
        RemoveInput(inputId);

        ISampleProvider normalized =
            NormalizeFormat(source);

        var volumeProvider =
            new VolumeSampleProvider(
                normalized)
            {
                Volume =
                    ClampVolume(volume)
            };

        _inputs[inputId] =
            volumeProvider;

        _mixer.AddMixerInput(
            volumeProvider);
    }

    public void RemoveInput(
        string inputId)
    {
        if (!_inputs.TryGetValue(
                inputId,
                out var provider))
        {
            return;
        }

        _mixer.RemoveMixerInput(
            provider);

        _inputs.Remove(
            inputId);
    }

    public void SetInputVolume(
        string inputId,
        float volume)
    {
        if (_inputs.TryGetValue(
                inputId,
                out var provider))
        {
            provider.Volume =
                ClampVolume(volume);
        }
    }

    public int Read(
        Span<float> buffer)
    {
        int samplesRead =
            _mixer.Read(buffer);

        float master =
            ClampVolume(
                MasterVolume);

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
                Math.Abs(sample);

            if (absolute > peak)
            {
                peak =
                    absolute;
            }
        }

        LastOutputPeak =
            peak;

        bool active =
            peak >= ActivityThreshold;

        if (active)
        {
            /*
             * Fire repeatedly while real audio is present.
             *
             * This is intentional for diagnostics so the UI
             * can display the current peak level instead of
             * merely reporting that the mixer was read once.
             */
            OutputAudioReceived?.Invoke(
                this,
                EventArgs.Empty);

            _outputActive =
                true;
        }
        else
        {
            _outputActive =
                false;
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

    private static float ClampVolume(
        float volume)
    {
        return Math.Clamp(
            volume,
            0.0f,
            1.0f);
    }

    public void Dispose()
    {
        foreach (
            string inputId
            in _inputs.Keys.ToList())
        {
            RemoveInput(
                inputId);
        }
    }

    private sealed class MasterVolumeSampleProvider
        : ISampleProvider
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