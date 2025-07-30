using System.Windows.Forms;
using Data;
using Microsoft.EntityFrameworkCore;

namespace MaterialRequestManager;

public class DoctorsForm : Form
{
    private readonly LabContext _db = new();
    private BindingSource _source = new();

    public DoctorsForm()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        Text = "Doctors";
        Width = 600;
        Height = 400;

        var grid = new DataGridView
        {
            Dock = DockStyle.Fill,
            AutoGenerateColumns = true,
            AllowUserToAddRows = true,
            AllowUserToDeleteRows = true
        };

        var nav = new BindingNavigator(true) { Dock = DockStyle.Top };

        Controls.Add(grid);
        Controls.Add(nav);

        _db.Doctors.Load();
        _source.DataSource = _db.Doctors.Local.ToBindingList();
        grid.DataSource = _source;
        nav.BindingSource = _source;

        FormClosing += DoctorsForm_FormClosing;
    }

    private void DoctorsForm_FormClosing(object? sender, FormClosingEventArgs e)
    {
        // Validate & save
        try
        {
            Validate();
            _source.EndEdit();
            _db.SaveChanges();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Could not save changes: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}