using System.Text.RegularExpressions;

namespace EnterpriseOperationsPlatform.Api.Operations;

public sealed record CreateEquipmentRequest(string? Id, string? Name, string? Area, string? Status = "Operational");

public static partial class EquipmentValidation
{
    public const int IdMaxLength = 32;
    public const int NameMaxLength = 200;
    public const int AreaMaxLength = 200;
    public const int StatusMaxLength = 32;

    private static readonly string[] AllowedStatuses = ["Operational", "Attention"];

    public static IReadOnlyDictionary<string, string[]> Validate(CreateEquipmentRequest? request)
    {
        var errors = new Dictionary<string, string[]>();
        if (request is null)
            return new Dictionary<string, string[]> { ["request"] = ["An equipment request is required."] };

        var id = request.Id?.Trim() ?? string.Empty;
        if (id.Length == 0)
            errors["id"] = ["Equipment ID is required."];
        else if (id.Length > IdMaxLength)
            errors["id"] = [$"Equipment ID must be {IdMaxLength} characters or fewer."];
        else if (!EquipmentIdPattern().IsMatch(id))
            errors["id"] = ["Equipment ID may contain letters, numbers, hyphens, and underscores only."];

        ValidateRequiredText(errors, "name", request.Name, NameMaxLength, "Equipment name");
        ValidateRequiredText(errors, "area", request.Area, AreaMaxLength, "Area");

        var status = request.Status?.Trim() ?? string.Empty;
        if (status.Length > StatusMaxLength)
            errors["status"] = [$"Status must be {StatusMaxLength} characters or fewer."];
        else if (status.Length > 0 && !AllowedStatuses.Contains(status, StringComparer.OrdinalIgnoreCase))
            errors["status"] = ["Status must be Operational or Attention."];

        return errors;
    }

    public static CreateEquipmentRequest Normalize(CreateEquipmentRequest request)
    {
        var status = request.Status?.Trim();
        var normalizedStatus = string.IsNullOrWhiteSpace(status)
            ? "Operational"
            : AllowedStatuses.First(allowed => string.Equals(allowed, status, StringComparison.OrdinalIgnoreCase));

        return new CreateEquipmentRequest(
            request.Id!.Trim().ToUpperInvariant(),
            request.Name!.Trim(),
            request.Area!.Trim(),
            normalizedStatus);
    }

    private static void ValidateRequiredText(Dictionary<string, string[]> errors, string field, string? value, int maxLength, string label)
    {
        var normalized = value?.Trim() ?? string.Empty;
        if (normalized.Length == 0)
            errors[field] = [$"{label} is required."];
        else if (normalized.Length > maxLength)
            errors[field] = [$"{label} must be {maxLength} characters or fewer."];
    }

    [GeneratedRegex("^[A-Za-z0-9][A-Za-z0-9_-]*$", RegexOptions.CultureInvariant)]
    private static partial Regex EquipmentIdPattern();
}
