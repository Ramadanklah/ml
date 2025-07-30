namespace Data.Entities;

public class Material
{
    public int Id { get; set; }
    public required string Description { get; set; }
    public required string Unit { get; set; }

    public ICollection<MaterialRequest> Requests { get; set; } = [];
}