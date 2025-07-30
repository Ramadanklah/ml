namespace Data.Entities;

public class Doctor
{
    public int Id { get; set; }
    public required string Name { get; set; }
    public string? PracticeAddress { get; set; }

    public ICollection<MaterialRequest> Requests { get; set; } = [];
}