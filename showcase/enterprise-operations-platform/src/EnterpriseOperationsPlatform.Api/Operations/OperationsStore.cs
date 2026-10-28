namespace EnterpriseOperationsPlatform.Api.Operations;

public sealed record Equipment(string Id, string Name, string Area, string Status);
public sealed record WorkOrder(Guid Id, string EquipmentId, string Title, string Priority, string Status, DateTimeOffset CreatedAt);
public sealed record CreateWorkOrder(string EquipmentId, string Title, string Priority = "Normal");

public sealed class OperationsStore
{
    private readonly object _gate = new();
    private readonly List<Equipment> _equipment =
    [new("EQ-100", "混料機 A", "一樓混料區", "Operational"), new("EQ-200", "包裝機 B", "二樓包裝區", "Attention")];
    private readonly List<WorkOrder> _workOrders = [];

    public IReadOnlyList<Equipment> GetEquipment() { lock (_gate) return _equipment.ToArray(); }
    public IReadOnlyList<WorkOrder> GetWorkOrders() { lock (_gate) return _workOrders.OrderByDescending(order => order.CreatedAt).ToArray(); }

    public bool TryCreateEquipment(CreateEquipmentRequest request)
    {
        var normalized = EquipmentValidation.Normalize(request);
        lock (_gate)
        {
            if (_equipment.Any(item => string.Equals(item.Id, normalized.Id, StringComparison.OrdinalIgnoreCase)))
                return false;

            _equipment.Add(new Equipment(normalized.Id!, normalized.Name!, normalized.Area!, normalized.Status!));
            return true;
        }
    }

    public WorkOrder? CreateWorkOrder(CreateWorkOrder request)
    {
        if (WorkOrderValidation.Validate(request).Count > 0) return null;
        var normalized = WorkOrderValidation.Normalize(request);
        lock (_gate)
        {
            if (_equipment.All(item => !string.Equals(item.Id, normalized.EquipmentId, StringComparison.OrdinalIgnoreCase))) return null;
            var order = new WorkOrder(Guid.NewGuid(), normalized.EquipmentId, normalized.Title, normalized.Priority, "Open", DateTimeOffset.UtcNow);
            _workOrders.Add(order);
            return order;
        }
    }
    public WorkOrder? CompleteWorkOrder(Guid id)
    {
        lock (_gate)
        {
            var index = _workOrders.FindIndex(order => order.Id == id);
            if (index < 0) return null;
            var completed = _workOrders[index] with { Status = "Completed" };
            _workOrders[index] = completed;
            return completed;
        }
    }
}
