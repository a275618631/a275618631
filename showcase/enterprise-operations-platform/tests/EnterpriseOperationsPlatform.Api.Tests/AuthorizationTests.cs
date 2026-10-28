using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Text.Encodings.Web;
using System.Text;
using EnterpriseOperationsPlatform.Api.Operations;
using EnterpriseOperationsPlatform.Api.Security;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;

namespace EnterpriseOperationsPlatform.Api.Tests;

public sealed class AuthorizationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public AuthorizationTests(WebApplicationFactory<Program> factory) => _factory = factory;

    [Fact]
    public async Task UnauthenticatedOperationsRequest_Returns401()
    {
        using var client = CreateClient();

        var response = await client.GetAsync("/api/operations/equipment");

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task UnauthenticatedEquipmentCreate_Returns401()
    {
        using var client = CreateClient();

        var response = await client.PostAsJsonAsync("/api/operations/equipment", new
        {
            id = "EQ-NEW-401",
            name = "新設備",
            area = "一樓"
        });

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task JwtBearerWithoutRuntimeConfiguration_Returns401()
    {
        using var client = _factory.CreateClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", TestJwt.Create(OperationsAuthorization.Viewer));

        var response = await client.GetAsync("/api/operations/equipment");

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task ViewerCannotCreateWorkOrder_Returns403()
    {
        using var client = CreateClient(OperationsAuthorization.Viewer);

        var response = await client.PostAsJsonAsync("/api/operations/work-orders", new
        {
            equipmentId = "EQ-100",
            title = "檢查馬達振動",
            priority = "Normal"
        });

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    [Fact]
    public async Task ViewerCannotCreateEquipment_Returns403()
    {
        using var client = CreateClient(OperationsAuthorization.Viewer);

        var response = await client.PostAsJsonAsync("/api/operations/equipment", new
        {
            id = "EQ-NEW-403",
            name = "新設備",
            area = "一樓"
        });

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    [Fact]
    public async Task OperatorCanCreateEquipmentAndUseItForWorkOrder()
    {
        using var client = CreateClient(OperationsAuthorization.Operator);
        var equipmentId = $"EQ-{Guid.NewGuid():N}"[..32];

        var response = await client.PostAsJsonAsync("/api/operations/equipment", new
        {
            id = equipmentId.ToLowerInvariant(),
            name = " 新增設備測試機 ",
            area = " 測試區 ",
            status = "attention"
        });

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var equipment = await response.Content.ReadFromJsonAsync<CreatedEquipment>();
        Assert.NotNull(equipment);
        Assert.Equal(equipmentId.ToUpperInvariant(), equipment.Id);
        Assert.Equal("新增設備測試機", equipment.Name);
        Assert.Equal("測試區", equipment.Area);
        Assert.Equal("Attention", equipment.Status);

        var workOrderResponse = await client.PostAsJsonAsync("/api/operations/work-orders", new
        {
            equipmentId,
            title = "新增設備工單驗證",
            priority = "Normal"
        });
        Assert.Equal(HttpStatusCode.Created, workOrderResponse.StatusCode);
    }

    [Fact]
    public async Task DuplicateEquipmentId_Returns409()
    {
        using var client = CreateClient(OperationsAuthorization.Operator);
        var response = await client.PostAsJsonAsync("/api/operations/equipment", new
        {
            id = " eq-100 ",
            name = "重複設備",
            area = "測試區"
        });

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
    }

    [Fact]
    public async Task InvalidEquipmentRequest_Returns400ValidationProblem()
    {
        using var client = CreateClient(OperationsAuthorization.Operator);
        var response = await client.PostAsJsonAsync("/api/operations/equipment", new
        {
            id = "INVALID ID",
            name = " ",
            area = "測試區",
            status = "Unknown"
        });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemResponse>();
        Assert.NotNull(problem);
        Assert.Contains("id", problem.Errors.Keys);
        Assert.Contains("name", problem.Errors.Keys);
        Assert.Contains("status", problem.Errors.Keys);
    }

    [Fact]
    public async Task InvalidWorkOrderRequest_Returns400ValidationProblem()
    {
        using var client = CreateClient(OperationsAuthorization.Operator);

        var response = await client.PostAsJsonAsync("/api/operations/work-orders", new
        {
            equipmentId = "EQ-100",
            title = new string('x', WorkOrderValidation.TitleMaxLength + 1),
            priority = "Normal"
        });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemResponse>();
        Assert.NotNull(problem);
        Assert.Contains("title", problem.Errors.Keys);
    }

    [Fact]
    public async Task OperatorCanCreateAndSupervisorCanCompleteWorkOrder()
    {
        using var operatorClient = CreateClient(OperationsAuthorization.Operator);
        var createResponse = await operatorClient.PostAsJsonAsync("/api/operations/work-orders", new
        {
            equipmentId = "EQ-100",
            title = "角色授權垂直切片測試",
            priority = "High"
        });

        Assert.Equal(HttpStatusCode.Created, createResponse.StatusCode);
        var created = await createResponse.Content.ReadFromJsonAsync<CreatedWorkOrder>();
        Assert.NotNull(created);

        var operatorCompleteResponse = await operatorClient.PostAsync($"/api/operations/work-orders/{created.Id}/complete", null);
        Assert.Equal(HttpStatusCode.Forbidden, operatorCompleteResponse.StatusCode);

        using var supervisorClient = CreateClient(OperationsAuthorization.Supervisor);
        var supervisorCompleteResponse = await supervisorClient.PostAsync($"/api/operations/work-orders/{created.Id}/complete", null);

        Assert.Equal(HttpStatusCode.OK, supervisorCompleteResponse.StatusCode);
    }

    [Fact]
    public async Task ViewerCanReadOperations()
    {
        using var client = CreateClient(OperationsAuthorization.Viewer);

        var response = await client.GetAsync("/api/operations/equipment");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task UnknownRoleCannotReadOperations_Returns403()
    {
        using var client = CreateClient("OperationsUnknown");

        var response = await client.GetAsync("/api/operations/equipment");

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    [Fact]
    public async Task JwtBearerTokenWithSupervisorRoleCanCompleteWorkOrder()
    {
        using var client = CreateJwtClient(OperationsAuthorization.Supervisor);
        using var operatorClient = CreateJwtClient(OperationsAuthorization.Operator);
        var createResponse = await operatorClient.PostAsJsonAsync("/api/operations/work-orders", new
        {
            equipmentId = "EQ-200",
            title = "JWT 角色授權測試",
            priority = "Normal"
        });
        var created = await createResponse.Content.ReadFromJsonAsync<CreatedWorkOrder>();
        Assert.Equal(HttpStatusCode.Created, createResponse.StatusCode);
        Assert.NotNull(created);

        var completeResponse = await client.PostAsync($"/api/operations/work-orders/{created.Id}/complete", null);

        Assert.Equal(HttpStatusCode.OK, completeResponse.StatusCode);
    }

    [Fact]
    public async Task DevelopmentDemoLogin_ReturnsJwtForValidCredentials()
    {
        using var client = CreateDemoClient();

        var response = await client.PostAsJsonAsync("/api/auth/demo-login", new
        {
            username = "operator",
            password = "operator-demo"
        });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var result = await response.Content.ReadFromJsonAsync<DemoLoginResponse>();
        Assert.NotNull(result);
        Assert.False(string.IsNullOrWhiteSpace(result.AccessToken));
        Assert.Equal(OperationsAuthorization.Operator, result.Role);
    }

    [Fact]
    public async Task DevelopmentDemoLogin_InvalidCredentials_Returns401()
    {
        using var client = CreateDemoClient();

        var response = await client.PostAsJsonAsync("/api/auth/demo-login", new
        {
            username = "operator",
            password = "wrong-password"
        });

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task DemoLoginEndpoint_IsNotMappedOutsideDevelopment()
    {
        using var client = _factory.WithWebHostBuilder(builder => builder.UseEnvironment("Production"))
            .CreateClient();

        var response = await client.PostAsJsonAsync("/api/auth/demo-login", new
        {
            username = "operator",
            password = "operator-demo"
        });

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    private HttpClient CreateClient(string? role = null)
    {
        var client = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureTestServices(services =>
            {
                services.AddAuthentication(options =>
                {
                    options.DefaultAuthenticateScheme = TestAuthenticationHandler.Scheme;
                    options.DefaultChallengeScheme = TestAuthenticationHandler.Scheme;
                }).AddScheme<TestAuthenticationOptions, TestAuthenticationHandler>(
                    TestAuthenticationHandler.Scheme,
                    options => options.Role = role);
            });
        }).CreateClient();

        if (role is not null)
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue(TestAuthenticationHandler.Scheme);

        return client;
    }

    private HttpClient CreateJwtClient(string role)
    {
        var client = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureTestServices(services =>
            {
                services.PostConfigure<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme, options =>
                {
                    options.Events = new JwtBearerEvents();
                    options.TokenValidationParameters = new TokenValidationParameters
                    {
                        ValidateIssuerSigningKey = true,
                        IssuerSigningKey = TestJwt.Key,
                        ValidateIssuer = true,
                        ValidIssuer = TestJwt.Issuer,
                        ValidateAudience = true,
                        ValidAudience = TestJwt.Audience,
                        ValidateLifetime = true,
                        RoleClaimType = ClaimTypes.Role
                    };
                });
            });
        }).CreateClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", TestJwt.Create(role));
        return client;
    }

    private HttpClient CreateDemoClient()
    {
        return _factory.WithWebHostBuilder(builder => builder
            .UseEnvironment("Development")
            .ConfigureTestServices(services => services.PostConfigure<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme, options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = TestJwt.Key,
                    ValidateIssuer = true,
                    ValidIssuer = TestJwt.Issuer,
                    ValidateAudience = true,
                    ValidAudience = TestJwt.Audience,
                    ValidateLifetime = true,
                    RoleClaimType = ClaimTypes.Role
                };
            })))
            .CreateClient();
    }

    private sealed record CreatedWorkOrder(Guid Id, string EquipmentId, string Title, string Priority, string Status, DateTimeOffset CreatedAt);
    private sealed record CreatedEquipment(string Id, string Name, string Area, string Status);
    private sealed record ValidationProblemResponse(string? Type, string? Title, int? Status, Dictionary<string, string[]> Errors);
    private sealed record DemoLoginResponse(string AccessToken, string Username, string Role, int ExpiresInSeconds);
}

