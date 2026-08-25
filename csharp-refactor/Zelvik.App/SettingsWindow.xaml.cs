using System.Windows;
using Zelvik.Audio;

namespace Zelvik.App;

public partial class SettingsWindow : Window
{
    private readonly AudioDeviceService _audioDeviceService = new();
    private readonly AudioSessionService _audioSessionService = new();

    public SettingsWindow()
    {
        InitializeComponent();

        LoadSettings();
        LoadAudioDevices();
        LoadRoutingApplications();
    }

    private void LoadSettings()
    {
        var settings =
            App.SettingsManager.Settings;

        DiscordTokenPasswordBox.Password =
            settings.Discord.BotToken;

        YouTubeApiKeyPasswordBox.Password =
            settings.YouTube.ApiKey;

        MonitorRoutingCheckBox.IsChecked =
            settings.Audio.MonitorEnabled;
    }

    private void LoadAudioDevices()
    {
        var captureDevices =
            _audioDeviceService.GetCaptureDevices();

        var renderDevices =
            _audioDeviceService.GetRenderDevices();

        Input1DeviceComboBox.ItemsSource =
            captureDevices;

        Input2DeviceComboBox.ItemsSource =
            captureDevices;

        RoutingOutputDeviceComboBox.ItemsSource =
            renderDevices;

        var settings =
            App.SettingsManager.Settings.Audio;

        Input1DeviceComboBox.SelectedItem =
            captureDevices.FirstOrDefault(
                device =>
                    device.Id == settings.Aux1Source);

        Input2DeviceComboBox.SelectedItem =
            captureDevices.FirstOrDefault(
                device =>
                    device.Id == settings.Aux2Source);

        RoutingOutputDeviceComboBox.SelectedItem =
            renderDevices.FirstOrDefault(
                device =>
                    device.Id == settings.MonitorDevice);
    }

    private void LoadRoutingApplications()
    {
        var sessions =
            _audioSessionService.GetActiveSessions();

        ConfigureRoutingComboBox(
            RoutingApplication1ComboBox,
            sessions,
            App.SettingsManager.Settings.Audio.RoutingApplication1);

        ConfigureRoutingComboBox(
            RoutingApplication2ComboBox,
            sessions,
            App.SettingsManager.Settings.Audio.RoutingApplication2);
    }

    private static void ConfigureRoutingComboBox(
        System.Windows.Controls.ComboBox comboBox,
        IReadOnlyList<AudioSessionInfo> sessions,
        string savedProcessName)
    {
        comboBox.ItemsSource =
            sessions;

        comboBox.SelectedValuePath =
            nameof(AudioSessionInfo.ProcessName);

        if (!string.IsNullOrWhiteSpace(
                savedProcessName))
        {
            comboBox.SelectedValue =
                savedProcessName;
        }
    }

    private void RefreshRoutingApplications1Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        RefreshRoutingApplications(
            RoutingApplication1ComboBox,
            App.SettingsManager.Settings.Audio.RoutingApplication1);
    }

    private void RefreshRoutingApplications2Button_Click(
        object sender,
        RoutedEventArgs e)
    {
        RefreshRoutingApplications(
            RoutingApplication2ComboBox,
            App.SettingsManager.Settings.Audio.RoutingApplication2);
    }

    private void RefreshRoutingApplications(
        System.Windows.Controls.ComboBox comboBox,
        string savedProcessName)
    {
        string? currentSelection =
            comboBox.SelectedValue as string;

        if (string.IsNullOrWhiteSpace(
                currentSelection))
        {
            currentSelection =
                savedProcessName;
        }

        var sessions =
            _audioSessionService.GetActiveSessions();

        comboBox.ItemsSource =
            sessions;

        comboBox.SelectedValuePath =
            nameof(AudioSessionInfo.ProcessName);

        if (!string.IsNullOrWhiteSpace(
                currentSelection))
        {
            comboBox.SelectedValue =
                currentSelection;
        }
    }

    private void YouTubeSignInButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        var loginWindow =
            new YouTubeLoginWindow
            {
                Owner = this
            };

        loginWindow.ShowDialog();

        if (loginWindow.IsYouTubeSignedIn)
        {
            YouTubeAccountStatusText.Text =
                "Signed in";

            YouTubeSignInButton.Content =
                "Re-authenticate";
        }
        else
        {
            YouTubeAccountStatusText.Text =
                "Signed out";

            YouTubeSignInButton.Content =
                "Sign in to YouTube";
        }
    }

    private void SaveSettingsButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        var settings =
            App.SettingsManager.Settings;

        settings.Discord.BotToken =
            DiscordTokenPasswordBox.Password;

        settings.YouTube.ApiKey =
            YouTubeApiKeyPasswordBox.Password;

        settings.Audio.Aux1Source =
            (Input1DeviceComboBox.SelectedItem
                as AudioDeviceInfo)?.Id
            ?? string.Empty;

        settings.Audio.Aux2Source =
            (Input2DeviceComboBox.SelectedItem
                as AudioDeviceInfo)?.Id
            ?? string.Empty;

        settings.Audio.RoutingApplication1 =
            RoutingApplication1ComboBox.SelectedValue
                as string
            ?? string.Empty;

        settings.Audio.RoutingApplication2 =
            RoutingApplication2ComboBox.SelectedValue
                as string
            ?? string.Empty;

        settings.Audio.MonitorDevice =
            (RoutingOutputDeviceComboBox.SelectedItem
                as AudioDeviceInfo)?.Id
            ?? string.Empty;

        settings.Audio.MonitorEnabled =
            MonitorRoutingCheckBox.IsChecked == true;

        App.SettingsManager.Save();

        DialogResult = true;
        Close();
    }

    private void CancelSettingsButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}