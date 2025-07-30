using System.Drawing;
using System.Windows.Forms;

namespace MaterialRequestManager;

public class MainForm : Form
{
    public MainForm()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        Text = "Material Request Manager";
        Width = 800;
        Height = 600;
        var lbl = new Label
        {
            Text = "Material Request Manager\n(Basic skeleton – extend as needed)",
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 14, FontStyle.Bold)
        };
        Controls.Add(lbl);
    }
}