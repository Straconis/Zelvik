namespace Zelvik.Core.Paths;

public static class AppPaths
{
    public static string AppDataDirectory { get; } =
        Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "Zelvik");

    public static string SettingsFile { get; } =
        Path.Combine(AppDataDirectory, "settings.json");

    public static string LogsDirectory { get; } =
        Path.Combine(AppDataDirectory, "logs");

    public static void EnsureDirectories()
    {
        Directory.CreateDirectory(AppDataDirectory);
        Directory.CreateDirectory(LogsDirectory);
    }
}