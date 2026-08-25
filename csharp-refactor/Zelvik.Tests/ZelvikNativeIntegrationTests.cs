using Xunit;
using Zelvik.Core.Native;

namespace Zelvik.Tests;

public sealed class ZelvikNativeIntegrationTests
{
    [Fact]
    public void GetVersion_ReturnsExpectedNativeVersion()
    {
        var version = ZelvikNative.GetVersion();

        Assert.Equal(1, version);
    }
}