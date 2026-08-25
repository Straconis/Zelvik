using Zelvik.YouTube;
using Xunit;
namespace Zelvik.Tests;

public sealed class YtDlpServiceTests
{
    private const string ControlVideoUrl =
        "https://www.youtube.com/shorts/BLbtr0Esl-Q";

    [Fact]
    public async Task ResolveStreamAsync_PublicVideo_ReturnsStreamUrl()
    {
        var service =
            new YtDlpService();

        var result =
            await service.ResolveStreamAsync(
                ControlVideoUrl);

        Assert.True(
            result.Success,
            $"yt-dlp failed.\nExit code: {result.ExitCode}\n" +
            $"STDERR:\n{result.StandardError}");

        Assert.NotEmpty(
            result.StreamUrls);

        Assert.All(
            result.StreamUrls,
            url =>
            {
                Assert.True(
                    Uri.TryCreate(
                        url,
                        UriKind.Absolute,
                        out _),
                    $"Invalid stream URL returned: {url}");
            });
    }

    [Fact]
    public async Task ResolveStreamAsync_EmptyUrl_Throws()
    {
        var service =
            new YtDlpService();

        await Assert.ThrowsAsync<ArgumentException>(
            () =>
                service.ResolveStreamAsync(
                    string.Empty));
    }

    [Fact]
    public async Task ResolveStreamAsync_InvalidVideo_FailsGracefully()
    {
        var service =
            new YtDlpService();

        var result =
            await service.ResolveStreamAsync(
                "https://www.youtube.com/watch?v=THIS_IS_NOT_REAL");

        Assert.False(
            result.Success);

        Assert.NotEqual(
            0,
            result.ExitCode);
    }
}