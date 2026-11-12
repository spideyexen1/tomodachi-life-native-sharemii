// SPDX-License-Identifier: GPL-3.0-only
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace NativeShareMiiSetup {
    public sealed partial class Wizard {
        readonly TabPage repairPage = new TabPage();
        readonly CheckBox vulkanMenu = new CheckBox();
        readonly Label repairIntro = new Label(), repairNote = new Label();
        readonly Button repairButton = new Button();
        readonly TextBox repairResult = new TextBox();
        readonly LinkLabel repairGuide = new LinkLabel();

        void BuildRepairPage() {
            vulkanMenu.SetBounds(20, 333, 790, 34); vulkanMenu.Checked = true; filesPage.Controls.Add(vulkanMenu);
            savesLink.Top = 371; localNote.SetBounds(20, 402, 790, 45); localNote.Font = new Font(Font.FontFamily, 9F);
            repairPage.BackColor = Color.White; tabs.TabPages.Add(repairPage);
            repairIntro.SetBounds(20, 20, 790, 76); repairIntro.Font = new Font(Font, FontStyle.Bold);
            repairNote.SetBounds(20, 105, 790, 92); repairNote.ForeColor = Color.FromArgb(70, 85, 105);
            repairButton.SetBounds(20, 214, 350, 42);
            repairResult.SetBounds(20, 276, 790, 110); repairResult.Multiline = true; repairResult.ReadOnly = true; repairResult.ScrollBars = ScrollBars.Vertical;
            repairGuide.SetBounds(20, 407, 790, 30);
            repairPage.Controls.AddRange(new Control[] {repairIntro, repairNote, repairButton, repairResult, repairGuide});
            repairButton.Click += async delegate { await RepairMenu(); };
            repairGuide.LinkClicked += delegate { Process.Start("https://github.com/spideyexen1/tomodachi-life-native-sharemii/blob/main/docs/" + (Localization.Code == "it" ? "it" : "en") + "/MENU-REPAIR.md"); };
        }
        void TranslateRepair() {
            repairPage.Text = T("Ripara menu F1", "Repair F1 menu");
            vulkanMenu.Text = T("Usa Vulkan per il menu F1 (consigliato; può preparare nuovi shader al primo avvio).", "Use Vulkan for the F1 menu (recommended; may prepare new shaders on first launch).");
            repairIntro.Text = T("F1 blocca i comandi ma il menu non si vede? Su alcune configurazioni OpenGL il pannello resta invisibile. Il passaggio a Vulkan ha risolto il problema sul PC verificato.", "Does F1 block input without showing a menu? On some OpenGL configurations the panel stays invisible. Switching to Vulkan fixed the issue on the tested PC.");
            repairNote.Text = T("Salva e chiudi gioco ed editor. Nella prima scheda seleziona la cartella del port esistente, poi premi Ripara. Conserviamo una copia delle impostazioni grafiche e abilitiamo Vulkan e il menu. Al riavvio può essere necessaria una preparazione degli shader. Serve una GPU Vulkan 1.3.", "Save and close the game and editor. Select the existing port folder in the first tab, then click Repair. We keep a copy of graphics settings and enable Vulkan and the menu. Restarting may require shader preparation. A Vulkan 1.3 GPU is required.");
            repairButton.Text = T("Ripara menu F1 con Vulkan", "Repair F1 menu with Vulkan");
            repairGuide.Text = T("Guida alla riparazione e al ripristino delle impostazioni (IT / EN)", "Menu repair and graphics settings restore guide (IT / EN)");
        }
        async Task<Dictionary<string, object>> RunUtility(string relativeScript, List<string> args, string port) {
            string localPython = Path.Combine(port, @"deps\python-venv\Scripts\python.exe");
            string python = File.Exists(localPython) ? localPython : await Task.Run(delegate { return FindPython(manualPython); });
            if (python == null) throw new InvalidOperationException(T("Installa Python 3.12 dalla scheda Requisiti.", "Install Python 3.12 from Requirements."));
            string root = ExtractBundle(null);
            List<string> command = new List<string> {"-X", "utf8", Path.Combine(root, relativeScript)}; command.AddRange(args);
            string arguments = JoinArguments(command);
            return await Task.Run(delegate {
                ProcessStartInfo info = new ProcessStartInfo(python, arguments); info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = info.RedirectStandardError = true; info.StandardOutputEncoding = info.StandardErrorEncoding = Encoding.UTF8;
                using (Process process = Process.Start(info)) {
                    Task<string> stdout = process.StandardOutput.ReadToEndAsync(), stderr = process.StandardError.ReadToEndAsync(); process.WaitForExit(); Task.WaitAll(stdout, stderr);
                    Dictionary<string, object> data;
                    try { data = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(stdout.Result); }
                    catch { throw new InvalidOperationException(stdout.Result + stderr.Result); }
                    if (process.ExitCode != 0 || !Convert.ToBoolean(data["ok"])) throw new InvalidOperationException(data.ContainsKey("error") ? Convert.ToString(data["error"]) : stderr.Result);
                    return (Dictionary<string, object>)data["result"];
                }
            });
        }
        async Task RepairMenu() {
            if (busy) return;
            string port = destination.Text;
            busy = true; UpdateButtons(); repairResult.Text = T("Controllo e riparazione del menu...", "Checking and repairing the menu...");
            try {
                Dictionary<string, object> result = await RunUtility(@"tools\repair_menu.py", new List<string> {"--port-dir", port}, port);
                repairResult.Text = T("Configurazione pronta: Vulkan e menu F1 abilitati. Riavvia il gioco. Impostazioni e backup:", "Configuration ready: Vulkan and F1 menu enabled. Restart the game. Settings and backup:") + Environment.NewLine + result["config"];
                if (result["backup"] != null) repairResult.AppendText(Environment.NewLine + result["backup"]);
            } catch (Exception error) { repairResult.Text = T("Operazione non completata. Dettagli:", "Operation incomplete. Details:") + Environment.NewLine + error.Message; }
            finally { busy = false; UpdateButtons(); }
        }
    }
}
