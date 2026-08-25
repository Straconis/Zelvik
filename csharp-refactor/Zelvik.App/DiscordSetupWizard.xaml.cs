using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using Zelvik.Core.Security;
using Zelvik.Discord;

namespace Zelvik.App;

public partial class DiscordSetupWizard : Window
{
    private readonly DiscordSetupService _discordSetupService =
        new();

    private readonly DiscordCredentialStore _credentialStore =
        new();

    private readonly List<WizardStep> _steps;

    private int _currentStep;

    private string _validatedToken =
        string.Empty;

    private ulong? _validatedBotId;

    private string _validatedBotName =
        string.Empty;

    private bool _tokenValidationInProgress;

    private sealed record WizardStep(
        string Title,
        string Instruction,
        string? ImageFile = null,
        WizardStepType Type = WizardStepType.Instruction);

    private enum WizardStepType
    {
        Welcome,
        Instruction,
        Token,
        Install,
        Finish
    }

    public string VerifiedToken { get; private set; } =
        string.Empty;

    public DiscordSetupWizard()
    {
        InitializeComponent();

        _steps =
            BuildSteps();

        _currentStep =
            0;

        UpdateStep();
    }

    private static List<WizardStep> BuildSteps()
    {
        return
        [
            new(
                "Welcome to Discord Setup",
                "Zelvik will walk you through creating a Discord bot, obtaining its token, verifying the token, and installing the bot into your server.",
                Type: WizardStepType.Welcome),

            new(
                "Create an Application",
                "Open the Discord Developer Portal and create a new application for Zelvik.",
                "01_create_application.png"),

            new(
                "Build the Bot",
                "Open the Bot section for your new application.",
                "02_build_bot.png"),

            new(
                "Create the Application",
                "Give your Discord application a name and complete the initial application setup.",
                "03_create_app.png"),

            new(
                "Reset the Bot Token",
                "In the Bot section, reset the token so Discord generates a fresh token for Zelvik.",
                "04_reset_token.png"),

            new(
                "Confirm Token Reset",
                "Confirm that you want to reset the bot token.",
                "05_confirm_reset_token.png"),

            new(
                "Complete MFA Verification",
                "Discord may require multi-factor authentication before allowing the token to be reset.",
                "06_mfa_verification.png"),

            new(
                "Copy Your Bot Token",
                "Copy the newly generated bot token. Keep this token private. Anyone who has it can control your bot.",
                "07_copy_token.png"),

            new(
                "Enter Your Bot Token",
                "Paste the bot token below. Zelvik will verify it with Discord before allowing you to continue.",
                Type: WizardStepType.Token),

            new(
                "Configure Installation",
                "Discord's installation settings determine how the Zelvik bot can be added to servers.",
                "08_installation_defaults.png"),

            new(
                "Enable Guild Installation",
                "Make sure guild/server installation is enabled for the application.",
                "09_guild_install_only.png"),

            new(
                "Enable the Bot Scope",
                "Select the bot scope when configuring the installation options.",
                "10_select_bot_scope.png"),

            new(
                "Configure Permissions",
                "Zelvik requires View Channels, Connect, and Speak permissions so it can join voice channels and transmit audio.",
                "11_permissions_configured.png"),

            new(
                "Install Zelvik",
                "The token has been verified. Use the button below to open Discord and add Zelvik to your server.",
                Type: WizardStepType.Install),

            new(
                "Open the Discord App",
                "Discord will open the application installation flow.",
                "12_discord_app_launch.png"),

            new(
                "Select Your Server",
                "Choose the Discord server where you want Zelvik installed and authorize the requested permissions.",
                "13_select_server.png"),

            new(
                "Discord Setup Complete",
                "Zelvik has been configured for Discord. Your verified bot token has been stored securely using Windows Credential Manager.",
                Type: WizardStepType.Finish)
        ];
    }

    private void UpdateStep()
    {
        if (_currentStep < 0)
            _currentStep = 0;

        if (_currentStep >= _steps.Count)
            _currentStep = _steps.Count - 1;

        WizardStep step =
            _steps[_currentStep];

        TitleText.Text =
            step.Title;

        InstructionText.Text =
            step.Instruction;

        StepCounterText.Text =
            $"Step {_currentStep + 1} of {_steps.Count}";

        WelcomePanel.Visibility =
            step.Type == WizardStepType.Welcome
                ? Visibility.Visible
                : Visibility.Collapsed;

        TokenPanel.Visibility =
            step.Type == WizardStepType.Token
                ? Visibility.Visible
                : Visibility.Collapsed;

        InstallPanel.Visibility =
            step.Type == WizardStepType.Install
                ? Visibility.Visible
                : Visibility.Collapsed;

        FinishPanel.Visibility =
            step.Type == WizardStepType.Finish
                ? Visibility.Visible
                : Visibility.Collapsed;

        bool hasImage =
            !string.IsNullOrWhiteSpace(step.ImageFile);

        StepImageBorder.Visibility =
            hasImage
                ? Visibility.Visible
                : Visibility.Collapsed;

        StepImage.Visibility =
            hasImage
                ? Visibility.Visible
                : Visibility.Collapsed;

        if (hasImage)
        {
            LoadStepImage(
                step.ImageFile!);
        }
        else
        {
            StepImage.Source =
                null;
        }

        if (step.Type == WizardStepType.Token)
        {
            LoadStoredToken();
        }

        UpdateNavigation();
    }

