using System.Net;
using System.Text.Json;
using Xunit;

namespace Zelvik.Tests;

public sealed class YouTubeApiIntegrationTests
{
    private const string ControlVideoId =
        "BLbtr0Esl-Q";

    [Fact]
    public async Task YouTubeDataApi_ValidKey_ReturnsVideoMetadata()
    {
        string apiKey =
            Environment.GetEnvironmentVariable(
                "ZELVIK_YOUTUBE_API_KEY")
            ?? string.Empty;

        Assert.False(
            string.IsNullOrWhiteSpace(apiKey),
            "Set ZELVIK_YOUTUBE_API_KEY before running this integration test.");

        using var client =
            new HttpClient();

        string requestUrl =
            "https://www.googleapis.com/youtube/v3/videos" +
            "?part=snippet" +
            $"&id={Uri.EscapeDataString(ControlVideoId)}" +
            $"&key={Uri.EscapeDataString(apiKey)}";

        using HttpResponseMessage response =
            await client.GetAsync(requestUrl);

        string responseBody =
            await response.Content.ReadAsStringAsync();

        Assert.True(
            response.StatusCode == HttpStatusCode.OK,
            $"YouTube Data API request failed.\n" +
            $"HTTP status: {(int)response.StatusCode} " +
            $"{response.StatusCode}\n" +
            $"Response:\n{responseBody}");

        using JsonDocument document =
            JsonDocument.Parse(responseBody);

        JsonElement root =
            document.RootElement;

        Assert.True(
            root.TryGetProperty(
                "items",
                out JsonElement items),
            "YouTube response did not contain an items array.");

        Assert.Equal(
            JsonValueKind.Array,
            items.ValueKind);

        Assert.True(
            items.GetArrayLength() > 0,
            "YouTube returned no metadata for the control video.");

        JsonElement video =
            items[0];

        Assert.Equal(
            ControlVideoId,
            video.GetProperty("id").GetString());

        JsonElement snippet =
            video.GetProperty("snippet");

        string? title =
            snippet.GetProperty("title").GetString();

        string? channelTitle =
            snippet.GetProperty("channelTitle").GetString();

        Assert.False(
            string.IsNullOrWhiteSpace(title),
            "YouTube returned an empty video title.");

        Assert.False(
            string.IsNullOrWhiteSpace(channelTitle),
            "YouTube returned an empty channel title.");
    }
}