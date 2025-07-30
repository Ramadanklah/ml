using Microsoft.EntityFrameworkCore;
using Data.Entities;

namespace Data;

internal static class LabSeed
{
    public static void Seed(ModelBuilder b)
    {
        var id = 1;
        b.Entity<Material>().HasData(
            new Material { Id = id++, Description = "S-Monovette Serum Gel, 7,5 ml", Unit = "Pck. á 50" },
            new Material { Id = id++, Description = "S-Monovette Citrat, 2,9 ml", Unit = "Pck. á 50" },
            new Material { Id = id++, Description = "S-Monovette EDTA, 2,6 ml", Unit = "Pck. á 50" },
            new Material { Id = id++, Description = "Vacutainer Serum Gel, 5,0 ml", Unit = "Pck. á 100" },
            new Material { Id = id++, Description = "Trachealsaugset, 70 ml", Unit = "Einzeln" },
            new Material { Id = id++, Description = "Infoflyer für Patienten – Thema bitte angeben", Unit = "-" }
        );
    }
}