    private void LoadStepImage(
        string fileName)
    {
        try
        {
            string path =
                Path.Combine(
                    AppContext.BaseDirectory,
                    "Assets",
                    "DiscordSetup",
                    fileName);

            if (!File.Exists(path))
            {
                StepImage.Source =
                    null;

                return;
            }

            var image =
                new BitmapImage();

            image.BeginInit();
            image.UriSource =
                new Uri(
                    path,
                    UriKind.Absolute);

            image.CacheOption =
                BitmapCacheOption.OnLoad;

            image.EndInit();

            StepImage.Source =
                image;
        }
        catch
        {
            StepImage.Source =
                null;
        }
    }

    private void LoadStoredToken()
    {
        if (_tokenValidationInProgress)
            return;

        try
        {
            string? token =
                _credentialStore.ReadToken();

            BotTokenPasswordBox.Password =
                token ?? string.Empty;

            BotTokenTextBox.Text =
                token ?? string.Empty;

            InvalidateTokenValidation();
        }
        catch
        {
            BotTokenPasswordBox.Password =
                string.Empty;

            BotTokenTextBox.Text =
                string.Empty;

            InvalidateTokenValidation();
        }
    }

    private string GetToken()
    {
        return
            ShowTokenCheckBox.IsChecked == true
                ? BotTokenTextBox.Text.Trim()
                : BotTokenPasswordBox.Password.Trim();
    }

    private void SetToken(
        string token)
    {
        BotTokenPasswordBox.Password =
            token;

        BotTokenTextBox.Text =
            token;
    }

    private void InvalidateTokenValidation()
    {
        _validatedToken =
            string.Empty;

        _validatedBotId =
            null;

        _validatedBotName =
            string.Empty;

        VerifiedToken =
            string.Empty;

        SaveTokenButton.IsEnabled =
            false;

        TokenStatusText.Text =
            string.Empty;

        NextButton.IsEnabled =
            false;
    }

    private void UpdateNavigation()
    {
        BackButton.IsEnabled =
            _currentStep > 0
            && !_tokenValidationInProgress;

        CancelButton.IsEnabled =
            !_tokenValidationInProgress;

        if (_currentStep ==
            _steps.Count - 1)
        {
            NextButton.Content =
                "Finish";

            NextButton.IsEnabled =
                !_tokenValidationInProgress;
        }
        else
        {
            NextButton.Content =
                "Next";

            NextButton.IsEnabled =
                CanAdvance();
        }
    }

    private bool CanAdvance()
    {
        WizardStep step =
            _steps[_currentStep];

        if (step.Type == WizardStepType.Token)
        {
            return
                !string.IsNullOrWhiteSpace(
                    _validatedToken)
                && _validatedBotId.HasValue;
        }

        if (step.Type == WizardStepType.Install)
        {
            return
                _validatedBotId.HasValue;
        }

        return true;
    }

