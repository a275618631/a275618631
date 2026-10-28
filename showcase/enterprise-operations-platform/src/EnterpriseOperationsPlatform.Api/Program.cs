using EnterpriseOperationsPlatform.Api.Data;
using EnterpriseOperationsPlatform.Api.Operations;
using EnterpriseOperationsPlatform.Api.Security;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.Extensions.Options;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;

static bool IsConfigured(string? value) =>
    !string.IsNullOrWhiteSpace(value)
    && !string.Equals(value, "SET_IN_LOCAL_SECRET_STORE", StringComparison.OrdinalIgnoreCase);

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<OperationsStore>();
builder.Services.Configure<DemoAuthOptions>(builder.Configuration.GetSection("DemoAuth"));
var jwtSettings = builder.Configuration.GetSection("Authentication:Jwt");
var jwtIssuer = jwtSettings["Issuer"];
var jwtAudience = jwtSettings["Audience"];
var jwtSigningKey = jwtSettings["SigningKey"];
var hasJwtConfiguration = IsConfigured(jwtIssuer)
    && IsConfigured(jwtAudience)
    && IsConfigured(jwtSigningKey)
    && Encoding.UTF8.GetByteCount(jwtSigningKey!) >= 32;
var validationSigningKey = hasJwtConfiguration
    ? new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSigningKey!))
    : new SymmetricSecurityKey(RandomNumberGenerator.GetBytes(32));
var validationIssuer = hasJwtConfiguration ? jwtIssuer : "unconfigured-local-jwt";
var validationAudience = hasJwtConfiguration ? jwtAudience : "unconfigured-local-jwt";

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = validationSigningKey,
            ValidateIssuer = true,
            ValidIssuer = validationIssuer,
            ValidateAudience = true,
            ValidAudience = validationAudience,
            ValidateLifetime = true,
            RoleClaimType = ClaimTypes.Role,
            ClockSkew = TimeSpan.FromMinutes(1)
        };
    });
builder.Services.AddAuthorizationBuilder()
    .AddPolicy(OperationsAuthorization.ReadPolicy, policy => policy
        .RequireAuthenticatedUser()
        .RequireRole(OperationsAuthorization.Viewer, OperationsAuthorization.Operator, OperationsAuthorization.Supervisor, OperationsAuthorization.Administrator))
    .AddPolicy(OperationsAuthorization.WritePolicy, policy => policy
        .RequireAuthenticatedUser()
        .RequireRole(OperationsAuthorization.Operator, OperationsAuthorization.Supervisor, OperationsAuthorization.Administrator))
    .AddPolicy(OperationsAuthorization.CompletePolicy, policy => policy
        .RequireAuthenticatedUser()
        .RequireRole(OperationsAuthorization.Supervisor, OperationsAuthorization.Administrator));
var operationsConnection = builder.Configuration.GetConnectionString("Operations");
if (!string.IsNullOrWhiteSpace(operationsConnection))
{
    builder.Services.AddDbContext<OperationsDbContext>(options => options.UseNpgsql(operationsConnection));
}
var allowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()
    ?? ["http://127.0.0.1:5173", "http://localhost:5173"];
builder.Services.AddCors(options => options.AddDefaultPolicy(policy => policy
    .WithOrigins(allowedOrigins)
    .AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();

if (app.Environment.IsDevelopment())
{
    app.MapPost("/api/auth/demo-login", (DemoLoginRequest request, IOptions<DemoAuthOptions> options, IOptionsMonitor<JwtBearerOptions> jwtOptions) =>
    {
        if (!options.Value.Enabled)
            return Results.NotFound();

        if (string.IsNullOrWhiteSpace(request.Username) || string.IsNullOrWhiteSpace(request.Password))
            return Results.BadRequest(new { message = "Username and password are required." });

        var user = options.Value.Authenticate(request.Username, request.Password);
        if (user is null)
            return Results.Unauthorized();

        var validationParameters = jwtOptions.Get(JwtBearerDefaults.AuthenticationScheme).TokenValidationParameters;
        if (validationParameters.ValidIssuer is null
            || validationParameters.ValidAudience is null
            || string.Equals(validationParameters.ValidIssuer, "unconfigured-local-jwt", StringComparison.Ordinal)
            || validationParameters.IssuerSigningKey is not SymmetricSecurityKey signingKey)
        {
            return Results.Problem(
                statusCode: StatusCodes.Status503ServiceUnavailable,
                title: "Local JWT settings are not configured.",
                detail: "Run scripts/set-local-jwt.ps1 before using the local demo login.");
        }

        const int expiresInSeconds = 3600;
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Username),
            new Claim(ClaimTypes.Name, user.Username),
            new Claim(ClaimTypes.Role, user.Role)
        };
        var credentials = new SigningCredentials(signingKey, SecurityAlgorithms.HmacSha256);
        var token = new JwtSecurityToken(
            issuer: validationParameters.ValidIssuer,
            audience: validationParameters.ValidAudience,
            claims: claims,
            expires: DateTime.UtcNow.AddSeconds(expiresInSeconds),
            signingCredentials: credentials);

        return Results.Ok(new DemoLoginResponse(
            new System.IdentityModel.Tokens.Jwt.JwtSecurityTokenHandler().WriteToken(token),
            user.Username,
            user.Role,
            expiresInSeconds));
    });
}

