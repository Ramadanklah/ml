using System;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using Data;
using Microsoft.EntityFrameworkCore;
using OfficeOpenXml;

namespace MaterialRequestManager;

public class ReportsForm : Form
{
    private readonly LabContext _db = new();

    private DateTimePicker _dtFrom = new() { Value = DateTime.Today.AddDays(-30) };
    private DateTimePicker _dtTo = new() { Value = DateTime.Today };
    private ComboBox _cbDoctor = new();
    private Button _btnRun = new() { Text = "Refresh" };
    private Button _btnExport = new() { Text = "Export to Excel" };
    private DataGridView _grid = new() { Dock = DockStyle.Fill, ReadOnly = true, AutoGenerateColumns = true };

    public ReportsForm()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        Text = "Reports";
        Width = 800;
        Height = 500;

        var top = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true };
        top.Controls.Add(new Label { Text = "From", AutoSize = true, Padding = new Padding(5) });
        top.Controls.Add(_dtFrom);
        top.Controls.Add(new Label { Text = "To", AutoSize = true, Padding = new Padding(5) });
        top.Controls.Add(_dtTo);
        top.Controls.Add(new Label { Text = "Doctor", AutoSize = true, Padding = new Padding(5) });
        top.Controls.Add(_cbDoctor);
        top.Controls.Add(_btnRun);
        top.Controls.Add(_btnExport);

        Controls.Add(_grid);
        Controls.Add(top);

        LoadData();
        _btnRun.Click += (s, e) => RefreshData();
        _btnExport.Click += (s, e) => Export();
    }

    private void LoadData()
    {
        _db.Doctors.Load();
        var list = _db.Doctors.Local.ToList();
        list.Insert(0, new Data.Entities.Doctor { Id = 0, Name = "All" });
        _cbDoctor.DataSource = list;
        _cbDoctor.DisplayMember = "Name";
        _cbDoctor.ValueMember = "Id";
        RefreshData();
    }

    private void RefreshData()
    {
        var from = _dtFrom.Value.Date;
        var to = _dtTo.Value.Date.AddDays(1); // inclusive
        int doctorId = (_cbDoctor.SelectedValue as int?) ?? 0;

        var query = _db.Requests
            .Include(r => r.Material)
            .Include(r => r.Doctor)
            .Where(r => r.RequestedOn >= from && r.RequestedOn < to);
        if (doctorId != 0)
            query = query.Where(r => r.DoctorId == doctorId);

        var data = query.AsEnumerable()
            .GroupBy(r => r.Material!.Description)
            .Select(g => new { Material = g.Key, Total = g.Sum(r => r.Quantity) })
            .OrderBy(r => r.Material)
            .ToList();

        _grid.DataSource = data;
    }

    private void Export()
    {
        if (_grid.Rows.Count == 0)
        {
            MessageBox.Show("Nothing to export");
            return;
        }

        using var pck = new ExcelPackage();
        var ws = pck.Workbook.Worksheets.Add("Report");
        // headers
        ws.Cells[1, 1].Value = "Material";
        ws.Cells[1, 2].Value = "Total";
        ws.Cells[1, 1, 1, 2].Style.Font.Bold = true;

        int row = 2;
        foreach (DataGridViewRow dgRow in _grid.Rows)
        {
            ws.Cells[row, 1].Value = dgRow.Cells[0].Value;
            ws.Cells[row, 2].Value = dgRow.Cells[1].Value;
            row++;
        }

        var file = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), $"Report_{DateTime.Now:yyyyMMdd_HHmm}.xlsx");
        pck.SaveAs(new FileInfo(file));
        MessageBox.Show($"Report saved to {file}");
    }
}