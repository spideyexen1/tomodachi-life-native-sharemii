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
#include "friday_mii_queue.h"
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
    g_t_page = 2; sm_sel = 0; sm_pending = 0; sm_q_ui = 0;
    sm_note = sm_qtr("Import all ShareMii categories in game. Export/list open the full editor.", "Importa tutte le categorie dal gioco. Esporta/elenca aprono l'editor completo.", "Alle Kategorien im Spiel importieren. Export/Liste oeffnen den Editor.", "Importa todas las categorias en el juego. Exportar/listar abren el editor.", "Importez toutes les categories dans le jeu. Export/liste ouvrent l'editeur.", "Importe todas as categorias no jogo. Exportar/listar abrem o editor.");
}
static void sm_act(int a) {
    if (sm_pending) return;
    if (sm_q_ui) { sm_q_act(a); return; }
    if (a == A_BACK) { g_t_page = 0; return; }
    if (a == A_UP) sm_sel = (sm_sel + 5) % 6;
    else if (a == A_DOWN) sm_sel = (sm_sel + 1) % 6;
    else if (a == A_LEFT || a == A_RIGHT || a == A_OK) {
        int d = a == A_LEFT ? -1 : 1;
        if (sm_sel == 0) sm_item = (sm_item + d + 8) % 8;
        else if (sm_sel == 1) sm_mode = (sm_mode + d + 4) % 4;
        else if (a == A_OK) {
            if (sm_sel == 2) {
                tomo_save_now();
                if (sm_mode == 0) {
                    sm_pending = 5;
                    sm_note = sm_qtr("Saving before opening the import queue...", "Salvataggio prima di aprire la coda importazioni...", "Speichern vor der Mii-Warteschlange...", "Guardando antes de abrir la cola Mii...", "Sauvegarde avant la file Mii...", "Salvando antes de abrir a fila Mii...");
                } else { sm_pending = 1; sm_note = "Salvataggio in corso... poi backup, editor e ritorno al gioco."; }
            }
            else if (sm_sel == 3) sm_folder(L"Scambi");
            else if (sm_sel == 4) sm_folder(L"build\\saves\\sharemii");
            else g_t_page = 0;
        }
    }
}
static void sm_draw(ImDrawList *dl, float bx, float bw, float rx, float ry, float rw, float pitch, float rh, float u, float in, double t, ImVec2 m, bool moved, bool click) {
    if (sm_pending == 5) {
        int state = tomo_save_state();
        if (state == 3) { sm_pending = 0; sm_q_open(); }
        else if (state == 4) { sm_pending = 0; sm_note = sm_qtr("Return to the island and save first.", "Torna sull'isola e salva prima.", "Zuerst auf der Insel speichern.", "Vuelve a la isla y guarda primero.", "Retournez sur l'ile et sauvegardez.", "Volte a ilha e salve primeiro."); }
    }
    if (sm_q_ui) { sm_q_draw(dl, bx, bw, rx, ry, rw, pitch, rh, u, in, t, m, moved, click); return; }
    if (sm_pending == 1) {
        const int state = tomo_save_state();
        if (state == 3) { sm_pending = 0; if (sm_handoff()) { sm_pending = 2; exit_game(); } }
        else if (state == 4) { sm_pending = 0; sm_note = "Salvataggio non disponibile qui. Torna sull'isola e riprova."; }
    }
    const char *labels[] = {
        sm_qtr("Content", "Contenuto", "Inhalt", "Contenido", "Contenu", "Conteudo"),
        sm_qtr("Mode", "Modalita", "Modus", "Modo", "Mode", "Modo"),
        sm_qtr("Save and open ShareMii", "Salva e apri ShareMii", "Speichern und ShareMii oeffnen", "Guardar y abrir ShareMii", "Sauvegarder et ouvrir ShareMii", "Salvar e abrir ShareMii"),
        sm_qtr("Import / export folder", "Cartella import / export", "Import- / Exportordner", "Carpeta importacion / exportacion", "Dossier import / export", "Pasta importacao / exportacao"),
        sm_qtr("Automatic backups", "Backup automatici", "Automatische Sicherungen", "Copias automaticas", "Sauvegardes automatiques", "Copias automaticas"),
        sm_qtr("Back", "Indietro", "Zurueck", "Volver", "Retour", "Voltar")};
    const char *modes[] = {sm_qtr("Import", "Importa", "Importieren", "Importar", "Importer", "Importar"),
        sm_qtr("Export", "Esporta", "Exportieren", "Exportar", "Exporter", "Exportar"),
        sm_qtr("Export all", "Esporta tutti", "Alle exportieren", "Exportar todos", "Tout exporter", "Exportar todos"),
        sm_qtr("List", "Elenca", "Auflisten", "Listar", "Lister", "Listar")};
    for (int row = 0; row < 6; ++row) {
        ImVec2 a(rx, ry + row * pitch), b(rx + rw, ry + row * pitch + rh);
        bool over = !sm_pending && m.x >= a.x && m.x < b.x && m.y >= a.y && m.y < b.y;
        if (over && moved) sm_sel = row;
        t_card(dl, a, b, u, row == sm_sel && !sm_pending, in, t);
        float cy = (a.y + b.y) * 0.5f;
        const char *label = row == 2 && sm_mode == 0 ? sm_qtr("Import files in game", "Importa dal gioco", "Dateien im Spiel importieren", "Importar desde el juego", "Importer dans le jeu", "Importar no jogo") : labels[row];
        t_text(dl, g_ft_row, 38.0f * u, a.x + 44.0f * u, cy, 0, t_col(NAVY, in), label);
        if (row < 2) t_text(dl, g_ft_row, 38.0f * u, b.x - 44.0f * u, cy, 1, t_col(NAVY, in), row == 0 ? sm_q_category(sm_item) : modes[sm_mode]);
        if (over && click) { sm_sel = row; sm_act(row < 2 && m.x < a.x + rw * 0.5f ? A_LEFT : A_OK); }
    }
    t_text(dl, g_ft_small, 26.0f * u, bx + bw * 0.5f, ry + 6.5f * pitch, 0.5f, t_col(NAVY, in), sm_note);
    t_text(dl, g_ft_small, 26.0f * u, bx + bw * 0.5f, ry + 7.1f * pitch, 0.5f, t_col(NAVY, in), sm_mode == 0 ? sm_qtr("Queue Miis and items across categories, then apply with one reload.", "Accoda Mii e oggetti di piu categorie, poi applica con un solo ricaricamento.", "Mehrere Miis einreihen und mit einmaligem Neuladen anwenden.", "Agrega varios Mii y aplicalos con una sola recarga automatica.", "Ajoutez plusieurs Mii puis appliquez-les avec un seul rechargement.", "Adicione varios Mii e aplique-os com uma unica recarga automatica.") : "ShareMii di Star-F0rce: chiudi l'editor per tornare alla partita.");
}
