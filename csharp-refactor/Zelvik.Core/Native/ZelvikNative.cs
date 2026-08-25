using System.Runtime.InteropServices;

namespace Zelvik.Core.Native;

public static class ZelvikNative
{
    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern int ZelvikNative_GetVersion();

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern nint ZelvikNative_AudioBuffer_Create(
        uint capacityFrames,
        uint bytesPerFrame);

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern void ZelvikNative_AudioBuffer_Destroy(
        nint handle);

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern uint ZelvikNative_AudioBuffer_Write(
        nint handle,
        nint data,
        uint frameCount);

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern uint ZelvikNative_AudioBuffer_Read(
        nint handle,
        nint data,
        uint frameCount);

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern uint ZelvikNative_AudioBuffer_AvailableFrames(
        nint handle);

    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern uint ZelvikNative_AudioBuffer_CapacityFrames(
        nint handle);

    public static int GetVersion()
    {
        return ZelvikNative_GetVersion();
    }

    public static nint CreateAudioBuffer(
        uint capacityFrames,
        uint bytesPerFrame)
    {
        return ZelvikNative_AudioBuffer_Create(
            capacityFrames,
            bytesPerFrame);
    }

    public static void DestroyAudioBuffer(nint handle)
    {
        ZelvikNative_AudioBuffer_Destroy(handle);
    }

    public static unsafe uint WriteAudio(
        nint handle,
        ReadOnlySpan<byte> data,
        uint frameCount)
    {
        if (handle == nint.Zero || data.IsEmpty)
        {
            return 0;
        }

        fixed (byte* pointer = data)
        {
            return ZelvikNative_AudioBuffer_Write(
                handle,
                (nint)pointer,
                frameCount);
        }
    }

    public static unsafe uint ReadAudio(
        nint handle,
        Span<byte> data,
        uint frameCount)
    {
        if (handle == nint.Zero || data.IsEmpty)
        {
            return 0;
        }

        fixed (byte* pointer = data)
        {
            return ZelvikNative_AudioBuffer_Read(
                handle,
                (nint)pointer,
                frameCount);
        }
    }

    public static uint GetAvailableFrames(nint handle)
    {
        return ZelvikNative_AudioBuffer_AvailableFrames(handle);
    }

    public static uint GetCapacityFrames(nint handle)
    {
        return ZelvikNative_AudioBuffer_CapacityFrames(handle);
    }
}