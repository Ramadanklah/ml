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
        Width = 1000;
        Height = 700;

        var menu = new MenuStrip();
        var doctorsItem = new ToolStripMenuItem("Doctors");
        var requestsItem = new ToolStripMenuItem("Requests");
        var reportsItem = new ToolStripMenuItem("Reports");

        menu.Items.AddRange(new ToolStripItem[] { doctorsItem, requestsItem, reportsItem });
        MainMenuStrip = menu;
        Controls.Add(menu);

        doctorsItem.Click += (_, __) => new DoctorsForm().ShowDialog(this);
        requestsItem.Click += (_, __) => new RequestsForm().ShowDialog(this);
        reportsItem.Click += (_, __) => new ReportsForm().ShowDialog(this);

        var welcome = new Label
        {
            Text = "Welcome to the Material Request Manager\nUse the menu to start.",
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 16, FontStyle.Bold)
        };
        Controls.Add(welcome);
    }
}