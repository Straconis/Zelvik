using System.Text.Json;
using Zelvik.Core.Paths;

namespace Zelvik.Core.Configuration;

public sealed class SettingsManager
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public AppSettings Settings { get; private set; } = new();

    public async Task LoadAsync()
    {
        AppPaths.EnsureDirectories();

        if (!File.Exists(AppPaths.SettingsFile))
        {
            Settings = new AppSettings();
            await SaveAsync();
            return;
        }

        try
        {
            string json = await File.ReadAllTextAsync(AppPaths.SettingsFile);

            Settings =
                JsonSerializer.Deserialize<AppSettings>(json, JsonOptions)
                ?? new AppSettings();
        }
        catch (JsonException)
        {
            Settings = new AppSettings();
        }
    }

    public async Task SaveAsync()
    {
        AppPaths.EnsureDirectories();

        string json = JsonSerializer.Serialize(Settings, JsonOptions);

        await File.WriteAllTextAsync(
            AppPaths.SettingsFile,
            json);
    }

    public void Save()
    {
        AppPaths.EnsureDirectories();

        string json = JsonSerializer.Serialize(Settings, JsonOptions);

        File.WriteAllText(
            AppPaths.SettingsFile,
            json);
    }
}