using System.IO;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace Zelvik.App;

public partial class YouTubeLoginWindow : Window
{
    private readonly string _profilePath;

    private readonly YouTubeCookieService _cookieService =
        new();

    public bool IsYouTubeSignedIn { get; private set; }

    public YouTubeLoginWindow()
    {
        InitializeComponent();

        _profilePath =
            Path.Combine(
                Environment.GetFolderPath(
                    Environment.SpecialFolder.LocalApplicationData),
                "Zelvik",
                "WebView2",
                "YouTube");

        Loaded +=
            YouTubeLoginWindow_Loaded;
    }

    private async void YouTubeLoginWindow_Loaded(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            Directory.CreateDirectory(
                _profilePath);

            var environment =
                await CoreWebView2Environment.CreateAsync(
                    browserExecutableFolder: null,
                    userDataFolder: _profilePath);

            await YouTubeWebView.EnsureCoreWebView2Async(
                environment);

            YouTubeWebView.CoreWebView2.Settings.AreDevToolsEnabled =
                false;

            YouTubeWebView.CoreWebView2.Settings.AreDefaultContextMenusEnabled =
                true;

            YouTubeWebView.CoreWebView2.Settings.IsStatusBarEnabled =
                true;

            YouTubeWebView.CoreWebView2.NavigationCompleted +=
                CoreWebView2_NavigationCompleted;

            YouTubeWebView.CoreWebView2.Navigate(
                "https://www.youtube.com/");
        }
        catch (Exception ex)
        {
            LoginStatusText.Text =
                "Initialization failed";

            MessageBox.Show(
                ex.ToString(),
                "YouTube Login Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private async void CoreWebView2_NavigationCompleted(
        object? sender,
        CoreWebView2NavigationCompletedEventArgs e)
    {
        await UpdateLoginStatusAsync();
    }

    private async void CheckLoginButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        await UpdateLoginStatusAsync();
    }

    private async Task UpdateLoginStatusAsync()
    {
        if (YouTubeWebView.CoreWebView2 is null)
            return;

        try
        {
            IsYouTubeSignedIn =
                await _cookieService.IsSignedInAsync(
                    YouTubeWebView.CoreWebView2.CookieManager);

            var cookies =
                await YouTubeWebView.CoreWebView2
                    .CookieManager
                    .GetCookiesAsync(
                        "https://www.youtube.com/");

            if (IsYouTubeSignedIn)
            {
                LoginStatusText.Text =
                    "Signed in";

                CookieStatusText.Text =
                    $"YouTube authentication detected ({cookies.Count} cookies).";
            }
            else
            {
                LoginStatusText.Text =
                    "Signed out";

                CookieStatusText.Text =
                    $"No authenticated YouTube session detected ({cookies.Count} cookies found).";
            }
        }
        catch (Exception ex)
        {
            LoginStatusText.Text =
                "Check failed";

            CookieStatusText.Text =
                ex.Message;
        }
    }

    private async void TestCookieExportButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (YouTubeWebView.CoreWebView2 is null)
        {
            MessageBox.Show(
                "The YouTube browser is not ready yet.",
                "Cookie Export",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);

            return;
        }

        try
        {
            bool signedIn =
                await _cookieService.IsSignedInAsync(
                    YouTubeWebView.CoreWebView2.CookieManager);

            if (!signedIn)
            {
                MessageBox.Show(
                    "Zelvik does not currently detect an authenticated YouTube session.",
                    "Cookie Export",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);

                return;
            }

            string cookieFile =
                await _cookieService.CreateTemporaryCookieFileAsync(
                    YouTubeWebView.CoreWebView2.CookieManager);

            CookieStatusText.Text =
                $"Cookie export created: {cookieFile}";

            MessageBox.Show(
                $"yt-dlp cookie file created successfully:\n\n{cookieFile}",
                "Cookie Export Successful",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                ex.ToString(),
                "Cookie Export Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void CloseButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        Close();
    }
}