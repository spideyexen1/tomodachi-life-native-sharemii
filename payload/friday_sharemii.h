#include <wchar.h>
/* Local integration: access to the original ShareMii editor from PC Settings.
 * The game confirms its save before handing off; no save parsing is implemented here. */
static int sm_sel, sm_item, sm_mode, sm_pending;
static const char *sm_note = "Scegli il contenuto e la modalita. Il gioco salva prima di aprire l'editor.";
static const char *const sm_items[] = {"Mii", "Food", "Clothing", "Treasure", "Interior", "Exterior", "Objects", "Landscaping"};
static const char *const sm_item_names[] = {"Mii", "Cibo", "Vestiti", "Tesori", "Interni", "Esterni", "Oggetti", "Paesaggio"};
static const char *const sm_modes[] = {"Import", "Export", "Export All", "List"};
static const char *const sm_mode_names[] = {"Importa", "Esporta", "Esporta tutti", "Elenca"};

static void sm_path(wchar_t *out, const wchar_t *relative) {
    wchar_t exe[32768], joined[32768];
    GetModuleFileNameW(NULL, exe, 32768);
    wchar_t *slash = wcsrchr(exe, L'\\');
    if (slash) *slash = 0;
    _snwprintf(joined, 32767, L"%ls\\..\\..\\%ls", exe, relative);
    joined[32767] = 0;
    GetFullPathNameW(joined, 32768, out, NULL);
}
static void sm_folder(const wchar_t *relative) {
    wchar_t path[32768]; sm_path(path, relative);
    ShellExecuteW(NULL, L"open", path, NULL, NULL, SW_SHOWNORMAL);
}
static int sm_handoff(void) {
    wchar_t python[32768], script[32768], save[32768], command[32768];
    sm_path(python, L"deps\\python-venv\\Scripts\\pythonw.exe");
    sm_path(script, L"integration\\bridge.py");
    DWORD n = GetEnvironmentVariableW(L"SSBU_USERDATA", save, 32000);
    if (!n || n >= 32000) { sm_note = "Cartella salvataggi non disponibile."; return 0; }
    wcscat(save, L"\\save");
    _snwprintf(command, 32767, L"\"%ls\" \"%ls\" --parent-pid %lu --mode \"%hs\" --item \"%hs\" --save \"%ls\"", python, script, GetCurrentProcessId(), sm_modes[sm_mode], sm_items[sm_item], save);
    command[32767] = 0;
    STARTUPINFOW si = {}; si.cb = sizeof si;
    PROCESS_INFORMATION pi = {};
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        printf("sharemii: bridge could not start, error %lu\n", GetLastError()); fflush(stdout);
        sm_note = "Impossibile aprire ShareMii. La partita resta aperta."; return 0;
    }
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    printf("sharemii: save confirmed; handing off %s / %s\n", sm_items[sm_item], sm_modes[sm_mode]); fflush(stdout);
    return 1;
}
static void sm_open(void) {
    g_t_page = 2; sm_sel = 0; sm_pending = 0;
    sm_note = "Scegli il contenuto e la modalita. Il gioco salva prima di aprire l'editor.";
}
static void sm_act(int a) {
    if (sm_pending) return;
    if (a == A_BACK) { g_t_page = 0; return; }
    if (a == A_UP) sm_sel = (sm_sel + 5) % 6;
    else if (a == A_DOWN) sm_sel = (sm_sel + 1) % 6;
    else if (a == A_LEFT || a == A_RIGHT || a == A_OK) {
        int d = a == A_LEFT ? -1 : 1;
        if (sm_sel == 0) sm_item = (sm_item + d + 8) % 8;
        else if (sm_sel == 1) sm_mode = (sm_mode + d + 4) % 4;
        else if (a == A_OK) {
            if (sm_sel == 2) { tomo_save_now(); sm_pending = 1; sm_note = "Salvataggio in corso... poi backup, editor e ritorno al gioco."; }
            else if (sm_sel == 3) sm_folder(L"Scambi");
            else if (sm_sel == 4) sm_folder(L"build\\saves\\sharemii");
            else g_t_page = 0;
        }
    }
}
static void sm_draw(ImDrawList *dl, float bx, float bw, float rx, float ry, float rw, float pitch, float rh, float u, float in, double t, ImVec2 m, bool moved, bool click) {
    if (sm_pending == 1) {
        const int state = tomo_save_state();
        if (state == 3) { sm_pending = 0; if (sm_handoff()) { sm_pending = 2; exit_game(); } }
        else if (state == 4) { sm_pending = 0; sm_note = "Salvataggio non disponibile qui. Torna sull'isola e riprova."; }
    }
    static const char *const labels[] = {"Contenuto", "Modalita", "Salva e apri ShareMii", "Cartella import / export", "Backup automatici", "Indietro"};
    for (int row = 0; row < 6; ++row) {
        ImVec2 a(rx, ry + row * pitch), b(rx + rw, ry + row * pitch + rh);
        bool over = !sm_pending && m.x >= a.x && m.x < b.x && m.y >= a.y && m.y < b.y;
        if (over && moved) sm_sel = row;
        t_card(dl, a, b, u, row == sm_sel && !sm_pending, in, t);
        float cy = (a.y + b.y) * 0.5f;
        t_text(dl, g_ft_row, 38.0f * u, a.x + 44.0f * u, cy, 0, t_col(NAVY, in), labels[row]);
        if (row < 2) t_text(dl, g_ft_row, 38.0f * u, b.x - 44.0f * u, cy, 1, t_col(NAVY, in), row == 0 ? sm_item_names[sm_item] : sm_mode_names[sm_mode]);
        if (over && click) sm_act(row < 2 && m.x < a.x + rw * 0.5f ? A_LEFT : A_OK);
    }
    t_text(dl, g_ft_small, 26.0f * u, bx + bw * 0.5f, ry + 6.5f * pitch, 0.5f, t_col(NAVY, in), sm_note);
    t_text(dl, g_ft_small, 26.0f * u, bx + bw * 0.5f, ry + 7.1f * pitch, 0.5f, t_col(NAVY, in), "ShareMii di Star-F0rce: chiudi l'editor per tornare alla partita.");
}