using (var startupScope = app.Services.CreateScope())
{
    if (startupScope.ServiceProvider.GetService<OperationsDbContext>() is { } startupDb && !await startupDb.Equipment.AnyAsync())
    {
        startupDb.Equipment.AddRange(
            new EquipmentEntity { Id = "EQ-100", Name = "混料機 A", Area = "一樓混料區", Status = "Operational" },
            new EquipmentEntity { Id = "EQ-200", Name = "包裝機 B", Area = "二樓包裝區", Status = "Attention" });
        await startupDb.SaveChangesAsync();
    }
}

var operations = app.MapGroup("/api/operations")
    .RequireAuthorization(OperationsAuthorization.ReadPolicy);
operations.MapGet("/equipment", async (OperationsStore store, IServiceProvider services) =>
{
    var db = services.GetService<OperationsDbContext>();
    if (db is null) return Results.Ok(store.GetEquipment());
    var equipment = await db.Equipment.AsNoTracking().OrderBy(item => item.Id).ToListAsync();
    return Results.Ok(equipment);
});
operations.MapPost("/equipment", async (CreateEquipmentRequest request, OperationsStore store, IServiceProvider services) =>
{
    var validationErrors = EquipmentValidation.Validate(request);
    if (validationErrors.Count > 0) return Results.ValidationProblem(validationErrors);
    var normalized = EquipmentValidation.Normalize(request);
    var db = services.GetService<OperationsDbContext>();
    if (db is not null)
    {
        var duplicate = await db.Equipment.AnyAsync(item => item.Id.ToUpper() == normalized.Id);
        if (duplicate) return Results.Conflict(new { message = "Equipment ID already exists." });

        var entity = new EquipmentEntity
        {
            Id = normalized.Id!,
            Name = normalized.Name!,
            Area = normalized.Area!,
            Status = normalized.Status!
        };
        db.Equipment.Add(entity);
        try
        {
            await db.SaveChangesAsync();
        }
        catch (DbUpdateException exception) when (exception.InnerException is Npgsql.PostgresException { SqlState: Npgsql.PostgresErrorCodes.UniqueViolation })
        {
            return Results.Conflict(new { message = "Equipment ID already exists." });
        }
        return Results.Created($"/api/operations/equipment/{entity.Id}", entity);
    }

    return store.TryCreateEquipment(normalized)
        ? Results.Created($"/api/operations/equipment/{normalized.Id}", normalized)
        : Results.Conflict(new { message = "Equipment ID already exists." });
}).RequireAuthorization(OperationsAuthorization.WritePolicy);
operations.MapGet("/work-orders", async (OperationsStore store, IServiceProvider services) =>
{
    var db = services.GetService<OperationsDbContext>();
    if (db is null) return Results.Ok(store.GetWorkOrders());
    var workOrders = await db.WorkOrders.AsNoTracking().OrderByDescending(order => order.CreatedAt).ToListAsync();
    return Results.Ok(workOrders);
});
operations.MapPost("/work-orders", async (CreateWorkOrder request, OperationsStore store, IServiceProvider services) =>
{
    var validationErrors = WorkOrderValidation.Validate(request);
    if (validationErrors.Count > 0) return Results.ValidationProblem(validationErrors);
    request = WorkOrderValidation.Normalize(request);
    var db = services.GetService<OperationsDbContext>();
    if (db is not null)
    {
        var equipmentExists = await db.Equipment.AnyAsync(item => item.Id == request.EquipmentId);
        if (!equipmentExists) return Results.NotFound(new { message = "Equipment was not found." });
        var entity = new WorkOrderEntity
        {
            Id = Guid.NewGuid(),
            EquipmentId = request.EquipmentId,
            Title = request.Title.Trim(),
            Priority = string.IsNullOrWhiteSpace(request.Priority) ? "Normal" : request.Priority.Trim(),
            Status = "Open",
            CreatedAt = DateTimeOffset.UtcNow
        };
        db.WorkOrders.Add(entity);
        await db.SaveChangesAsync();
        return Results.Created($"/api/operations/work-orders/{entity.Id}", entity);
    }
    var result = store.CreateWorkOrder(request);
    return result is null ? Results.NotFound(new { message = "Equipment was not found." }) : Results.Created($"/api/operations/work-orders/{result.Id}", result);
}).RequireAuthorization(OperationsAuthorization.WritePolicy);
operations.MapPost("/work-orders/{id:guid}/complete", async (Guid id, OperationsStore store, IServiceProvider services) =>
{
    var db = services.GetService<OperationsDbContext>();
    if (db is not null)
    {
        var entity = await db.WorkOrders.SingleOrDefaultAsync(order => order.Id == id);
        if (entity is null) return Results.NotFound();
        entity.Status = "Completed";
        await db.SaveChangesAsync();
        return Results.Ok(entity);
    }
    var updated = store.CompleteWorkOrder(id);
    return updated is null ? Results.NotFound() : Results.Ok(updated);
}).RequireAuthorization(OperationsAuthorization.CompletePolicy);
app.MapGet("/health", async (IServiceProvider services) =>
{
    var db = services.GetService<OperationsDbContext>();
    if (db is null) return Results.Ok(new { status = "ok", persistence = "in-memory" });
    var connected = await db.Database.CanConnectAsync();
    return Results.Ok(new { status = connected ? "ok" : "degraded", persistence = connected ? "postgresql" : "postgresql-unreachable" });
});
app.Run();

public partial class Program;