internal static class TestJwt
{
    public const string Issuer = "enterprise-operations-platform-tests";
    public const string Audience = "enterprise-operations-platform-api";
    public static readonly SymmetricSecurityKey Key = new(Encoding.UTF8.GetBytes("synthetic-test-signing-key-1234567890"));

    public static string Create(string role)
    {
        var token = new JwtSecurityToken(
            issuer: Issuer,
            audience: Audience,
            claims: [new Claim(ClaimTypes.Role, role)],
            expires: DateTime.UtcNow.AddMinutes(5),
            signingCredentials: new SigningCredentials(Key, SecurityAlgorithms.HmacSha256));
        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}

internal sealed class TestAuthenticationOptions : AuthenticationSchemeOptions
{
    public string? Role { get; set; }
}

internal sealed class TestAuthenticationHandler : AuthenticationHandler<TestAuthenticationOptions>
{
    public new const string Scheme = "Test";

    public TestAuthenticationHandler(
        IOptionsMonitor<TestAuthenticationOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder) : base(options, logger, encoder)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.ContainsKey("Authorization") || string.IsNullOrWhiteSpace(Options.Role))
            return Task.FromResult(AuthenticateResult.NoResult());

        var identity = new ClaimsIdentity(
        [
            new Claim(ClaimTypes.NameIdentifier, "synthetic-test-user"),
            new Claim(ClaimTypes.Role, Options.Role)
        ], Scheme);
        return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme)));
    }
}
