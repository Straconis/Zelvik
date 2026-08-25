using System.Windows;
using System.Windows.Media;
using Zelvik.Core.Configuration;

namespace Zelvik.App;

public partial class App : Application
{
    public static SettingsManager SettingsManager { get; } = new();

    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        await SettingsManager.LoadAsync();

        ApplyTheme(SettingsManager.Settings.Ui.DarkMode);

        var mainWindow = new MainWindow();
        MainWindow = mainWindow;
        mainWindow.Show();
    }

    public static void ApplyTheme(bool darkMode)
    {
        if (darkMode)
        {
            Current.Resources["WindowBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(24, 24, 24));

            Current.Resources["PanelBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(36, 36, 36));

            Current.Resources["ControlBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(48, 48, 48));

            Current.Resources["ControlBorderBrush"] =
                new SolidColorBrush(Color.FromRgb(80, 80, 80));

            Current.Resources["PrimaryTextBrush"] =
                new SolidColorBrush(Color.FromRgb(240, 240, 240));

            Current.Resources["SecondaryTextBrush"] =
                new SolidColorBrush(Color.FromRgb(184, 184, 184));

            Current.Resources["DisabledTextBrush"] =
                new SolidColorBrush(Color.FromRgb(136, 136, 136));
        }
        else
        {
            Current.Resources["WindowBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(250, 250, 250));

            Current.Resources["PanelBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(255, 255, 255));

            Current.Resources["ControlBackgroundBrush"] =
                new SolidColorBrush(Color.FromRgb(242, 242, 242));

            Current.Resources["ControlBorderBrush"] =
                new SolidColorBrush(Color.FromRgb(180, 180, 180));

            Current.Resources["PrimaryTextBrush"] =
                new SolidColorBrush(Color.FromRgb(20, 20, 20));

            Current.Resources["SecondaryTextBrush"] =
                new SolidColorBrush(Color.FromRgb(90, 90, 90));

            Current.Resources["DisabledTextBrush"] =
                new SolidColorBrush(Color.FromRgb(120, 120, 120));
        }
    }
}