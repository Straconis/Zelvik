using System.Globalization;
using System.IO;
using Microsoft.Web.WebView2.Core;

namespace Zelvik.App;

/// <summary>
/// Converts cookies from Zelvik's private WebView2 YouTube profile
/// into the Netscape cookie-file format understood by yt-dlp.
/// </summary>
public sealed class YouTubeCookieService
{
    private static readonly string[] CookieSources =
    {
        "https://www.youtube.com/",
        "https://accounts.google.com/",
        "https://google.com/"
    };

    /// <summary>
    /// Creates a temporary yt-dlp-compatible cookie file from
    /// Zelvik's WebView2 browser session.
    ///
    /// The caller is responsible for deleting the returned file
    /// when yt-dlp has finished using it.
    /// </summary>
    public async Task<string> CreateTemporaryCookieFileAsync(
        CoreWebView2CookieManager cookieManager)
    {
        ArgumentNullException.ThrowIfNull(
            cookieManager);

        var cookies =
            await GetAuthenticationCookiesAsync(
                cookieManager);

        if (cookies.Count == 0)
        {
            throw new InvalidOperationException(
                "No YouTube authentication cookies were found. " +
                "Sign in to YouTube through Zelvik first.");
        }

        string directory =
            Path.Combine(
                Path.GetTempPath(),
                "Zelvik",
                "YouTube");

        Directory.CreateDirectory(
            directory);

        string filePath =
            Path.Combine(
                directory,
                $"youtube-cookies-{Guid.NewGuid():N}.txt");

        await WriteNetscapeCookieFileAsync(
            filePath,
            cookies);

        return filePath;
    }

    /// <summary>
    /// Deletes a temporary cookie file created by this service.
    /// Failure to delete is intentionally ignored so cleanup
    /// cannot crash Zelvik.
    /// </summary>
    public void DeleteTemporaryCookieFile(
        string? filePath)
    {
        if (string.IsNullOrWhiteSpace(
                filePath))
        {
            return;
        }

        try
        {
            if (File.Exists(
                    filePath))
            {
                File.Delete(
                    filePath);
            }
        }
        catch
        {
            // Best-effort cleanup.
        }
    }

    /// <summary>
    /// Checks whether the WebView2 profile appears to contain
    /// an authenticated YouTube session.
    /// </summary>
    public async Task<bool> IsSignedInAsync(
        CoreWebView2CookieManager cookieManager)
    {
        ArgumentNullException.ThrowIfNull(
            cookieManager);

        var cookies =
            await cookieManager.GetCookiesAsync(
                "https://www.youtube.com/");

        return cookies.Any(
            IsAuthenticationCookie);
    }

    private static async Task<List<CoreWebView2Cookie>>
        GetAuthenticationCookiesAsync(
            CoreWebView2CookieManager cookieManager)
    {
        var cookiesByKey =
            new Dictionary<string, CoreWebView2Cookie>(
                StringComparer.Ordinal);

        foreach (string source
                 in CookieSources)
        {
            var cookies =
                await cookieManager.GetCookiesAsync(
                    source);

            foreach (var cookie
                     in cookies)
            {
                if (!IsRelevantDomain(
                        cookie.Domain))
                {
                    continue;
                }

                string key =
                    $"{cookie.Domain}\t" +
                    $"{cookie.Path}\t" +
                    $"{cookie.Name}";

                cookiesByKey[key] =
                    cookie;
            }
        }

        return cookiesByKey
            .Values
            .ToList();
    }

    private static bool IsRelevantDomain(
        string domain)
    {
        string normalized =
            domain.TrimStart('.');

        return normalized.Equals(
                   "youtube.com",
                   StringComparison.OrdinalIgnoreCase)
               ||
               normalized.EndsWith(
                   ".youtube.com",
                   StringComparison.OrdinalIgnoreCase)
               ||
               normalized.Equals(
                   "google.com",
                   StringComparison.OrdinalIgnoreCase)
               ||
               normalized.EndsWith(
                   ".google.com",
                   StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsAuthenticationCookie(
        CoreWebView2Cookie cookie)
    {
        return cookie.Name.Equals(
                   "SAPISID",
                   StringComparison.OrdinalIgnoreCase)
               ||
               cookie.Name.Equals(
                   "APISID",
                   StringComparison.OrdinalIgnoreCase)
               ||
               cookie.Name.Equals(
                   "SID",
                   StringComparison.OrdinalIgnoreCase)
               ||
               cookie.Name.Equals(
                   "__Secure-1PSID",
                   StringComparison.OrdinalIgnoreCase)
               ||
               cookie.Name.Equals(
                   "__Secure-3PSID",
                   StringComparison.OrdinalIgnoreCase);
    }

    private static async Task WriteNetscapeCookieFileAsync(
        string filePath,
        IReadOnlyCollection<CoreWebView2Cookie> cookies)
    {
        await using var stream =
            new FileStream(
                filePath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None);

        await using var writer =
            new StreamWriter(
                stream);

        await writer.WriteLineAsync(
            "# Netscape HTTP Cookie File");

        await writer.WriteLineAsync(
            "# Generated temporarily by Zelvik for yt-dlp.");

        await writer.WriteLineAsync(
            "# This file should be deleted after use.");

        foreach (var cookie
                 in cookies)
        {
            string domain =
                NormalizeDomain(
                    cookie.Domain);

            string includeSubdomains =
                domain.StartsWith(
                    ".",
                    StringComparison.Ordinal)
                    ? "TRUE"
                    : "FALSE";

            string path =
                string.IsNullOrWhiteSpace(
                    cookie.Path)
                    ? "/"
                    : cookie.Path;

            string secure =
                cookie.IsSecure
                    ? "TRUE"
                    : "FALSE";

            string expiration =
                GetUnixExpiration(
                    cookie);

            string outputDomain =
                cookie.IsHttpOnly
                    ? $"#HttpOnly_{domain}"
                    : domain;

            string line =
                string.Join(
                    '\t',
                    outputDomain,
                    includeSubdomains,
                    path,
                    secure,
                    expiration,
                    SanitizeField(cookie.Name),
                    SanitizeField(cookie.Value));

            await writer.WriteLineAsync(
                line);
        }
    }

    private static string NormalizeDomain(
        string domain)
    {
        if (string.IsNullOrWhiteSpace(
                domain))
        {
            return ".youtube.com";
        }

        string normalized =
            domain.Trim();

        if (!normalized.StartsWith(
                ".",
                StringComparison.Ordinal))
        {
            normalized =
                "." + normalized;
        }

        return normalized;
    }

    private static string GetUnixExpiration(
        CoreWebView2Cookie cookie)
    {
        if (cookie.IsSession)
        {
            return "0";
        }

        DateTime expiration =
            cookie.Expires;

        if (expiration == DateTime.MinValue)
        {
            return "0";
        }

        DateTimeOffset expirationOffset =
            new(
                expiration.ToUniversalTime());

        long unixTime =
            expirationOffset.ToUnixTimeSeconds();

        return unixTime.ToString(
            CultureInfo.InvariantCulture);
    }

    private static string SanitizeField(
        string value)
    {
        return value
            .Replace(
                "\t",
                string.Empty)
            .Replace(
                "\r",
                string.Empty)
            .Replace(
                "\n",
                string.Empty);
    }
}