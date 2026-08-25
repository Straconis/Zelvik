using System.Diagnostics;
using NAudio.CoreAudioApi;

namespace Zelvik.Audio;

public sealed class AudioSessionInfo
{
    public int ProcessId { get; init; }

    public string ProcessName { get; init; } = string.Empty;

    public string DisplayName { get; init; } = string.Empty;

    public override string ToString()
    {
        return string.IsNullOrWhiteSpace(DisplayName)
            ? ProcessName
            : DisplayName;
    }
}

public sealed class AudioSessionService
{
    public IReadOnlyList<AudioSessionInfo> GetActiveSessions()
    {
        var results = new List<AudioSessionInfo>();

        using var enumerator =
            new MMDeviceEnumerator();

        using var device =
            enumerator.GetDefaultAudioEndpoint(
                DataFlow.Render,
                Role.Multimedia);

        var sessions =
            device.AudioSessionManager.Sessions;

        for (int i = 0; i < sessions.Count; i++)
        {
            using var session =
                sessions[i];

            int processId;

            try
            {
                processId =
                    (int)session.GetProcessID;
            }
            catch
            {
                continue;
            }

            if (processId <= 0)
                continue;

            try
            {
                using var process =
                    Process.GetProcessById(
                        processId);

                string processName =
                    process.ProcessName;

                string displayName =
                    !string.IsNullOrWhiteSpace(
                        session.DisplayName)
                        ? session.DisplayName
                        : processName;

                if (results.Any(
                        x =>
                            x.ProcessId ==
                            processId))
                {
                    continue;
                }

                results.Add(
                    new AudioSessionInfo
                    {
                        ProcessId =
                            processId,

                        ProcessName =
                            processName,

                        DisplayName =
                            displayName
                    });
            }
            catch
            {
                // Process may disappear between
                // enumeration and lookup.
            }
        }

        return results
            .OrderBy(
                x => x.DisplayName)
            .ToList();
    }

    public AudioSessionInfo? FindActiveSession(
        string processName)
    {
        if (string.IsNullOrWhiteSpace(
                processName))
        {
            return null;
        }

        string normalizedName =
            Path.GetFileNameWithoutExtension(
                processName);

        return GetActiveSessions()
            .Where(
                session =>
                    string.Equals(
                        session.ProcessName,
                        normalizedName,
                        StringComparison.OrdinalIgnoreCase))
            .OrderBy(
                session =>
                    session.ProcessId)
            .FirstOrDefault();
    }
}