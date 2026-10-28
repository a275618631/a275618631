using System.Security.Cryptography;
using System.Text;

namespace EnterpriseOperationsPlatform.Api.Security;

public sealed class DemoAuthOptions
{
    public bool Enabled { get; set; }

    public List<DemoAuthUser> Users { get; set; } = [];

    public DemoAuthUser? Authenticate(string username, string password)
    {
        var user = Users.FirstOrDefault(item =>
            string.Equals(item.Username, username.Trim(), StringComparison.OrdinalIgnoreCase));
        if (user is null)
            return null;

        var expected = Encoding.UTF8.GetBytes(user.Password);
        var actual = Encoding.UTF8.GetBytes(password);
        return CryptographicOperations.FixedTimeEquals(expected, actual) ? user : null;
    }
}

public sealed class DemoAuthUser
{
    public string Username { get; set; } = string.Empty;

    public string Password { get; set; } = string.Empty;

    public string Role { get; set; } = string.Empty;
}

public sealed record DemoLoginRequest(string Username, string Password);

public sealed record DemoLoginResponse(string AccessToken, string Username, string Role, int ExpiresInSeconds);
