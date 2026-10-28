using EnterpriseOperationsPlatform.Api.Operations;

namespace EnterpriseOperationsPlatform.Api.Tests;

public class OperationsStoreTests
{
    [Fact]
    public void CreateKnownEquipmentOrder_IsOpen()
    {
        var store = new OperationsStore();
        var order = store.CreateWorkOrder(new CreateWorkOrder("EQ-100", "檢查馬達振動", "High"));
        Assert.NotNull(order);
        Assert.Equal("Open", order.Status);
        Assert.Single(store.GetWorkOrders());
    }
    [Fact]
    public void CompleteExistingOrder_ChangesStatus()
    {
        var store = new OperationsStore();
        var order = store.CreateWorkOrder(new CreateWorkOrder("EQ-200", "更換封口零件"))!;
        Assert.Equal("Completed", store.CompleteWorkOrder(order.Id)!.Status);
        Assert.Null(store.CompleteWorkOrder(Guid.NewGuid()));
    }
    [Fact]
    public void UnknownEquipment_IsRejected()
    {
        Assert.Null(new OperationsStore().CreateWorkOrder(new CreateWorkOrder("EQ-404", "Synthetic test")));
    }

    [Fact]
    public void InvalidWorkOrder_IsRejectedBeforeStorage()
    {
        var store = new OperationsStore();

        Assert.Null(store.CreateWorkOrder(new CreateWorkOrder("EQ-100", " ")));
        Assert.Empty(store.GetWorkOrders());
    }

    [Fact]
    public void ValidWorkOrder_IsTrimmedAndDefaultsPriority()
    {
        var order = new OperationsStore().CreateWorkOrder(new CreateWorkOrder(" EQ-100 ", " 檢查馬達 ", " "));

        Assert.NotNull(order);
        Assert.Equal("EQ-100", order.EquipmentId);
        Assert.Equal("檢查馬達", order.Title);
        Assert.Equal("Normal", order.Priority);
    }

    [Fact]
    public void EquipmentId_IsCanonicalizedForCaseInsensitiveLookup()
    {
        var order = new OperationsStore().CreateWorkOrder(new CreateWorkOrder("eq-100", "大小寫一致性測試"));

        Assert.NotNull(order);
        Assert.Equal("EQ-100", order.EquipmentId);
    }
}
