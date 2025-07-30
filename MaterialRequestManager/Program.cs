using System;
using System.Windows.Forms;
using Data;

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

        Application.Run(new MainForm());
    }
}