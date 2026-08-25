using System.Diagnostics;
using Xunit;

namespace Zelvik.Tests;

public sealed class YtDlpAuthenticatedIntegrationTests
{
    private const string ControlVideoUrl =
        "https://www.youtube.com/shorts/BLbtr0Esl-Q";

    [Fact]
    public async Task DownloadControlAudio_ToFile_ProducesMediaFile()
    {
        string cookieFile =
            Environment.GetEnvironmentVariable(
                "ZELVIK_TEST_COOKIE_FILE")
            ?? string.Empty;

        Assert.False(
            string.IsNullOrWhiteSpace(cookieFile),
            "Set ZELVIK_TEST_COOKIE_FILE to a Zelvik-generated cookie file.");

        Assert.True(
            File.Exists(cookieFile),
            $"Cookie file does not exist: {cookieFile}");

        string outputDirectory =
            @"D:\ZelvikTemp\MediaTest";

        if (!Directory.Exists(@"D:\ZelvikTemp"))
        {
            outputDirectory =
                Path.Combine(
                    Path.GetTempPath(),
                    "Zelvik",
                    "MediaTest");
        }

        Directory.CreateDirectory(
            outputDirectory);

        string mediaId =
            $"zelvik-youtube-test-{Guid.NewGuid():N}";

        /*
         * IMPORTANT:
         *
         * Do not force WebM.
         *
         * Production Zelvik now allows yt-dlp to choose
         * whichever audio format YouTube makes available.
         */
        string outputTemplate =
            Path.Combine(
                outputDirectory,
                mediaId + ".%(ext)s");

        var startInfo =
            new ProcessStartInfo
            {
                FileName = "yt-dlp",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

        startInfo.ArgumentList.Add(
            "--no-playlist");

        startInfo.ArgumentList.Add(
            "--no-progress");

        startInfo.ArgumentList.Add(
            "-v");

        startInfo.ArgumentList.Add(
            "-f");

        startInfo.ArgumentList.Add(
            "bestaudio/best");

        startInfo.ArgumentList.Add(
            "-o");

        startInfo.ArgumentList.Add(
            outputTemplate);

        startInfo.ArgumentList.Add(
            "--cookies");

        startInfo.ArgumentList.Add(
            cookieFile);

        startInfo.ArgumentList.Add(
            ControlVideoUrl);

        using var process =
            new Process
            {
                StartInfo = startInfo
            };

        Assert.True(
            process.Start(),
            "Could not start yt-dlp.");

        Task<string> stdoutTask =
            process.StandardOutput.ReadToEndAsync();

        Task<string> stderrTask =
            process.StandardError.ReadToEndAsync();

        await process.WaitForExitAsync();

        string stdout =
            await stdoutTask;

        string stderr =
            await stderrTask;

        string? downloadedFile =
            Directory
                .EnumerateFiles(
                    outputDirectory,
                    mediaId + ".*",
                    SearchOption.TopDirectoryOnly)
                .Where(
                    path =>
                    {
                        string extension =
                            Path.GetExtension(path);

                        return !extension.Equals(
                                   ".part",
                                   StringComparison.OrdinalIgnoreCase)
                               &&
                               !extension.Equals(
                                   ".ytdl",
                                   StringComparison.OrdinalIgnoreCase);
                    })
                .OrderByDescending(
                    path =>
                    {
                        try
                        {
                            return new FileInfo(path).Length;
                        }
                        catch
                        {
                            return 0;
                        }
                    })
                .FirstOrDefault();

        try
        {
            Assert.True(
                process.ExitCode == 0,
                "yt-dlp media download failed.\n\n" +
                $"Exit code: {process.ExitCode}\n\n" +
                $"STDOUT:\n{stdout}\n\n" +
                $"STDERR:\n{stderr}");

            Assert.False(
                string.IsNullOrWhiteSpace(downloadedFile),
                "yt-dlp exited successfully but no media file was produced.");

            Assert.True(
                File.Exists(downloadedFile),
                $"Downloaded media file does not exist: {downloadedFile}");

            var fileInfo =
                new FileInfo(
                    downloadedFile!);

            Assert.True(
                fileInfo.Length > 1024,
                $"Downloaded media file is suspiciously small: {fileInfo.Length} bytes");

            Console.WriteLine(
                $"Downloaded file: {downloadedFile}");

            Console.WriteLine(
                $"Size: {fileInfo.Length} bytes");

            Console.WriteLine(
                $"Extension: {fileInfo.Extension}");

            Console.WriteLine(
                "yt-dlp stdout:");

            Console.WriteLine(
                stdout);

            Console.WriteLine(
                "yt-dlp stderr:");

            Console.WriteLine(
                stderr);
        }
        finally
        {
            /*
             * Remove everything created for this test,
             * including any partial yt-dlp files.
             */
            foreach (
                string file
                in Directory.EnumerateFiles(
                    outputDirectory,
                    mediaId + ".*",
                    SearchOption.TopDirectoryOnly))
            {
                try
                {
                    File.Delete(file);
                }
                catch
                {
                    // Best-effort test cleanup.
                }
            }
        }
    }
}