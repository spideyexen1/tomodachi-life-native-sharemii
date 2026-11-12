// SPDX-License-Identifier: GPL-3.0-only
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Tomodachi Life Native + ShareMii Setup")]
[assembly: AssemblyVersion("0.2.0.0")]
[assembly: AssemblyFileVersion("0.2.0.0")]
[assembly: AssemblyDescription("Source-only installation wizard; no game content is included")]

namespace NativeShareMiiSetup {
    static class Program {
        [STAThread]
        static int Main(string[] args) {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            try {
                if (Array.IndexOf(args, "--self-test") >= 0) {
                    string snapshot = Value(args, "--snapshot");
                    string folder = Value(args, "--work-dir");
                    if (String.IsNullOrEmpty(folder)) throw new ArgumentException("--work-dir is required for self-test");
                    using (Wizard wizard = new Wizard(true)) wizard.SelfTest(folder, snapshot);
                    File.WriteAllText(Path.Combine(folder, "self-test.txt"), "PASS: source bundle, path validation, languages, modes and form rendering.\r\n");
                    return 0;
                }
                Application.Run(new Wizard(false));
                return 0;
            } catch (Exception error) {
                if (Array.IndexOf(args, "--self-test") >= 0) {
                    string folder = Value(args, "--work-dir");
                    if (!String.IsNullOrEmpty(folder)) { Directory.CreateDirectory(folder); File.WriteAllText(Path.Combine(folder, "self-test.txt"), error.ToString()); }
                    return 1;
                }
                MessageBox.Show(error.Message, "Native + ShareMii Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }
        static string Value(string[] args, string key) {
            int index = Array.IndexOf(args, key);
            return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
        }
    }

    public sealed class Wizard : Form {
        readonly ComboBox language = new ComboBox();
        readonly ComboBox mode = new ComboBox();
        readonly TabControl tabs = new TabControl();
        readonly TabPage filesPage = new TabPage();
        readonly TabPage requirementsPage = new TabPage();
        readonly TabPage progressPage = new TabPage();
        readonly TextBox destination = new TextBox();
        readonly TextBox baseFile = new TextBox();
        readonly TextBox updateFile = new TextBox();
        readonly TextBox keysFile = new TextBox();
        readonly TextBox log = new TextBox();
        readonly Label heading = new Label();
        readonly Label subtitle = new Label();
        readonly Label fileIntro = new Label();
        readonly Label modeLabel = new Label();
        readonly Label destinationLabel = new Label();
        readonly Label baseLabel = new Label();
        readonly Label updateLabel = new Label();
        readonly Label keysLabel = new Label();
        readonly Label localNote = new Label();
        readonly Label requirementsIntro = new Label();
        readonly Label pythonStatus = new Label();
        readonly Label compilerStatus = new Label();
        readonly Label buildNote = new Label();
        readonly Label phase = new Label();
        readonly Label progressNote = new Label();
        readonly ProgressBar bar = new ProgressBar();
        readonly Button back = new Button();
        readonly Button next = new Button();
        readonly Button cancel = new Button();
        readonly Button refresh = new Button();
        readonly Button pythonInstall = new Button();
        readonly Button compilerInstall = new Button();
        readonly Button choosePython = new Button();
        readonly Button openLogs = new Button();
        readonly List<Button> browseButtons = new List<Button>();
        bool italian, busy, installing, cancelled, finished, compilerFound;
        string pythonPath, manualPython, cacheRoot, logPath;
        Process activeProcess;
        StreamWriter fileLog;
        readonly object logSync = new object();

        public Wizard(bool testing) {
            italian = System.Globalization.CultureInfo.CurrentUICulture.TwoLetterISOLanguageName == "it";
            Text = "Native + ShareMii Setup 0.2.0";
            ClientSize = new Size(900, 690);
            MinimumSize = new Size(916, 729);
            MaximumSize = new Size(916, 729);
            StartPosition = FormStartPosition.CenterScreen;
            AutoScaleMode = AutoScaleMode.Dpi;
            Font = new Font("Segoe UI", 10F);
            BackColor = Color.FromArgb(246, 248, 251);
            Panel hero = new Panel(); hero.SetBounds(0, 0, 900, 108); hero.BackColor = Color.FromArgb(22, 43, 73);
            heading.SetBounds(28, 20, 640, 38); heading.Font = new Font("Segoe UI", 21F, FontStyle.Bold); heading.ForeColor = Color.White;
            subtitle.SetBounds(30, 64, 650, 30); subtitle.ForeColor = Color.FromArgb(203, 220, 238);
            language.SetBounds(738, 34, 132, 30); language.DropDownStyle = ComboBoxStyle.DropDownList;
            language.Items.AddRange(new object[] {"Italiano", "English"}); language.SelectedIndex = italian ? 0 : 1;
            language.SelectedIndexChanged += delegate { italian = language.SelectedIndex == 0; Translate(); };
            hero.Controls.AddRange(new Control[] {heading, subtitle, language}); Controls.Add(hero);
            tabs.SetBounds(24, 128, 852, 480);
            filesPage.BackColor = requirementsPage.BackColor = progressPage.BackColor = Color.White;
            tabs.TabPages.AddRange(new TabPage[] {filesPage, requirementsPage, progressPage});
            tabs.Selecting += delegate(object sender, TabControlCancelEventArgs e) { if ((busy || finished) && e.TabPageIndex != 2) e.Cancel = true; };
            tabs.SelectedIndexChanged += delegate { UpdateButtons(); };
            Controls.Add(tabs);
            fileIntro.SetBounds(20, 16, 788, 46); fileIntro.Font = new Font(Font, FontStyle.Bold);
            modeLabel.SetBounds(20, 73, 180, 26); mode.SetBounds(204, 69, 606, 30); mode.DropDownStyle = ComboBoxStyle.DropDownList;
            mode.SelectedIndexChanged += delegate { SetMode(); };
            filesPage.Controls.AddRange(new Control[] {fileIntro, modeLabel, mode});
            AddPathRow(destinationLabel, destination, 116, true, "");
            AddPathRow(baseLabel, baseFile, 176, false, "Game package (*.nsp;*.nsz;*.xci)|*.nsp;*.nsz;*.xci");
            AddPathRow(updateLabel, updateFile, 236, false, "Update package (*.nsp;*.nsz)|*.nsp;*.nsz");
            AddPathRow(keysLabel, keysFile, 296, false, "Console keys (*.keys)|*.keys");
            localNote.SetBounds(20, 365, 790, 65); localNote.ForeColor = Color.FromArgb(70, 85, 105); filesPage.Controls.Add(localNote);
            destination.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "TomodachiLife");
            requirementsIntro.SetBounds(20, 18, 790, 55); requirementsIntro.Font = new Font(Font, FontStyle.Bold);
            pythonStatus.SetBounds(22, 94, 780, 30); compilerStatus.SetBounds(22, 225, 780, 30);
            pythonInstall.SetBounds(22, 135, 248, 38); choosePython.SetBounds(284, 135, 248, 38);
            compilerInstall.SetBounds(22, 266, 346, 38); refresh.SetBounds(552, 135, 250, 38);
            buildNote.SetBounds(22, 330, 780, 91); buildNote.ForeColor = Color.FromArgb(70, 85, 105);
            requirementsPage.Controls.AddRange(new Control[] {requirementsIntro, pythonStatus, compilerStatus, pythonInstall, choosePython, compilerInstall, refresh, buildNote});
            refresh.Click += async delegate { await Probe(); };
            choosePython.Click += async delegate { using (OpenFileDialog dialog = new OpenFileDialog()) { dialog.Filter = "Python executable|python.exe"; if (dialog.ShowDialog(this) == DialogResult.OK) { manualPython = dialog.FileName; await Probe(); } } };
            pythonInstall.Click += async delegate { await InstallPrerequisite(false); };
            compilerInstall.Click += async delegate { await InstallPrerequisite(true); };
            phase.SetBounds(20, 18, 790, 30); phase.Font = new Font(Font, FontStyle.Bold);
            bar.SetBounds(20, 57, 790, 24);
            progressNote.SetBounds(20, 91, 790, 48); progressNote.ForeColor = Color.FromArgb(70, 85, 105);
            log.SetBounds(20, 143, 790, 245); log.Multiline = true; log.ReadOnly = true; log.ScrollBars = ScrollBars.Both; log.WordWrap = false; log.Font = new Font("Consolas", 9F);
            openLogs.SetBounds(20, 400, 270, 33); openLogs.Click += delegate { if (!String.IsNullOrEmpty(logPath)) Process.Start("explorer.exe", "/select," + Quote(logPath)); };
            progressPage.Controls.AddRange(new Control[] {phase, bar, progressNote, log, openLogs});
            back.SetBounds(524, 635, 108, 36); next.SetBounds(644, 635, 108, 36); cancel.SetBounds(764, 635, 108, 36);
            back.Click += delegate { if (!busy && tabs.SelectedIndex > 0) tabs.SelectedIndex--; };
            next.Click += async delegate {
                if (finished) { LaunchGame(); return; }
                if (tabs.SelectedIndex == 0) { if (!ValidateFields()) return; tabs.SelectedIndex = 1; await Probe(); }
                else if (tabs.SelectedIndex == 1) await Install();
                else { tabs.SelectedIndex = 1; await Probe(); }
            };
            cancel.Click += delegate { if (busy && installing) StopInstallation(); else if (!busy) Close(); };
            Controls.AddRange(new Control[] {back, next, cancel});
            LinkLabel credits = new LinkLabel(); credits.SetBounds(28, 644, 465, 25); credits.Text = "GPL-3.0 · Original port + ShareMii credits / Sorgenti";
            credits.LinkClicked += delegate { Process.Start("https://github.com/spideyexen1/tomodachi-life-native-sharemii"); }; Controls.Add(credits);
            FormClosing += delegate(object sender, FormClosingEventArgs e) { if (busy) { e.Cancel = true; if (installing) StopInstallation(); else MessageBox.Show(this, T("Attendi la conclusione dell'installer dei prerequisiti.", "Wait for the prerequisite installer to finish.")); } };
            Translate();
        }

        string T(string it, string en) { return italian ? it : en; }
        void Translate() {
            heading.Text = "Native + ShareMii";
            subtitle.Text = T("Setup guidato Windows · nessun file del gioco incluso", "Windows setup wizard · no game files included");
            filesPage.Text = T("1. Cartella e file", "1. Folder and files"); requirementsPage.Text = T("2. Requisiti", "2. Requirements"); progressPage.Text = T("3. Installazione", "3. Installation");
            fileIntro.Text = T("Scegli dove installare il port e indica i file della tua copia.", "Choose the port folder and select files from your own copy.");
            modeLabel.Text = T("Tipo di installazione", "Installation mode"); int selected = Math.Max(0, mode.SelectedIndex);
            mode.Items.Clear(); mode.Items.Add(T("Nuova installazione / riprendi", "New installation / resume")); mode.Items.Add(T("Port già installato: aggiungi ShareMii", "Existing port: add ShareMii")); mode.SelectedIndex = selected;
            destinationLabel.Text = T("Cartella del port", "Port folder"); baseLabel.Text = T("Gioco base", "Base game"); updateLabel.Text = T("Aggiornamento 1.0.4", "Update 1.0.4"); keysLabel.Text = "prod.keys";
            foreach (Button button in browseButtons) button.Text = T("Sfoglia...", "Browse...");
            localNote.Text = T("Gioco, aggiornamento e chiavi vengono letti solo sul tuo PC. Non vengono caricati online. Per una nuova installazione scegli una cartella vuota; per riprendere usa la stessa cartella.", "Game, update and keys are read only on your PC and are never uploaded. Choose an empty folder for a new installation; use the same folder to resume.");
            requirementsIntro.Text = T("Controlla i prerequisiti. Puoi installare quelli mancanti con i pulsanti qui sotto.", "Check prerequisites. Use the buttons below to install missing components.");
            pythonInstall.Text = T("Installa Python 3.12", "Install Python 3.12"); choosePython.Text = T("Scegli Python già installato...", "Select an installed Python..."); compilerInstall.Text = T("Installa Microsoft C++ Build Tools", "Install Microsoft C++ Build Tools"); refresh.Text = T("Ripeti controllo", "Check again");
            buildNote.Text = T("Windows x64 · GPU Vulkan 1.3 / OpenGL 4.5 · almeno 8 GB RAM (16 consigliati) · circa 15 GB + strumenti e backup.\r\nLa prima compilazione e gli shader possono richiedere un'ora o più. Microsoft C++ può chiedere la conferma amministratore di Windows.", "Windows x64 · Vulkan 1.3 / OpenGL 4.5 GPU · 8 GB RAM minimum (16 recommended) · about 15 GB plus tools and backups.\r\nThe first build and shaders may take an hour or longer. Microsoft C++ installation may request Windows administrator approval.");
            progressNote.Text = T("Mantieni il PC acceso. Se interrompi, i passaggi completati restano disponibili per riprendere.", "Keep the PC running. If you cancel, completed steps are retained for a later resume.");
            openLogs.Text = T("Mostra log installazione", "Show installation log"); back.Text = T("Indietro", "Back"); cancel.Text = busy && installing ? T("Interrompi", "Stop") : T("Chiudi", "Close");
            if (!busy) phase.Text = finished ? T("Installazione completata", "Installation complete") : T("Pronto per l'installazione", "Ready to install");
            UpdateStatus(); UpdateButtons();
        }
        void AddPathRow(Label label, TextBox box, int y, bool directory, string filter) {
            label.SetBounds(20, y, 178, 27); box.SetBounds(204, y - 3, 484, 29);
            Button browse = new Button(); browse.SetBounds(700, y - 4, 110, 31); browseButtons.Add(browse);
            browse.Click += delegate {
                if (directory) { using (FolderBrowserDialog dialog = new FolderBrowserDialog()) { if (Directory.Exists(box.Text)) dialog.SelectedPath = box.Text; if (dialog.ShowDialog(this) == DialogResult.OK) box.Text = dialog.SelectedPath; } }
                else { using (OpenFileDialog dialog = new OpenFileDialog()) { dialog.Filter = filter; if (dialog.ShowDialog(this) == DialogResult.OK) box.Text = dialog.FileName; } }
            };
            filesPage.Controls.AddRange(new Control[] {label, box, browse});
        }
        void SetMode() {
            bool needsFiles = mode.SelectedIndex == 0;
            baseFile.Enabled = updateFile.Enabled = keysFile.Enabled = needsFiles;
            baseLabel.Enabled = updateLabel.Enabled = keysLabel.Enabled = needsFiles;
            for (int i = 1; i < browseButtons.Count; i++) browseButtons[i].Enabled = needsFiles;
        }
        bool ValidateFields() {
            if (!Path.IsPathRooted(destination.Text)) { MessageBox.Show(this, T("Scegli una cartella di installazione completa.", "Choose an absolute installation folder.")); return false; }
            if (mode.SelectedIndex == 0 && (!File.Exists(baseFile.Text) || !File.Exists(updateFile.Text) || !File.Exists(keysFile.Text))) { MessageBox.Show(this, T("Seleziona gioco base, aggiornamento 1.0.4 e prod.keys della tua console.", "Select your base game, update 1.0.4 and console prod.keys.")); return false; }
            return true;
        }
        void UpdateButtons() {
            back.Enabled = !busy && !finished && tabs.SelectedIndex > 0;
            next.Enabled = !busy && (tabs.SelectedIndex != 1 || (pythonPath != null && compilerFound));
            next.Text = finished ? T("Avvia gioco", "Launch game") : tabs.SelectedIndex == 0 ? T("Avanti", "Next") : tabs.SelectedIndex == 1 ? T("Installa", "Install") : T("Riprova", "Retry");
            cancel.Enabled = !busy || installing; language.Enabled = !busy;
            cancel.Text = busy && installing ? T("Interrompi", "Stop") : T("Chiudi", "Close");
            pythonInstall.Enabled = !busy && pythonPath == null; compilerInstall.Enabled = !busy && !compilerFound;
            choosePython.Enabled = refresh.Enabled = !busy;
        }
        void UpdateStatus() {
            pythonStatus.Text = pythonPath == null ? T("○ Python 3.12 x64 con Tcl/Tk: non rilevato", "○ Python 3.12 x64 with Tcl/Tk: not found") : T("✓ Python 3.12 x64 con Tcl/Tk: disponibile", "✓ Python 3.12 x64 with Tcl/Tk: ready");
            compilerStatus.Text = compilerFound ? T("✓ Microsoft C++ x64 Build Tools: disponibili", "✓ Microsoft C++ x64 Build Tools: ready") : T("○ Microsoft C++ x64 Build Tools: non rilevati", "○ Microsoft C++ x64 Build Tools: not found");
            pythonStatus.ForeColor = pythonPath == null ? Color.FromArgb(135, 75, 10) : Color.FromArgb(20, 110, 65);
            compilerStatus.ForeColor = compilerFound ? Color.FromArgb(20, 110, 65) : Color.FromArgb(135, 75, 10);
        }
        async Task Probe() {
            if (busy) return;
            busy = true; UpdateButtons(); pythonStatus.Text = compilerStatus.Text = T("Controllo...", "Checking...");
            string preferred = manualPython;
            try { string[] found = await Task.Run(delegate { return new string[] {FindPython(preferred), FindCompiler()}; }); pythonPath = found[0]; compilerFound = found[1] != null; }
            finally { busy = false; UpdateStatus(); UpdateButtons(); }
        }
        static string FindPython(string preferred) {
            List<string> candidates = new List<string>(); if (preferred != null) candidates.Add(preferred);
            string py = RunCapture("py.exe", "-3.12 -c " + Quote("import sys;print(sys.executable)"), 10000); if (!String.IsNullOrEmpty(py)) candidates.Add(py.Trim());
            foreach (RegistryKey hive in new RegistryKey[] {Registry.CurrentUser, Registry.LocalMachine}) {
                using (RegistryKey key = hive.OpenSubKey(@"SOFTWARE\Python\PythonCore\3.12\InstallPath")) {
                    if (key != null) { object exe = key.GetValue("ExecutablePath"); object folder = key.GetValue(""); if (exe != null) candidates.Add(exe.ToString()); else if (folder != null) candidates.Add(Path.Combine(folder.ToString(), "python.exe")); }
                }
            }
            candidates.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python312\python.exe"));
            foreach (string candidate in candidates) {
                if (!File.Exists(candidate)) continue;
                string result = RunCapture(candidate, "-c " + Quote("import sys,tkinter;assert sys.version_info[:2]==(3,12) and sys.maxsize>2**32;print(sys.executable)"), 10000);
                if (!String.IsNullOrEmpty(result)) return result.Trim();
            }
            return null;
        }
        static string FindCompiler() {
            string exe = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Microsoft Visual Studio\Installer\vswhere.exe");
            if (!File.Exists(exe)) return null;
            string result = RunCapture(exe, "-latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath", 10000);
            return String.IsNullOrWhiteSpace(result) ? null : result.Trim();
        }
        static string RunCapture(string file, string arguments, int timeout) {
            try {
                ProcessStartInfo info = new ProcessStartInfo(file, arguments); info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true; info.RedirectStandardError = true;
                using (Process process = Process.Start(info)) {
                    Task<string> output = process.StandardOutput.ReadToEndAsync(); Task<string> errors = process.StandardError.ReadToEndAsync();
                    if (!process.WaitForExit(timeout)) { process.Kill(); return null; }
                    Task.WaitAll(output, errors); return process.ExitCode == 0 ? output.Result : null;
                }
            } catch { return null; }
        }
        async Task InstallPrerequisite(bool compiler) {
            string prompt = compiler ? T("Installare Microsoft C++ Build Tools con il carico di lavoro C++? Windows può richiedere privilegi amministratore.", "Install Microsoft C++ Build Tools and the C++ workload? Windows may request administrator privileges.") : T("Installare Python 3.12 per il tuo utente?", "Install Python 3.12 for your user account?");
            if (MessageBox.Show(this, prompt, Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            tabs.SelectedIndex = 2; busy = true; installing = false; finished = false; UpdateButtons();
            string args = compiler ? "install --id Microsoft.VisualStudio.2022.BuildTools --exact --source winget --accept-package-agreements --accept-source-agreements --override " + Quote("--passive --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended") : "install --id Python.Python.3.12 --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements";
            try {
                phase.Text = T("Installazione prerequisito...", "Installing prerequisite...");
                int code = await Task.Run(delegate { return RunProcess("winget.exe", args, null); });
                if (code != 0) MessageBox.Show(this, T("WinGet non ha completato l'installazione. Consulta il log o usa il sito ufficiale.", "WinGet did not complete installation. Check the log or use the official download page."));
            } catch (Exception error) {
                MessageBox.Show(this, error.Message + "\r\n" + T("Aprirò la pagina ufficiale del prerequisito.", "The official prerequisite page will open."));
                Process.Start(compiler ? "https://visualstudio.microsoft.com/visual-cpp-build-tools/" : "https://www.python.org/downloads/windows/");
            } finally { busy = false; activeProcess = null; tabs.SelectedIndex = 1; UpdateButtons(); }
            await Probe();
        }
        async Task Install() {
            if (busy || !ValidateFields() || pythonPath == null || !compilerFound) return;
            string target = destination.Text; bool existing = mode.SelectedIndex == 1;
            tabs.SelectedIndex = 2; busy = true; installing = true; cancelled = false; finished = false; bar.Value = 0; log.Clear(); UpdateButtons();
            try {
                phase.Text = T("Preparazione del setup...", "Preparing setup...");
                cacheRoot = ExtractBundle(null);
                logPath = Path.Combine(cacheRoot, "setup-last.log"); fileLog = new StreamWriter(logPath, false, Encoding.UTF8); fileLog.AutoFlush = true;
                List<string> args = new List<string>(); args.Add("-u"); args.Add(Path.Combine(cacheRoot, @"tools\setup_backend.py")); args.Add("--port-dir"); args.Add(target);
                if (existing) args.Add("--existing"); else { args.Add("--base"); args.Add(baseFile.Text); args.Add("--update"); args.Add(updateFile.Text); args.Add("--keys"); args.Add(keysFile.Text); }
                string arguments = JoinArguments(args);
                int result = await Task.Run(delegate { return RunProcess(pythonPath, arguments, cacheRoot); });
                finished = result == 0 && !cancelled;
                if (finished) { bar.Value = 100; phase.Text = T("Installazione completata", "Installation complete"); progressNote.Text = T("Il collegamento ShareMii è pronto. Crea l'isola e salva prima di usare l'editor. Il primo avvio può preparare ancora gli shader.", "The ShareMii shortcut is ready. Create your island and save before using the editor. The first start may prepare shaders again."); }
                else phase.Text = cancelled ? T("Interrotta: puoi riprendere nella stessa cartella", "Stopped: resume with the same folder") : T("Installazione non completata: consulta il log", "Installation incomplete: check the log");
            } catch (Exception error) { WriteLine(error.Message); phase.Text = T("Installazione non completata", "Installation incomplete"); }
            finally { lock (logSync) { if (fileLog != null) { fileLog.Dispose(); fileLog = null; } } busy = false; installing = false; activeProcess = null; cancel.Text = T("Chiudi", "Close"); UpdateButtons(); }
        }
        int RunProcess(string file, string arguments, string cwd) {
            ProcessStartInfo info = new ProcessStartInfo(file, arguments); info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true; info.RedirectStandardError = true;
            info.StandardOutputEncoding = Encoding.UTF8; info.StandardErrorEncoding = Encoding.UTF8; if (cwd != null) info.WorkingDirectory = cwd;
            using (Process process = new Process()) {
                process.StartInfo = info; process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) WriteLine(e.Data); }; process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) WriteLine(e.Data); };
                process.Start(); activeProcess = process; process.BeginOutputReadLine(); process.BeginErrorReadLine(); process.WaitForExit(); return process.ExitCode;
            }
        }
        void WriteLine(string line) {
            lock (logSync) { if (fileLog != null) fileLog.WriteLine(line); }
            if (IsDisposed || !IsHandleCreated) return;
            BeginInvoke((Action)delegate {
                if (IsDisposed) return;
                if (line.StartsWith("##setup ")) {
                    try {
                        Dictionary<string, object> data = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(line.Substring(8));
                        string stage = Convert.ToString(data["stage"]); int value = Convert.ToInt32(data["percent"]); bar.Value = Math.Max(bar.Value, Math.Max(0, Math.Min(100, value)));
                        Dictionary<string, string> titles = new Dictionary<string, string> { {"validate", T("Controllo installazione", "Checking installation")}, {"download", T("Download strumenti open source", "Downloading open-source tools")}, {"python", T("Preparazione ambiente Python", "Preparing Python environment")}, {"native", T("Compilazione gioco e shader", "Building game and shaders")}, {"integration", T("Installazione menu ShareMii", "Installing ShareMii menu")}, {"done", T("Installazione completata", "Installation complete")}, {"error", T("Operazione interrotta: consulta il log", "Stopped: check the log")} };
                        phase.Text = titles.ContainsKey(stage) ? titles[stage] : stage;
                    } catch { }
                }
                if (log.TextLength > 250000) log.Text = log.Text.Substring(100000);
                log.AppendText(line + Environment.NewLine);
            });
        }
        void StopInstallation() {
            if (!installing || cancelled || activeProcess == null) return;
            if (MessageBox.Show(this, T("Interrompere questa installazione? I passaggi completati restano disponibili per riprendere.", "Stop this installation? Completed steps remain available for resume."), Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            cancelled = true;
            try { string kill = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "taskkill.exe"); RunCapture(kill, "/PID " + activeProcess.Id + " /T /F", 10000); } catch { }
        }
        void LaunchGame() {
            string python = Path.Combine(destination.Text, @"deps\python-venv\Scripts\pythonw.exe"); string script = Path.Combine(destination.Text, @"integration\play-native.py");
            if (!File.Exists(python) || !File.Exists(script)) { MessageBox.Show(this, T("Installazione incompleta.", "Installation is incomplete.")); return; }
            ProcessStartInfo info = new ProcessStartInfo(python, Quote(script)); info.UseShellExecute = false; info.CreateNoWindow = true; info.WorkingDirectory = destination.Text; Process.Start(info);
        }

        static string Hex(byte[] value) { return BitConverter.ToString(value).Replace("-", "").ToLowerInvariant(); }
        static string ExtractBundle(string overrideFolder) {
            Assembly assembly = Assembly.GetExecutingAssembly(); byte[] data;
            using (Stream input = assembly.GetManifestResourceStream("SetupSources")) using (MemoryStream buffer = new MemoryStream()) { input.CopyTo(buffer); data = buffer.ToArray(); }
            string expected; using (StreamReader reader = new StreamReader(assembly.GetManifestResourceStream("SetupSourcesHash"))) expected = reader.ReadToEnd().Trim();
            using (SHA256 sha = SHA256.Create()) if (Hex(sha.ComputeHash(data)) != expected) throw new InvalidDataException("Setup source bundle integrity check failed.");
            string folder = overrideFolder ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "TomodachiLifeShareMiiSetup", expected.Substring(0, 16));
            folder = Path.GetFullPath(folder); Directory.CreateDirectory(folder); string prefix = folder.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            using (MemoryStream stream = new MemoryStream(data)) using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read)) {
                foreach (ZipArchiveEntry entry in archive.Entries) {
                    string destination = Path.GetFullPath(Path.Combine(folder, entry.FullName.Replace('/', Path.DirectorySeparatorChar)));
                    if (!destination.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Invalid setup bundle path.");
                    Directory.CreateDirectory(Path.GetDirectoryName(destination)); using (Stream input = entry.Open()) using (FileStream output = File.Create(destination)) input.CopyTo(output);
                }
            }
            return folder;
        }
        static string JoinArguments(List<string> values) { List<string> quoted = new List<string>(); foreach (string value in values) quoted.Add(Quote(value)); return String.Join(" ", quoted.ToArray()); }
        static string Quote(string value) {
            StringBuilder result = new StringBuilder("\""); int slashes = 0;
            foreach (char c in value) { if (c == '\\') { slashes++; continue; } if (c == '"') { result.Append('\\', slashes * 2 + 1); result.Append(c); slashes = 0; continue; } result.Append('\\', slashes); slashes = 0; result.Append(c); }
            result.Append('\\', slashes * 2); result.Append('"'); return result.ToString();
        }
        public void SelfTest(string workFolder, string snapshot) {
            string root = ExtractBundle(Path.GetFullPath(workFolder));
            if (!File.Exists(Path.Combine(root, @"tools\setup_backend.py"))) throw new Exception("Missing backend payload");
            if (Quote(@"C:\folder with spaces\") != "\"C:\\folder with spaces\\\\\"") throw new Exception("Argument quoting test failed");
            destination.Text = @"C:\Games\TomodachiLife";
            language.SelectedIndex = 1; if (filesPage.Text != "1. Folder and files") throw new Exception("English labels failed");
            mode.SelectedIndex = 1; if (baseFile.Enabled) throw new Exception("Existing installation mode failed");
            mode.SelectedIndex = 0; if (!baseFile.Enabled) throw new Exception("New installation mode failed");
            language.SelectedIndex = 0;
            busy = true; installing = true; UpdateButtons();
            if (cancel.Text != "Interrompi" || next.Enabled) throw new Exception("Installation control state failed");
            busy = false; installing = false; UpdateButtons();
            if (!String.IsNullOrEmpty(snapshot)) {
                ShowInTaskbar = false; StartPosition = FormStartPosition.Manual; Location = new Point(-20000, -20000);
                Show(); PerformLayout(); Application.DoEvents();
                using (Bitmap bitmap = new Bitmap(Width, Height)) {
                    DrawToBitmap(bitmap, new Rectangle(0, 0, Width, Height));
                    Color pixel = bitmap.GetPixel(12, 110);
                    if (pixel.R != 22 || pixel.G != 43 || pixel.B != 73) throw new Exception("The form did not render its controls");
                    bitmap.Save(snapshot);
                }
                Hide();
            }
        }
    }
}
