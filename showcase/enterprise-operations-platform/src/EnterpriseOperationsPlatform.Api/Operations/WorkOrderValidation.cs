namespace EnterpriseOperationsPlatform.Api.Operations;

public static class WorkOrderValidation
{
    public const int EquipmentIdMaxLength = 32;
    public const int TitleMaxLength = 500;
    public const int PriorityMaxLength = 32;

    public static IReadOnlyDictionary<string, string[]> Validate(CreateWorkOrder? request)
    {
        var errors = new Dictionary<string, string[]>();
        if (request is null)
            return new Dictionary<string, string[]> { ["request"] = ["A work-order request is required."] };

        var equipmentId = request.EquipmentId?.Trim() ?? string.Empty;
        if (equipmentId.Length == 0)
            errors["equipmentId"] = ["Equipment is required."];
        else if (equipmentId.Length > EquipmentIdMaxLength)
            errors["equipmentId"] = [$"Equipment must be {EquipmentIdMaxLength} characters or fewer."];

        var title = request.Title?.Trim() ?? string.Empty;
        if (title.Length == 0)
            errors["title"] = ["Title is required."];
        else if (title.Length > TitleMaxLength)
            errors["title"] = [$"Title must be {TitleMaxLength} characters or fewer."];

        var priority = request.Priority?.Trim() ?? string.Empty;
        if (priority.Length > PriorityMaxLength)
            errors["priority"] = [$"Priority must be {PriorityMaxLength} characters or fewer."];

        return errors;
    }

    public static CreateWorkOrder Normalize(CreateWorkOrder request) =>
        new(
            request.EquipmentId.Trim().ToUpperInvariant(),
            request.Title.Trim(),
            string.IsNullOrWhiteSpace(request.Priority) ? "Normal" : request.Priority.Trim());
}
