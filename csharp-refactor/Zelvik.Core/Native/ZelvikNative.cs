using System.Runtime.InteropServices;

namespace Zelvik.Core.Native;

public static class ZelvikNative
{
    [DllImport(
        "Zelvik.Native.dll",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern int ZelvikNative_GetVersion();

    public static int GetVersion()
    {
        return ZelvikNative_GetVersion();
    }
}