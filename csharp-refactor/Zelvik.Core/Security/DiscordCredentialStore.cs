using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

namespace Zelvik.Core.Security;

public sealed class DiscordCredentialStore
{
    private const string TargetName = "Zelvik";
    private const string UserName = "discord_bot_token";

    private const uint CredentialTypeGeneric = 1;
    private const uint CredentialPersistLocalMachine = 2;
    private const int ErrorNotFound = 1168;

    public string? ReadToken()
    {
        if (!CredRead(
                TargetName,
                CredentialTypeGeneric,
                0,
                out IntPtr credentialPointer))
        {
            int error =
                Marshal.GetLastWin32Error();

            if (error == ErrorNotFound)
                return null;

            throw new Win32Exception(
                error,
                "Unable to read the Discord bot token from Windows Credential Manager.");
        }

        try
        {
            CREDENTIAL credential =
                Marshal.PtrToStructure<CREDENTIAL>(
                    credentialPointer);

            if (credential.CredentialBlob == IntPtr.Zero
                || credential.CredentialBlobSize == 0)
            {
                return null;
            }

            string token =
                Marshal.PtrToStringUni(
                    credential.CredentialBlob,
                    (int)credential.CredentialBlobSize / 2)
                ?? string.Empty;

            token =
                token.TrimEnd('\0').Trim();

            return string.IsNullOrWhiteSpace(token)
                ? null
                : token;
        }
        finally
        {
            CredFree(
                credentialPointer);
        }
    }

    public void SaveToken(
        string token)
    {
        token =
            (token ?? string.Empty).Trim();

        if (string.IsNullOrWhiteSpace(token))
        {
            throw new ArgumentException(
                "Discord bot token cannot be empty.",
                nameof(token));
        }

        byte[] credentialBytes =
            Encoding.Unicode.GetBytes(
                token);

        IntPtr credentialBlob =
            Marshal.AllocCoTaskMem(
                credentialBytes.Length);

        try
        {
            Marshal.Copy(
                credentialBytes,
                0,
                credentialBlob,
                credentialBytes.Length);

            var credential =
                new CREDENTIAL
                {
                    Type =
                        CredentialTypeGeneric,

                    TargetName =
                        TargetName,

                    CredentialBlobSize =
                        (uint)credentialBytes.Length,

                    CredentialBlob =
                        credentialBlob,

                    Persist =
                        CredentialPersistLocalMachine,

                    UserName =
                        UserName
                };

            if (!CredWrite(
                    ref credential,
                    0))
            {
                int error =
                    Marshal.GetLastWin32Error();

                throw new Win32Exception(
                    error,
                    "Unable to save the Discord bot token to Windows Credential Manager.");
            }
        }
        finally
        {
            Marshal.ZeroFreeCoTaskMemUnicode(
                credentialBlob);
        }
    }

    public void DeleteToken()
    {
        if (CredDelete(
                TargetName,
                CredentialTypeGeneric,
                0))
        {
            return;
        }

        int error =
            Marshal.GetLastWin32Error();

        if (error == ErrorNotFound)
            return;

        throw new Win32Exception(
            error,
            "Unable to remove the Discord bot token from Windows Credential Manager.");
    }

    [StructLayout(
        LayoutKind.Sequential,
        CharSet = CharSet.Unicode)]
    private struct CREDENTIAL
    {
        public uint Flags;
        public uint Type;

        [MarshalAs(UnmanagedType.LPWStr)]
        public string TargetName;

        [MarshalAs(UnmanagedType.LPWStr)]
        public string? Comment;

        public long LastWritten;

        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;

        [MarshalAs(UnmanagedType.LPWStr)]
        public string? TargetAlias;

        [MarshalAs(UnmanagedType.LPWStr)]
        public string UserName;
    }

    [DllImport(
        "advapi32.dll",
        EntryPoint = "CredReadW",
        CharSet = CharSet.Unicode,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredRead(
        string target,
        uint type,
        uint flags,
        out IntPtr credential);

    [DllImport(
        "advapi32.dll",
        EntryPoint = "CredWriteW",
        CharSet = CharSet.Unicode,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredWrite(
        ref CREDENTIAL credential,
        uint flags);

    [DllImport(
        "advapi32.dll",
        EntryPoint = "CredDeleteW",
        CharSet = CharSet.Unicode,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredDelete(
        string target,
        uint type,
        uint flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(
        IntPtr buffer);
}
