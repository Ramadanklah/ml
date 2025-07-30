using Microsoft.EntityFrameworkCore;
using Data.Entities;

namespace Data;

public class LabContext : DbContext
{
    private const string DbFile = "lab.db";

    public DbSet<Doctor> Doctors => Set<Doctor>();
    public DbSet<Material> Materials => Set<Material>();
    public DbSet<MaterialRequest> Requests => Set<MaterialRequest>();

    protected override void OnConfiguring(DbContextOptionsBuilder options)
        => options.UseSqlite($"Data Source={DbFile}");

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Doctor>().HasIndex(d => d.Name).IsUnique();
        LabSeed.Seed(modelBuilder);
    }
}