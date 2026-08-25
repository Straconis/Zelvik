using Xunit;
using Zelvik.Core.Native;

namespace Zelvik.Tests;

public sealed class ZelvikNativeAudioBufferTests
{
    [Fact]
    public void AudioBuffer_RoundTripsAudioWithoutModification()
    {
        const uint capacityFrames = 128;
        const uint bytesPerFrame = 4;
        const uint frameCount = 32;

        var handle = ZelvikNative.CreateAudioBuffer(
            capacityFrames,
            bytesPerFrame);

        Assert.NotEqual(nint.Zero, handle);

        try
        {
            var input = new byte[frameCount * bytesPerFrame];

            for (var i = 0; i < input.Length; i++)
            {
                input[i] = (byte)((i * 37) & 0xFF);
            }

            var written = ZelvikNative.WriteAudio(
                handle,
                input,
                frameCount);

            Assert.Equal(frameCount, written);
            Assert.Equal(
                frameCount,
                ZelvikNative.GetAvailableFrames(handle));

            var output = new byte[input.Length];

            var read = ZelvikNative.ReadAudio(
                handle,
                output,
                frameCount);

            Assert.Equal(frameCount, read);
            Assert.Equal(
                0u,
                ZelvikNative.GetAvailableFrames(handle));

            Assert.Equal(input, output);
        }
        finally
        {
            ZelvikNative.DestroyAudioBuffer(handle);
        }
    }

    [Fact]
    public void AudioBuffer_WrapsAroundWithoutCorruptingAudio()
    {
        const uint capacityFrames = 8;
        const uint bytesPerFrame = 2;

        var handle = ZelvikNative.CreateAudioBuffer(
            capacityFrames,
            bytesPerFrame);

        Assert.NotEqual(nint.Zero, handle);

        try
        {
            var first = new byte[]
            {
                0x01, 0x02,
                0x03, 0x04,
                0x05, 0x06,
                0x07, 0x08,
                0x09, 0x0A,
                0x0B, 0x0C
            };

            Assert.Equal(
                6u,
                ZelvikNative.WriteAudio(
                    handle,
                    first,
                    6));

            var firstRead = new byte[first.Length];

            Assert.Equal(
                6u,
                ZelvikNative.ReadAudio(
                    handle,
                    firstRead,
                    6));

            Assert.Equal(first, firstRead);

            var second = new byte[]
            {
                0x11, 0x12,
                0x13, 0x14,
                0x15, 0x16,
                0x17, 0x18,
                0x19, 0x1A,
                0x1B, 0x1C,
                0x1D, 0x1E
            };

            Assert.Equal(
                7u,
                ZelvikNative.WriteAudio(
                    handle,
                    second,
                    7));

            var secondRead = new byte[second.Length];

            Assert.Equal(
                7u,
                ZelvikNative.ReadAudio(
                    handle,
                    secondRead,
                    7));

            Assert.Equal(second, secondRead);

            Assert.Equal(
                0u,
                ZelvikNative.GetAvailableFrames(handle));
        }
        finally
        {
            ZelvikNative.DestroyAudioBuffer(handle);
        }
    }
}