using NAudio.Wave;
using NAudio.Wave.SampleProviders;
using Xunit;
using Zelvik.Audio;

namespace Zelvik.Tests;

public class AudioMixerServiceTests
{
    [Fact]
    public void MixerOutputsSilenceWhenNoInputsExist()
    {
        using var mixer = new AudioMixerService();

        float[] buffer = new float[480];

        int samplesRead = mixer.Read(buffer);

        Assert.Equal(buffer.Length, samplesRead);
        Assert.All(buffer, sample => Assert.Equal(0.0f, sample));
    }

    [Fact]
    public void SingleInputPassesThroughMixer()
    {
        using var mixer = new AudioMixerService();

        var source = CreateConstantSource(0.5f);

        mixer.AddOrReplaceInput(
            "test",
            source,
            1.0f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.5f, sample, 3));
    }

    [Fact]
    public void InputVolumeChangesSourceGain()
    {
        using var mixer = new AudioMixerService();

        var source = CreateConstantSource(1.0f);

        mixer.AddOrReplaceInput(
            "test",
            source,
            0.25f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.25f, sample, 3));
    }

    [Fact]
    public void MasterVolumeChangesEntireMix()
    {
        using var mixer = new AudioMixerService();

        mixer.MasterVolume = 0.5f;

        mixer.AddOrReplaceInput(
            "test",
            CreateConstantSource(1.0f),
            1.0f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.5f, sample, 3));
    }

    [Fact]
    public void MultipleInputsAreMixedTogether()
    {
        using var mixer = new AudioMixerService();

        mixer.AddOrReplaceInput(
            "input1",
            CreateConstantSource(0.25f),
            1.0f);

        mixer.AddOrReplaceInput(
            "input2",
            CreateConstantSource(0.50f),
            1.0f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.75f, sample, 3));
    }

    [Fact]
    public void RemovingInputRemovesItFromMix()
    {
        using var mixer = new AudioMixerService();

        mixer.AddOrReplaceInput(
            "input1",
            CreateConstantSource(0.25f),
            1.0f);

        mixer.AddOrReplaceInput(
            "input2",
            CreateConstantSource(0.50f),
            1.0f);

        mixer.RemoveInput("input2");

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.25f, sample, 3));
    }

    [Fact]
    public void ZeroInputVolumeProducesSilence()
    {
        using var mixer = new AudioMixerService();

        mixer.AddOrReplaceInput(
            "test",
            CreateConstantSource(1.0f),
            0.0f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.0f, sample, 3));
    }

    [Fact]
    public void SetInputVolumeChangesExistingInput()
    {
        using var mixer = new AudioMixerService();

        mixer.AddOrReplaceInput(
            "test",
            CreateConstantSource(1.0f),
            1.0f);

        mixer.SetInputVolume(
            "test",
            0.4f);

        float[] buffer = new float[480];

        mixer.Read(buffer);

        Assert.All(
            buffer,
            sample => Assert.Equal(0.4f, sample, 3));
    }

    private static ISampleProvider CreateConstantSource(
        float value)
    {
        return new ConstantSampleProvider(
            WaveFormat.CreateIeeeFloatWaveFormat(
                48000,
                2),
            value);
    }

    private sealed class ConstantSampleProvider
        : ISampleProvider
    {
        private readonly float _value;

        public WaveFormat WaveFormat { get; }

        public ConstantSampleProvider(
            WaveFormat waveFormat,
            float value)
        {
            WaveFormat = waveFormat;
            _value = value;
        }

        public int Read(
            Span<float> buffer)
        {
            buffer.Fill(_value);
            return buffer.Length;
        }
    }
}