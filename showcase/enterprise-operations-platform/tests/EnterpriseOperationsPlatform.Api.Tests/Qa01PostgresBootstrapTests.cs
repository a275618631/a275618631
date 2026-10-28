using EnterpriseOperationsPlatform.Api.Data;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace EnterpriseOperationsPlatform.Api.Tests;

public sealed class Qa01PostgresBootstrapTests
{
    [Qa01DatabaseFact]
    public async Task DedicatedRestoreSchemaCanMigrateAndReportSyntheticDigest()
    {
        var connectionString = Environment.GetEnvironmentVariable("QA01_POSTGRES_CONNECTION")
            ?? throw new InvalidOperationException("QA01_POSTGRES_CONNECTION is required.");
        var schema = Environment.GetEnvironmentVariable("QA01_POSTGRES_SCHEMA")
            ?? throw new InvalidOperationException("QA01_POSTGRES_SCHEMA is required.");
        var runId = Environment.GetEnvironmentVariable("QA01_RUN_ID")
            ?? throw new InvalidOperationException("QA01_RUN_ID is required.");
        var action = Environment.GetEnvironmentVariable("QA01_DB_ACTION") ?? "migrate";
        var artifactsDirectory = Environment.GetEnvironmentVariable("QA01_ARTIFACTS_DIR")
            ?? throw new InvalidOperationException("QA01_ARTIFACTS_DIR is required.");

        if (!System.Text.RegularExpressions.Regex.IsMatch(schema, "^qa01_[a-f0-9]{32}$"))
            throw new InvalidOperationException("QA-01 schema name is outside its dedicated namespace.");

        var builder = new NpgsqlConnectionStringBuilder(connectionString);
        if (string.IsNullOrWhiteSpace(builder.Host)
            || builder.Host is not ("127.0.0.1" or "localhost" or "::1")
            || string.IsNullOrWhiteSpace(builder.Database)
            || !builder.Database.StartsWith("enterprise_operations_restore_", StringComparison.Ordinal)
            || builder.Username != "enterprise_operations")
        {
            throw new InvalidOperationException("QA-01 permits only the local A restore database and application role.");
        }

        await using (var connection = new NpgsqlConnection(connectionString))
        {
            await connection.OpenAsync();
            await using var createSchema = new NpgsqlCommand($"CREATE SCHEMA IF NOT EXISTS \"{schema}\"", connection);
            await createSchema.ExecuteNonQueryAsync();
        }

        builder.SearchPath = schema;
        var options = new DbContextOptionsBuilder<OperationsDbContext>()
            .UseNpgsql(builder.ConnectionString)
            .Options;
        await using var db = new OperationsDbContext(options);
        await db.Database.MigrateAsync();

        if (action == "migrate")
        {
            Assert.True(await db.Database.CanConnectAsync());
            return;
        }

        if (action != "digest")
            throw new InvalidOperationException($"Unsupported QA-01 database action: {action}.");

        var prefix = $"QA01-{runId}-";
        var equipment = await db.Equipment.AsNoTracking()
            .Where(item => item.Name.StartsWith(prefix))
            .OrderBy(item => item.Id)
            .Select(item => new { item.Id, item.Name, item.Area, item.Status })
            .ToListAsync();
        var orders = await db.WorkOrders.AsNoTracking()
            .Where(order => order.Title.StartsWith(prefix))
            .OrderBy(order => order.Title)
            .Select(order => new { order.Id, order.Title, order.Status })
            .ToListAsync();
        var json = JsonSerializer.Serialize(new { equipment, orders });
        var digest = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(json))).ToLowerInvariant();
        Directory.CreateDirectory(artifactsDirectory);
        await File.WriteAllTextAsync(
            Path.Combine(artifactsDirectory, $"database-{action}-{runId}.json"),
            JsonSerializer.Serialize(new { runId, equipmentCount = equipment.Count, workOrderCount = orders.Count, recordCount = equipment.Count + orders.Count, sha256 = digest }, new JsonSerializerOptions { WriteIndented = true }));
        Assert.NotEmpty(equipment);
        Assert.NotEmpty(orders);
    }
}

public sealed class Qa01DatabaseFactAttribute : FactAttribute
{
    public Qa01DatabaseFactAttribute()
    {
        if (Environment.GetEnvironmentVariable("QA01_RUN_POSTGRES_BOOTSTRAP") != "1")
            Skip = "Set QA01_RUN_POSTGRES_BOOTSTRAP=1 through scripts/qa-01.ps1 to run against its isolated schema.";
    }
}
