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
        readonly TabPage savesPage = new TabPage();
        readonly Label savesIntro = new Label(), sourceLabel = new Label();
        readonly TextBox saveSource = new TextBox(), saveResult = new TextBox();
        readonly CheckBox importAfter = new CheckBox(), confirmVersion = new CheckBox();
        readonly Button saveFolder = new Button(), saveZip = new Button(), saveInspect = new Button(), saveImport = new Button(), saveExport = new Button(), saveRecover = new Button();
        readonly LinkLabel savesGuide = new LinkLabel(), savesLink = new LinkLabel();

        void BuildSavePage() {
            savesPage.BackColor = Color.White; tabs.TabPages.Add(savesPage);
            savesIntro.SetBounds(20, 16, 788, 60); savesIntro.Font = new Font(Font, FontStyle.Bold);
            sourceLabel.SetBounds(20, 80, 790, 25); saveSource.SetBounds(20, 108, 500, 29);
            saveFolder.SetBounds(532, 106, 133, 34); saveZip.SetBounds(677, 106, 133, 34);
            confirmVersion.SetBounds(20, 153, 790, 44); importAfter.SetBounds(20, 199, 790, 44);
            saveInspect.SetBounds(20, 253, 185, 38); saveImport.SetBounds(220, 253, 185, 38); saveExport.SetBounds(420, 253, 185, 38); saveRecover.SetBounds(620, 253, 190, 38);
            saveResult.SetBounds(20, 306, 790, 86); saveResult.Multiline = true; saveResult.ReadOnly = true; saveResult.ScrollBars = ScrollBars.Vertical;
            savesGuide.SetBounds(20, 407, 790, 29); savesLink.SetBounds(20, 338, 790, 26);
            savesPage.Controls.AddRange(new Control[] {savesIntro, sourceLabel, saveSource, saveFolder, saveZip, confirmVersion, importAfter, saveInspect, saveImport, saveExport, saveRecover, saveResult, savesGuide});
            filesPage.Controls.Add(savesLink);
            savesLink.LinkClicked += delegate { tabs.SelectedTab = savesPage; };
            savesGuide.LinkClicked += delegate { Process.Start("https://github.com/spideyexen1/tomodachi-life-native-sharemii/blob/main/docs/" + (Localization.Code == "it" ? "it" : "en") + "/SAVE-TRANSFER.md"); };
            saveFolder.Click += delegate { using (FolderBrowserDialog dialog = new FolderBrowserDialog()) { if (dialog.ShowDialog(this) == DialogResult.OK) saveSource.Text = dialog.SelectedPath; } };
            saveZip.Click += delegate { using (OpenFileDialog dialog = new OpenFileDialog()) { dialog.Filter = "ZIP (*.zip)|*.zip"; if (dialog.ShowDialog(this) == DialogResult.OK) saveSource.Text = dialog.FileName; } };
            saveInspect.Click += async delegate { await SaveAction("inspect", null); };
            saveImport.Click += async delegate {
                if (MessageBox.Show(this, T("Sostituire l'isola del port selezionato? Prima verrà conservato un backup completo. Chiudi anche l'emulatore.", "Replace the island in the selected port? A full backup will be kept first. Close the emulator too."), Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes) await SaveAction("import", null);
            };
            saveExport.Click += async delegate { using (SaveFileDialog dialog = new SaveFileDialog()) { dialog.Filter = "ZIP (*.zip)|*.zip"; dialog.FileName = "Tomodachi-save-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".zip"; if (dialog.ShowDialog(this) == DialogResult.OK) await SaveAction("export", dialog.FileName); } };
            saveRecover.Click += async delegate { await SaveAction("recover", null); };
        }
        void TranslateSaves() {
            savesPage.Text = T("Salvataggi", "Saved games");
            savesIntro.Text = T("Trasferisci un'isola completa. Usa la cartella del port scelta nella prima scheda. Gioco, editor ed emulatore devono essere chiusi.", "Transfer a complete island. Use the port folder selected in the first tab. Close the game, editor and emulator first.");
            sourceLabel.Text = T("Salvataggio da emulatore / backup: cartella raw o ZIP", "Emulator save / backup: raw folder or ZIP");
            saveFolder.Text = T("Cartella...", "Folder..."); saveZip.Text = "ZIP...";
            confirmVersion.Text = T("Confermo che il salvataggio proviene dal gioco 1.0.4 (necessario per cartelle senza metadati).", "I confirm this save is from game 1.0.4 (required for folders without version metadata).");
            importAfter.Text = T("Importa il salvataggio selezionato al termine dell'installazione (facoltativo).", "Import the selected save after installation (optional).");
            saveInspect.Text = T("Verifica sorgente", "Inspect source"); saveImport.Text = T("Importa ora", "Import now"); saveExport.Text = T("Esporta ZIP", "Export ZIP"); saveRecover.Text = T("Recupera interruzione", "Recover interrupted import");
            savesGuide.Text = T("Guida importazione, esportazione e ripristino (IT / EN)", "Import, export and restore guide (IT / EN)");
            savesLink.Text = T("Hai già un'isola su emulatore? Apri Salvataggi →", "Already have an island in an emulator? Open Saved games →");
        }
        void EnableSaveControls() {
            foreach (Control control in savesPage.Controls) control.Enabled = !busy;
            savesLink.Enabled = !busy;
        }
        bool ValidateOptionalSave() {
            if (!importAfter.Checked) return true;
            if (!Directory.Exists(saveSource.Text) && !File.Exists(saveSource.Text)) { MessageBox.Show(this, T("Seleziona prima una cartella di salvataggio o uno ZIP nella scheda Salvataggi.", "Select a save folder or ZIP in Saved games first.")); return false; }
            return MessageBox.Show(this, T("Al termine del setup l'isola selezionata sostituirà quella del port, dopo un backup. Continuare?", "After setup, the selected island will replace the port's island after a backup. Continue?"), Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;
        }
        async Task SaveAction(string operation, string output) {
            if (busy) return;
            if (operation == "inspect" || operation == "import") {
                if (!Directory.Exists(saveSource.Text) && !File.Exists(saveSource.Text)) { MessageBox.Show(this, T("Seleziona prima una cartella di salvataggio o uno ZIP nella scheda Salvataggi.", "Select a save folder or ZIP in Saved games first.")); return; }
            }
            string port = destination.Text, source = saveSource.Text; bool unknown = confirmVersion.Checked;
            string localPython = Path.Combine(port, @"deps\python-venv\Scripts\python.exe");
            busy = true; UpdateButtons(); saveResult.Text = T("Trasferimento in corso... Attendi prima di avviare il gioco.", "Transferring... Wait before starting the game.");
            try {
                string python = File.Exists(localPython) ? localPython : await Task.Run(delegate { return FindPython(manualPython); });
                if (python == null) throw new InvalidOperationException(T("Installa Python 3.12 dalla scheda Requisiti.", "Install Python 3.12 from Requirements."));
                string root = ExtractBundle(null);
                List<string> args = new List<string> {"-X", "utf8", Path.Combine(root, @"payload\save_transfer.py"), operation, "--port-dir", port};
                if (operation == "inspect" || operation == "import") { args.Add("--source"); args.Add(source); }
                if (output != null) { args.Add("--output"); args.Add(output); }
                if (unknown) args.Add("--allow-unknown-version");
                string arguments = JoinArguments(args);
                string result = await Task.Run(delegate {
                    ProcessStartInfo info = new ProcessStartInfo(python, arguments); info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = info.RedirectStandardError = true; info.StandardOutputEncoding = info.StandardErrorEncoding = Encoding.UTF8;
                    using (Process process = Process.Start(info)) {
                        Task<string> stdout = process.StandardOutput.ReadToEndAsync(), stderr = process.StandardError.ReadToEndAsync(); process.WaitForExit(); Task.WaitAll(stdout, stderr);
                        if (process.ExitCode != 0) {
                            string detail = stdout.Result + stderr.Result;
                            try { Dictionary<string, object> failure = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(stdout.Result); detail = Convert.ToString(failure["error"]); } catch { }
                            throw new InvalidOperationException(detail);
                        }
                        return stdout.Result;
                    }
                });
                Dictionary<string, object> data = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(result);
                if (!Convert.ToBoolean(data["ok"])) throw new InvalidOperationException(result);
                Dictionary<string, object> details = (Dictionary<string, object>)data["result"];
                StringBuilder display = new StringBuilder(T("Operazione completata. Dettagli e percorsi:", "Operation complete. Details and paths:"));
                if (details.ContainsKey("files")) display.AppendLine().Append(T("File: ", "Files: ")).Append(details["files"]);
                if (operation == "inspect") display.AppendLine().Append(T("Versione dichiarata: ", "Recorded version: ")).Append(details["game_version"] ?? T("non identificata; conferma 1.0.4 prima di importare", "unknown; confirm 1.0.4 before importing"));
                foreach (string key in new string[] {"backup", "target", "archive"}) if (details.ContainsKey(key)) display.AppendLine().Append(details[key]);
                if (operation == "recover" && !Convert.ToBoolean(details["recovered"])) display.AppendLine().Append(T("Nessuna importazione in sospeso.", "No pending import."));
                saveResult.Text = display.ToString();
                if (operation == "import") importAfter.Checked = false;
            } catch (Exception error) { saveResult.Text = T("Operazione non completata. Dettagli:", "Operation incomplete. Details:") + Environment.NewLine + error.Message; }
            finally { busy = false; UpdateButtons(); }
        }
    }
}
