using Discord;
using Discord.WebSocket;

namespace Zelvik.Discord;

public sealed class DiscordTokenValidationResult
{
    public bool Valid { get; init; }

    public string BotName { get; init; } =
        string.Empty;

    public ulong? BotId { get; init; }

    public string Error { get; init; } =
        string.Empty;
}

public sealed class DiscordSetupService
{
    public async Task<DiscordTokenValidationResult> ValidateTokenAsync(
        string token,
        CancellationToken cancellationToken = default)
    {
        token =
            (token ?? string.Empty).Trim();

        if (string.IsNullOrWhiteSpace(token))
        {
            return new DiscordTokenValidationResult
            {
                Valid =
                    false,

                Error =
                    "Enter a Discord bot token first."
            };
        }

        var config =
            new DiscordSocketConfig
            {
                GatewayIntents =
                    GatewayIntents.None,

                LogLevel =
                    LogSeverity.Warning
            };

        using var client =
            new DiscordSocketClient(
                config);

        using var timeout =
            CancellationTokenSource
                .CreateLinkedTokenSource(
                    cancellationToken);

        timeout.CancelAfter(
            TimeSpan.FromSeconds(15));

        try
        {
            await client.LoginAsync(
                TokenType.Bot,
                token);

            await client.StartAsync();

            while (client.CurrentUser is null)
            {
                timeout.Token
                    .ThrowIfCancellationRequested();

                await Task.Delay(
                    100,
                    timeout.Token);
            }

            return new DiscordTokenValidationResult
            {
                Valid =
                    true,

                BotName =
                    client.CurrentUser.ToString(),

                BotId =
                    client.CurrentUser.Id
            };
        }
        catch (OperationCanceledException)
        {
            return new DiscordTokenValidationResult
            {
                Valid =
                    false,

                Error =
                    "Discord did not respond in time. Check your internet connection and try again."
            };
        }
        catch (global::Discord.Net.HttpException ex)
        {
            return new DiscordTokenValidationResult
            {
                Valid =
                    false,

                Error =
                    "Discord rejected this token. Make sure you copied the Bot Token and try again.\n\n" +
                    ex.Message
            };
        }
        catch (Exception ex)
        {
            return new DiscordTokenValidationResult
            {
                Valid =
                    false,

                Error =
                    "Zelvik could not verify the token.\n\n" +
                    $"{ex.GetType().Name}: {ex.Message}"
            };
        }
        finally
        {
            try
            {
                await client.StopAsync();
            }
            catch
            {
            }

            try
            {
                await client.LogoutAsync();
            }
            catch
            {
            }
        }
    }

    public string BuildBotInstallUrl(
        ulong botId)
    {
        const ulong viewChannels =
            1UL << 10;

        const ulong connect =
            1UL << 20;

        const ulong speak =
            1UL << 21;

        ulong permissions =
            viewChannels
            | connect
            | speak;

        return
            "https://discord.com/oauth2/authorize"
            + $"?client_id={botId}"
            + "&scope=bot%20applications.commands"
            + $"&permissions={permissions}";
    }
}

