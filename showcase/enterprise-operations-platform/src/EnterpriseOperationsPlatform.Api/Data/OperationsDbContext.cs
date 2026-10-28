using Microsoft.EntityFrameworkCore;

namespace EnterpriseOperationsPlatform.Api.Data;

public sealed class EquipmentEntity
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Area { get; set; } = string.Empty;
    public string Status { get; set; } = "Operational";
}

public sealed class WorkOrderEntity
{
    public Guid Id { get; set; }
    public string EquipmentId { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Priority { get; set; } = "Normal";
    public string Status { get; set; } = "Open";
    public DateTimeOffset CreatedAt { get; set; }
}

public sealed class OperationsDbContext(DbContextOptions<OperationsDbContext> options) : DbContext(options)
{
    public DbSet<EquipmentEntity> Equipment => Set<EquipmentEntity>();
    public DbSet<WorkOrderEntity> WorkOrders => Set<WorkOrderEntity>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<EquipmentEntity>(entity =>
        {
            entity.ToTable("equipment");
            entity.HasKey(item => item.Id);
            entity.Property(item => item.Id).HasMaxLength(32);
            entity.Property(item => item.Name).HasMaxLength(200).IsRequired();
            entity.Property(item => item.Area).HasMaxLength(200).IsRequired();
            entity.Property(item => item.Status).HasMaxLength(32).IsRequired();
        });
        modelBuilder.Entity<WorkOrderEntity>(entity =>
        {
            entity.ToTable("work_orders");
            entity.HasKey(item => item.Id);
            entity.Property(item => item.EquipmentId).HasMaxLength(32).IsRequired();
            entity.Property(item => item.Title).HasMaxLength(500).IsRequired();
            entity.Property(item => item.Priority).HasMaxLength(32).IsRequired();
            entity.Property(item => item.Status).HasMaxLength(32).IsRequired();
            entity.HasIndex(item => item.EquipmentId);
        });
    }
}