    private async void TestTokenButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_tokenValidationInProgress)
            return;

        string token =
            GetToken();

        if (string.IsNullOrWhiteSpace(token))
        {
            TokenStatusText.Text =
                "Enter or paste your Discord bot token first.";

            SaveTokenButton.IsEnabled =
                false;

            return;
        }

        _tokenValidationInProgress =
            true;

        UpdateNavigation();

        TestTokenButton.IsEnabled =
            false;

        SaveTokenButton.IsEnabled =
            false;

        TokenStatusText.Text =
            "Connecting to Discord...";

        try
        {
            DiscordTokenValidationResult result =
                await _discordSetupService
                    .ValidateTokenAsync(
                        token);

            if (!result.Valid)
            {
                InvalidateTokenValidation();

                TokenStatusText.Text =
                    result.Error;

                return;
            }

            _validatedToken =
                token;

            _validatedBotId =
                result.BotId;

            _validatedBotName =
                result.BotName;

            TokenStatusText.Text =
                $"Token verified successfully.\n\n" +
                $"Bot: {_validatedBotName}\n" +
                $"Bot ID: {_validatedBotId}";

            SaveTokenButton.IsEnabled =
                true;

            VerifiedToken =
                token;
        }
        catch (Exception ex)
        {
            InvalidateTokenValidation();

            TokenStatusText.Text =
                "Zelvik could not verify the token.\n\n" +
                $"{ex.GetType().Name}: {ex.Message}";
        }
        finally
        {
            _tokenValidationInProgress =
                false;

            TestTokenButton.IsEnabled =
                true;

            UpdateNavigation();
        }
    }

    private void SaveTokenButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(
                _validatedToken))
        {
            TokenStatusText.Text =
                "Verify the Discord token before saving it.";

            return;
        }

        try
        {
            _credentialStore.SaveToken(
                _validatedToken);

            VerifiedToken =
                _validatedToken;

            TokenStatusText.Text =
                $"Token verified and saved securely.\n\n" +
                $"Bot: {_validatedBotName}\n" +
                $"Bot ID: {_validatedBotId}";

            SaveTokenButton.IsEnabled =
                false;
        }
        catch (Exception ex)
        {
            TokenStatusText.Text =
                "The token was verified, but Zelvik could not save it to Windows Credential Manager.\n\n" +
                $"{ex.GetType().Name}: {ex.Message}";
        }
    }

    private void PasteTokenButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            if (Clipboard.ContainsText())
            {
                string token =
                    Clipboard.GetText().Trim();

                SetToken(token);

                InvalidateTokenValidation();

                TokenStatusText.Text =
                    "Token pasted. Click Test Connection to verify it.";
            }
        }
        catch (Exception ex)
        {
            TokenStatusText.Text =
                "Zelvik could not read the clipboard.\n\n" +
                ex.Message;
        }
    }

    private void ShowTokenCheckBox_Checked(
        object sender,
        RoutedEventArgs e)
    {
        string token =
            GetToken();

        BotTokenTextBox.Text =
            token;

        BotTokenPasswordBox.Visibility =
            Visibility.Collapsed;

        BotTokenTextBox.Visibility =
            Visibility.Visible;
    }

    private void ShowTokenCheckBox_Unchecked(
        object sender,
        RoutedEventArgs e)
    {
        string token =
            GetToken();

        BotTokenPasswordBox.Password =
            token;

        BotTokenTextBox.Visibility =
            Visibility.Collapsed;

        BotTokenPasswordBox.Visibility =
            Visibility.Visible;
    }

    private void OpenDeveloperPortalButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        OpenUrl(
            "https://discord.com/developers/applications");
    }

    private void InstallBotButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (!_validatedBotId.HasValue)
        {
            TokenStatusText.Text =
                "Verify the bot token before installing Zelvik.";

            return;
        }

        string url =
            _discordSetupService
                .BuildBotInstallUrl(
                    _validatedBotId.Value);

        OpenUrl(url);
    }

    private void BackButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_tokenValidationInProgress)
            return;

        if (_currentStep > 0)
        {
            _currentStep--;

            UpdateStep();
        }
    }

    private void NextButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_tokenValidationInProgress)
            return;

        WizardStep step =
            _steps[_currentStep];

        if (step.Type == WizardStepType.Token)
        {
            if (string.IsNullOrWhiteSpace(
                    _validatedToken))
            {
                TokenStatusText.Text =
                    "Verify your Discord bot token before continuing.";

                return;
            }

            if (!string.IsNullOrWhiteSpace(
                    _validatedToken)
                && !string.Equals(
                    GetToken(),
                    _validatedToken,
                    StringComparison.Ordinal))
            {
                InvalidateTokenValidation();

                TokenStatusText.Text =
                    "The token changed. Test the new token before continuing.";

                return;
            }

            if (!string.IsNullOrWhiteSpace(
                    _validatedToken))
            {
                try
                {
                    _credentialStore.SaveToken(
                        _validatedToken);

                    VerifiedToken =
                        _validatedToken;
                }
                catch (Exception ex)
                {
                    TokenStatusText.Text =
                        "The token was verified, but Zelvik could not save it securely.\n\n" +
                        $"{ex.GetType().Name}: {ex.Message}";

                    return;
                }
            }
        }

        if (_currentStep >=
            _steps.Count - 1)
        {
            DialogResult =
                true;

            Close();

            return;
        }

        _currentStep++;

        UpdateStep();
    }

    private void CancelButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        DialogResult =
            false;

        Close();
    }

    private static void OpenUrl(
        string url)
    {
        try
        {
            Process.Start(
                new ProcessStartInfo
                {
                    FileName =
                        url,
                    UseShellExecute =
                        true
                });
        }
        catch
        {
            // Browser launch failures should not crash
            // the setup wizard.
        }
    }
}
