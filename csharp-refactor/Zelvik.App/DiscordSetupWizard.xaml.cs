using System.Windows;

namespace Zelvik.App;

public partial class DiscordSetupWizard : Window
{
    private int _currentStep;

    public string VerifiedToken { get; private set; } =
        string.Empty;

    public DiscordSetupWizard()
    {
        InitializeComponent();

        UpdateNavigation();
    }

    private void CancelButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        DialogResult =
            false;

        Close();
    }

    private void BackButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_currentStep > 0)
        {
            _currentStep--;

            UpdateNavigation();
        }
    }

    private void NextButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        _currentStep++;

        UpdateNavigation();
    }

    private void FinishButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        VerifiedToken =
            BotTokenPasswordBox.Password.Trim();

        DialogResult =
            true;

        Close();
    }

    private void UpdateNavigation()
    {
        BackButton.IsEnabled =
            _currentStep > 0;

        StepCounterText.Text =
            $"Step {_currentStep + 1}";
    }
}
