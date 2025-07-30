using System;
using System.Windows.Forms;
using Data;
using OfficeOpenXml;

namespace MaterialRequestManager;

internal static class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        using var db = new LabContext();
        db.Database.EnsureCreated();
        ExcelPackage.LicenseContext = LicenseContext.NonCommercial;

        Application.Run(new MainForm());
    }
}