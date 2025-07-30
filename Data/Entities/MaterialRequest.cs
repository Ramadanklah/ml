namespace Data.Entities;

public class MaterialRequest
{
    public int Id { get; set; }
    public DateTime RequestedOn { get; set; } = DateTime.Today;
    public int Quantity { get; set; }

    public required int DoctorId { get; set; }
    public Doctor? Doctor { get; set; }

    public required int MaterialId { get; set; }
    public Material? Material { get; set; }
}