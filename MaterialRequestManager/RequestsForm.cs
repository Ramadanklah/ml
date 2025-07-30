using System;
using System.Linq;
using System.Windows.Forms;
using Data;
using Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace MaterialRequestManager;

public class RequestsForm : Form
{
    private readonly LabContext _db = new();

    private ComboBox _cbDoctor = new();
    private ComboBox _cbMaterial = new();
    private NumericUpDown _numQty = new() { Minimum = 1, Maximum = 1000, Value = 1 };
    private Button _btnAdd = new() { Text = "Add" };
    private DataGridView _grid = new() { Dock = DockStyle.Fill, ReadOnly = true, AutoGenerateColumns = true };

    public RequestsForm()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        Text = "Material Requests";
        Width = 800;
        Height = 500;

        var topPanel = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true };

        topPanel.Controls.Add(new Label { Text = "Doctor", AutoSize = true, Padding = new Padding(5) });
        topPanel.Controls.Add(_cbDoctor);
        topPanel.Controls.Add(new Label { Text = "Material", AutoSize = true, Padding = new Padding(5) });
        topPanel.Controls.Add(_cbMaterial);
        topPanel.Controls.Add(new Label { Text = "Qty", AutoSize = true, Padding = new Padding(5) });
        topPanel.Controls.Add(_numQty);
        topPanel.Controls.Add(_btnAdd);

        Controls.Add(_grid);
        Controls.Add(topPanel);

        LoadData();

        _btnAdd.Click += BtnAdd_Click;
    }

    private void LoadData()
    {
        _db.Doctors.Load();
        _db.Materials.Load();
        _db.Requests.Include(r => r.Material).Include(r => r.Doctor).Load();

        _cbDoctor.DataSource = _db.Doctors.Local.ToBindingList();
        _cbDoctor.DisplayMember = "Name";
        _cbDoctor.ValueMember = "Id";

        _cbMaterial.DataSource = _db.Materials.Local.ToBindingList();
        _cbMaterial.DisplayMember = "Description";
        _cbMaterial.ValueMember = "Id";

        RefreshGrid();
    }

    private void RefreshGrid()
    {
        var today = DateTime.Today;
        var list = _db.Requests
            .Include(r => r.Material)
            .Include(r => r.Doctor)
            .Where(r => r.RequestedOn >= today)
            .OrderByDescending(r => r.Id)
            .Select(r => new
            {
                r.Id,
                Date = r.RequestedOn,
                Doctor = r.Doctor!.Name,
                Material = r.Material!.Description,
                r.Quantity
            }).ToList();
        _grid.DataSource = list;
    }

    private void BtnAdd_Click(object? sender, EventArgs e)
    {
        if (_cbDoctor.SelectedValue is not int doctorId || _cbMaterial.SelectedValue is not int materialId)
        {
            MessageBox.Show("Please select doctor and material.");
            return;
        }
        var qty = (int)_numQty.Value;
        var req = new MaterialRequest
        {
            DoctorId = doctorId,
            MaterialId = materialId,
            Quantity = qty,
            RequestedOn = DateTime.Now
        };
        _db.Requests.Add(req);
        _db.SaveChanges();
        RefreshGrid();
    }
}