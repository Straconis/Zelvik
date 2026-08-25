using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace Zelvik.Audio;

public sealed class LocalFileAudioSource :
    IDisposable
{
    private AudioFileReader? _reader;

    public bool IsLoaded =>
        _reader is not null;

    public string? FilePath { get; private set; }

    public ISampleProvider? SampleProvider { get; private set; }

    public void Load(
        string filePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(
            filePath);

        DisposeReader();

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException(
                "The selected audio file does not exist.",
                filePath);
        }

        _reader =
            new AudioFileReader(
                filePath);

        FilePath =
            filePath;

        SampleProvider =
            ConvertToMixerFormat(
                _reader);
    }

    public void Restart()
    {
        if (_reader is null)
        {
            throw new InvalidOperationException(
                "No local audio file is loaded.");
        }

        _reader.Position =
            0;
    }

    public void Stop()
    {
        if (_reader is null)
            return;

        _reader.Position =
            0;
    }

    private static ISampleProvider ConvertToMixerFormat(
        ISampleProvider source)
    {
        ISampleProvider result =
            source;

        if (result.WaveFormat.SampleRate != 48000)
        {
            result =
                new WdlResamplingSampleProvider(
                    result,
                    48000);
        }

        if (result.WaveFormat.Channels == 1)
        {
            result =
                new MonoToStereoSampleProvider(
                    result);
        }
        else if (result.WaveFormat.Channels != 2)
        {
            throw new NotSupportedException(
                $"Local audio has {result.WaveFormat.Channels} channels. " +
                "Zelvik currently supports mono or stereo local files.");
        }

        return result;
    }

    private void DisposeReader()
    {
        SampleProvider =
            null;

        _reader?.Dispose();

        _reader =
            null;

        FilePath =
            null;
    }

    public void Dispose()
    {
        DisposeReader();
    }
}