/* SPDX-License-Identifier: GPL-3.0-only
 * In-game batch selection. Only a confirmed game save is handed to the offline
 * transaction helper; the original ShareMii GUI is never opened for this path. */
#include <commdlg.h>
#include "friday_queue_types.h"

static const char *sm_qtr(const char *en, const char *it, const char *de, const char *es, const char *fr, const char *pt) {
    switch (PRIMARYLANGID(GetUserDefaultUILanguage())) {
    case LANG_ITALIAN: return it; case LANG_GERMAN: return de; case LANG_SPANISH: return es;
    case LANG_FRENCH: return fr; case LANG_PORTUGUESE: return pt; default: return en;
    }
}
static const char *sm_q_category(int kind) {
    switch (kind) {
    case 1: return sm_qtr("Food", "Cibo", "Essen", "Comida", "Nourriture", "Comida");
    case 2: return sm_qtr("Clothing", "Vestiti", "Kleidung", "Ropa", "Vetements", "Roupas");
    case 3: return sm_qtr("Treasure", "Tesori", "Schaetze", "Tesoros", "Tresors", "Tesouros");
    case 4: return sm_qtr("Interiors", "Interni", "Innenraeume", "Interiores", "Interieurs", "Interiores");
    case 5: return sm_qtr("Exteriors", "Esterni", "Aussenbereiche", "Exteriores", "Exterieurs", "Exteriores");
    case 6: return sm_qtr("Objects", "Oggetti", "Objekte", "Objetos", "Objets", "Objetos");
    case 7: return sm_qtr("Landscaping", "Paesaggio", "Landschaft", "Paisaje", "Paysage", "Paisagem");
    default: return "Mii";
    }
}
static SmString sm_utf8(const SmWString& value) {
    if (value.empty()) return {};
    int n = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), (int)value.size(), NULL, 0, NULL, NULL);
    if (n <= 0) return "?";
    SmString out((size_t)n, '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), (int)value.size(), &out[0], n, NULL, NULL);
    return out;
}
static SmString sm_short(SmString s, size_t n = 46) {
    if (s.size() <= n) return s;
    while (n && ((unsigned char)s[n] & 0xc0) == 0x80) --n;
    return s.substr(0, n) + "...";
}
struct SmResident { int slot; SmString name; };
struct SmQueuedMii { int slot; SmWString file; SmString name; int kind; int model; int fit; };
static SmVector<SmResident> sm_residents;
static SmVector<SmResident> sm_ugc_slots[7], sm_models[7];
static int sm_model_start[7];
static const wchar_t *const sm_extensions[] = {L".ltd", L".ltdf", L".ltdc", L".ltdg", L".ltdi", L".ltde", L".ltdo", L".ltdl"};
static const wchar_t *const sm_ugc_types[] = {L"Food", L"Cloth", L"Goods", L"Interior", L"Exterior", L"MapObject", L"MapFloor"};
static int sm_pick_kind, sm_pick_photo, sm_pick_fit;
static SmVector<SmResident>& sm_q_slots(int kind) { return kind ? sm_ugc_slots[kind - 1] : sm_residents; }
static SmVector<SmQueuedMii> sm_queue;
static SmVector<SmWString> sm_picked;
static SmString sm_q_message;
static int sm_q_ui, sm_q_sel, sm_q_index, sm_q_start, sm_q_confirm;
static volatile LONG sm_pick_state;
static HWND sm_pick_owner;
static void sm_qsay(const SmString& text) { sm_q_message = text; sm_note = sm_q_message.c_str(); }
static uint32_t sm_u32(const SmVector<unsigned char>& b, size_t at) {
    uint32_t v = 0; if (at <= b.size() && b.size() - at >= 4) memcpy(&v, b.data() + at, 4); return v;
}
static bool sm_q_save_path(wchar_t *save) {
    DWORD n = GetEnvironmentVariableW(L"SSBU_USERDATA", save, 32000);
    if (!n || n >= 32000) return false;
    wcscat(save, L"\\save"); return true;
}
static bool sm_q_residents(void) {
    sm_residents.clear();
    wchar_t save[32768]; if (!sm_q_save_path(save)) return false;
    SmWString file = SmWString(save) + L"\\Mii.sav";
    FILE *f = _wfopen(file.c_str(), L"rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long size = ftell(f); rewind(f);
    if (size < 32 || size > 16 * 1024 * 1024) { fclose(f); return false; }
    SmVector<unsigned char> b((size_t)size);
    bool ok = fread(b.data(), 1, b.size(), f) == b.size(); fclose(f);
    if (!ok || sm_u32(b, 0) != 0x01020304) return false;
    size_t heap = sm_u32(b, 8), raw = 0, names = 0;
    if (heap < 32 || heap > b.size()) return false;
    for (size_t at = 32; at + 8 <= heap; at += 8) {
        if (sm_u32(b, at) == 0x881ca27a) raw = (size_t)sm_u32(b, at + 4) + 4;
        if (sm_u32(b, at) == 0x2499bfda) names = (size_t)sm_u32(b, at + 4) + 4;
    }
    if (!raw || !names || raw + 70 * 156 > b.size() || names + 70 * 64 > b.size()) return false;
    SmVector<SmResident> found;
    for (int slot = 0; slot < 70; ++slot) {
        unsigned sum = 0; for (int j = 0; j < 156; ++j) sum += b[raw + slot * 156 + j];
        if (sum == 152 || sm_u32(b, raw + slot * 156) != 152) continue;
        wchar_t name[33] = {}; memcpy(name, b.data() + names + slot * 64, 64);
        SmString label = sm_utf8(name); if (label.empty()) label = "Mii " + sm_number(slot + 1);
        found.push_back({slot + 1, label});
    }
    sm_residents.swap(found); return !sm_residents.empty();
}
static bool sm_q_destinations(void) {
    sm_q_residents();
    for (auto& slots : sm_ugc_slots) slots.clear();
    for (auto& models : sm_models) models.clear();
    wchar_t save[32768]; if (!sm_q_save_path(save)) return false;
    SmWString file = SmWString(save) + L"\\Player.sav";
    FILE *f = _wfopen(file.c_str(), L"rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long size = ftell(f); rewind(f);
    if (size < 32 || size > 32 * 1024 * 1024) { fclose(f); return false; }
    SmVector<unsigned char> bytes((size_t)size);
    bool ok = fread(bytes.data(), 1, bytes.size(), f) == bytes.size(); fclose(f);
    size_t heap = sm_u32(bytes, 8);
    if (!ok || sm_u32(bytes, 0) != 0x01020304 || heap < 32 || heap > bytes.size()) return false;
    const uint32_t keys[] = {0xf4a39965,0xaf129c33,0x1a9c00fe,0xa39744e9,0xf4beadc2,0x5951050b,0xa1126d32};
    const uint32_t name_keys[] = {0x408494f5,0x40710642,0x2f793eb1,0x3de2c5dd,0x27c875d6,0x56f99338,0x918875a9};
    for (int kind = 0; kind < 7; ++kind) {
        size_t enabled = 0, names = 0; int maximum = kind == 1 ? 299 : 99;
        for (size_t at = 32; at + 8 <= heap; at += 8) {
            if (sm_u32(bytes, at) == keys[kind]) enabled = (size_t)sm_u32(bytes, at + 4) + 4;
            if (sm_u32(bytes, at) == name_keys[kind]) names = (size_t)sm_u32(bytes, at + 4) + 4;
        }
        if (enabled < heap || enabled + maximum * 4 > bytes.size()) continue;
        for (int index = 0; index < maximum; ++index) {
            uint32_t flag = sm_u32(bytes, enabled + index * 4);
            int present = 0;
            const wchar_t *suffixes[] = {L".canvas.zs", L".ugctex.zs", L"_Thumb.ugctex.zs"};
            for (auto suffix : suffixes) {
                wchar_t relative[128]; _snwprintf(relative, 127, L"\\Ugc\\Ugc%ls%03d%ls", sm_ugc_types[kind], index, suffix); relative[127] = 0;
                if (GetFileAttributesW((SmWString(save) + relative).c_str()) != INVALID_FILE_ATTRIBUTES) ++present;
            }
            if ((flag == 0 || flag == 0xafff8aa5) && !present && index < (kind == 1 ? 256 : 99))
                sm_ugc_slots[kind].push_back({index + 1, "#" + sm_number(index + 1)});
            if (flag == 0x1d7fadf4 && present == 3 && names >= heap && names + (index + 1) * 128 <= bytes.size()) {
                wchar_t name[65] = {}; memcpy(name, bytes.data() + names + index * 128, 128);
                SmString label = sm_utf8(name); if (label.empty()) label = "#" + sm_number(index + 1);
                sm_models[kind].push_back({index + 1, label});
            }
        }
    }
    return !sm_q_slots(sm_item).empty();
}
static const char *sm_q_resident_name(int slot, int kind) {
    for (auto& resident : sm_q_slots(kind)) if (resident.slot == slot) return resident.name.c_str();
    return "?";
}
static bool sm_q_used(int slot, int kind, int except = -1) {
    for (int i = 0; i < (int)sm_queue.size(); ++i) if (i != except && sm_queue[i].kind == kind && sm_queue[i].slot == slot) return true;
    return false;
}
static DWORD WINAPI sm_q_picker(void *) {
        HMODULE dll = LoadLibraryW(L"comdlg32.dll");
        if (!dll) { InterlockedExchange(&sm_pick_state, 4); return 0; }
        typedef BOOL (WINAPI *PickFn)(LPOPENFILENAMEW);
        typedef DWORD (WINAPI *ErrorFn)(void);
        PickFn pick = (PickFn)GetProcAddress(dll, "GetOpenFileNameW");
        ErrorFn error = (ErrorFn)GetProcAddress(dll, "CommDlgExtendedError");
        SmVector<wchar_t> buffer(65536, 0);
        OPENFILENAMEW ofn = {}; ofn.lStructSize = sizeof ofn; ofn.hwndOwner = sm_pick_owner;
        const wchar_t *filters[] = {L"Mii (*.ltd)\0*.ltd\0\0", L"Food (*.ltdf)\0*.ltdf\0\0", L"Clothing (*.ltdc)\0*.ltdc\0\0", L"Treasure (*.ltdg)\0*.ltdg\0\0", L"Interior (*.ltdi)\0*.ltdi\0\0", L"Exterior (*.ltde)\0*.ltde\0\0", L"Objects (*.ltdo)\0*.ltdo\0\0", L"Landscaping (*.ltdl)\0*.ltdl\0\0"};
        ofn.lpstrFilter = sm_pick_photo ? L"JPEG / PNG\0*.jpg;*.jpeg;*.png\0\0" : filters[sm_pick_kind]; ofn.lpstrFile = buffer.data(); ofn.nMaxFile = (DWORD)buffer.size();
        ofn.Flags = OFN_EXPLORER | OFN_ALLOWMULTISELECT | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR;
        sm_picked.clear();
        if (pick && pick(&ofn)) {
            SmWString first = buffer.data(); const wchar_t *next = buffer.data() + first.size() + 1;
            if (!*next) sm_picked.push_back(first);
            else while (*next) { sm_picked.push_back(first + L"\\" + next); next += wcslen(next) + 1; }
            FreeLibrary(dll); InterlockedExchange(&sm_pick_state, 2);
        } else { DWORD e = error ? error() : 1; FreeLibrary(dll); InterlockedExchange(&sm_pick_state, e ? 4 : 3); }
    return 0;
}
static void sm_q_pick(void) {
    sm_pick_kind = sm_item; sm_pick_photo = sm_mode >= 4; sm_pick_fit = sm_mode >= 4 ? sm_mode - 4 : 0; sm_pick_owner = GetActiveWindow(); InterlockedExchange(&sm_pick_state, 1);
    HANDLE thread = CreateThread(NULL, 0, sm_q_picker, NULL, 0, NULL);
    if (thread) CloseHandle(thread); else sm_pick_state = 4;
}
static bool sm_q_preview(const SmWString& path, SmString& name, int kind) {
    FILE *f = _wfopen(path.c_str(), L"rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long size = ftell(f); rewind(f);
    unsigned char head[436] = {}; size_t n = fread(head, 1, sizeof head, f); fclose(f);
    size_t dot = path.find_last_of(L".");
    if (dot == SmWString::npos || _wcsicmp(path.substr(dot).c_str(), sm_extensions[kind]) || size > 64 * 1024 * 1024) return false;
    if (kind) {
        const int counts[] = {10,10,17,8,11,13,8}; size_t at = 4 + counts[kind - 1] * 4 + 24;
        if (n < at + 128 || head[0] != kind - 1 || head[1] || head[2] || head[3] || memcmp(head + at - 4, "\xa2\xa2\xa2\xa2", 4)) return false;
        wchar_t text[65] = {}; memcpy(text, head + at, 128); name = sm_utf8(text);
    } else {
    if (size > 64 * 1024 * 1024 || n < 161 || head[0] < 1 || head[0] > 3 ||
        (head[0] == 2 && n < 428) || (head[0] == 3 && n < 428)) return false;
    if (head[0] == 3) { wchar_t text[33] = {}; memcpy(text, head + 232, 64); name = sm_utf8(text); }
    }
    if (name.empty()) { size_t slash = path.find_last_of(L"\\/"); name = sm_utf8(path.substr(slash == SmWString::npos ? 0 : slash + 1)); }
    return true;
}
static bool sm_q_photo_preview(const SmWString& path, SmString& name) {
    size_t dot = path.find_last_of(L".");
    if (dot == SmWString::npos) return false;
    SmWString ext = path.substr(dot);
    if (_wcsicmp(ext.c_str(), L".png") && _wcsicmp(ext.c_str(), L".jpg") && _wcsicmp(ext.c_str(), L".jpeg")) return false;
    FILE *f = _wfopen(path.c_str(), L"rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long size = ftell(f); rewind(f);
    unsigned char signature[8] = {}; size_t n = fread(signature, 1, 8, f); fclose(f);
    if (size < 8 || size > 64 * 1024 * 1024 || n != 8 ||
        (memcmp(signature, "\x89PNG\r\n\x1a\n", 8) && !(signature[0] == 0xff && signature[1] == 0xd8 && signature[2] == 0xff))) return false;
    size_t slash = path.find_last_of(L"\\/"); name = sm_utf8(path.substr(slash == SmWString::npos ? 0 : slash + 1));
    return true;
}
static void sm_q_collect(void) {
    LONG state = InterlockedCompareExchange(&sm_pick_state, 0, 0); if (state != 2 && state != 3 && state != 4) return;
    InterlockedExchange(&sm_pick_state, 0); sm_q_confirm = 0;
    if (state == 3) return;
    if (state == 4) { sm_qsay(sm_qtr("File selection failed.", "Selezione file non riuscita.", "Dateiauswahl fehlgeschlagen.", "No se pudo seleccionar el archivo.", "Echec de selection du fichier.", "Falha ao selecionar arquivo.")); return; }
    SmVector<int> slots;
    auto& destinations = sm_q_slots(sm_pick_kind);
    for (size_t i = 0; i < destinations.size(); ++i) {
        int slot = destinations[(sm_q_start + i) % destinations.size()].slot;
        if (!sm_q_used(slot, sm_pick_kind)) slots.push_back(slot);
    }
    if (sm_picked.size() > slots.size() || sm_queue.size() + sm_picked.size() > 70) {
        sm_qsay(sm_qtr("Not enough destinations or queue full (70). Miis need existing residents; items need free slots.", "Destinazioni insufficienti o coda piena (70). Mii: abitanti esistenti; oggetti: slot liberi.", "Nicht genug Ziele oder Warteschlange voll (70).", "Faltan destinos o cola llena (70).", "Destinations insuffisantes ou file pleine (70).", "Destinos insuficientes ou fila cheia (70).")); return;
    }
    SmVector<SmQueuedMii> added;
    for (size_t i = 0; i < sm_picked.size(); ++i) {
        SmString name;
        if (!(sm_pick_photo ? sm_q_photo_preview(sm_picked[i], name) : sm_q_preview(sm_picked[i], name, sm_pick_kind))) { sm_qsay(sm_qtr("Invalid or incomplete file.", "File non valido o incompleto.", "Ungueltige ShareMii-Datei.", "Archivo ShareMii no valido.", "Fichier ShareMii invalide.", "Arquivo ShareMii invalido.")); return; }
        added.push_back({slots[i], sm_picked[i], name, sm_pick_kind, sm_pick_photo ? sm_models[sm_pick_kind - 1][sm_model_start[sm_pick_kind - 1]].slot : 0, sm_pick_fit});
    }
    sm_q_index = (int)sm_queue.size(); sm_queue.insert(sm_queue.end(), added.begin(), added.end());
    sm_qsay(sm_qtr("Review each file and its destination, then apply the whole queue.", "Controlla ogni file e la destinazione, poi applica tutta la coda.", "Dateien und Ziele pruefen, dann anwenden.", "Revisa cada archivo y destino, luego aplica la cola.", "Verifiez chaque fichier et destination, puis appliquez la file.", "Revise cada arquivo e destino, depois aplique a fila."));
}
static SmString sm_q_json(const SmWString& value) {
    SmString out = "\"";
    for (unsigned char c : sm_utf8(value)) {
        if (c == '"' || c == '\\') { out += '\\'; out += (char)c; }
        else if (c < 32) { char escaped[8]; snprintf(escaped, sizeof escaped, "\\u%04x", c); out += escaped; }
        else out += (char)c;
    }
    return out + "\"";
}
static bool sm_q_handoff(void) {
    wchar_t python[32768], script[32768], ticket[32768], save[32768], command[32768], relative[160];
    if (!sm_q_save_path(save)) return false;
    sm_path(python, L"deps\\python-venv\\Scripts\\pythonw.exe"); sm_path(script, L"integration\\mii_import.py");
    _snwprintf(relative, 159, L"integration\\mii-request-%lu-%llu.json", GetCurrentProcessId(), (unsigned long long)GetTickCount64());
    relative[159] = 0; sm_path(ticket, relative);
    SmString json = "{\"schema\":1,\"save\":" + sm_q_json(save) + ",\"entries\":[";
    for (size_t i = 0; i < sm_queue.size(); ++i) {
        if (i) json += ',';
        json += "{\"kind\":" + sm_number(sm_queue[i].kind) + ",\"slot\":" + sm_number(sm_queue[i].slot) + ",\"file\":" + sm_q_json(sm_queue[i].file);
        if (sm_queue[i].model) {
            const char *fits[] = {"contain", "cover", "stretch"};
            json += ",\"photo\":true,\"template\":" + sm_number(sm_queue[i].model) + ",\"fit\":\"" + fits[sm_queue[i].fit] + "\"";
        }
        json += '}';
    }
    json += "]}";
    FILE *f = _wfopen(ticket, L"wb"); if (!f) return false;
    bool written = fwrite(json.data(), 1, json.size(), f) == json.size(); if (fclose(f)) written = false;
    if (!written) { DeleteFileW(ticket); return false; }
    _snwprintf(command, 32767, L"\"%ls\" \"%ls\" --parent-pid %lu --request \"%ls\"", python, script, GetCurrentProcessId(), ticket); command[32767] = 0;
    STARTUPINFOW si = {}; si.cb = sizeof si; PROCESS_INFORMATION pi = {};
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) { DeleteFileW(ticket); return false; }
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    printf("sharemii: committed save; queued %zu ShareMii creations for one automatic reload\n", sm_queue.size()); fflush(stdout);
    return true;
}
static void sm_q_open(void) {
    if (sm_mode >= 4 && sm_item == 0) { sm_qsay(sm_qtr("Photos need an item category, not Mii.", "Per le foto scegli una categoria di oggetti, non Mii.", "Fotos brauchen eine Objektkategorie.", "Elige una categoria de objetos para fotos.", "Choisissez une categorie d'objets pour les photos.", "Escolha uma categoria de objetos para fotos.")); return; }
    if (!sm_q_destinations()) { sm_qsay(sm_qtr("No destinations available. Miis need residents; items need free slots.", "Nessuna destinazione: per i Mii crea abitanti; per gli oggetti servono slot liberi.", "Keine Ziele: Miis brauchen Bewohner, Objekte freie Plaetze.", "Sin destinos: los Mii requieren residentes, los objetos espacios libres.", "Aucune destination : residents pour les Mii, places libres pour les objets.", "Sem destinos: Miis precisam de residentes, objetos de espacos livres.")); return; }
    if (sm_mode >= 4) {
        auto& models = sm_models[sm_item - 1];
        if (models.empty()) { sm_qsay(sm_qtr("Create and save a model in Palette House for this category first.", "Crea e salva prima un modello di questa categoria nella Casa dei colori.", "Zuerst ein Modell dieser Kategorie im Spiel erstellen und speichern.", "Crea y guarda primero un modelo de esta categoria en el juego.", "Creez et sauvegardez d'abord un modele de cette categorie dans le jeu.", "Crie e salve primeiro um modelo desta categoria no jogo.")); return; }
        sm_model_start[sm_item - 1] %= (int)models.size();
    }
    sm_q_ui = 1; sm_q_sel = 2; sm_q_confirm = 0;
    sm_q_start %= (int)sm_q_slots(sm_item).size();
    if (sm_q_index >= (int)sm_queue.size()) sm_q_index = 0;
    if (sm_mode >= 4) sm_qsay(sm_qtr("Add JPG/PNG photos, then review the model for each entry. Original models stay unchanged.", "Aggiungi foto JPG/PNG e controlla il modello di ogni voce. I modelli originali restano invariati.", "JPG/PNG hinzufuegen und jedes Modell pruefen. Originale bleiben unveraendert.", "Agrega fotos JPG/PNG y revisa cada modelo. Los originales se conservan.", "Ajoutez des photos JPG/PNG et verifiez chaque modele. Les originaux sont conserves.", "Adicione fotos JPG/PNG e revise cada modelo. Os originais sao preservados."));
    else sm_qsay(sm_qtr("Add files for the selected category. Miis replace residents; items use free slots.", "Aggiungi file della categoria scelta. I Mii sostituiscono abitanti; gli oggetti usano slot liberi.", "Kategorie-Dateien hinzufuegen. Miis ersetzen Bewohner; Objekte brauchen freie Plaetze.", "Agrega archivos de la categoria. Mii: sustituir residentes; objetos: espacios libres.", "Ajoutez les fichiers. Mii : remplacement de residents ; objets : places libres.", "Adicione arquivos. Miis substituem residentes; objetos usam espacos livres."));
}
static void sm_q_act(int action) {
    if (sm_pending || sm_pick_state == 1) return;
    if (action == A_BACK) { sm_q_ui = 0; return; }
    if (action == A_UP) sm_q_sel = (sm_q_sel + 5) % 6;
    else if (action == A_DOWN) sm_q_sel = (sm_q_sel + 1) % 6;
    else if (action == A_LEFT || action == A_RIGHT || action == A_OK) {
        int d = action == A_LEFT ? -1 : 1;
        if (sm_q_sel == 0) {
            bool photo = sm_queue.empty() ? sm_mode >= 4 : sm_queue[sm_q_index].model != 0;
            if (photo) {
                int kind = sm_queue.empty() ? sm_item : sm_queue[sm_q_index].kind;
                auto& models = sm_models[kind - 1]; if (models.empty()) return;
                int current = sm_queue.empty() ? models[sm_model_start[kind - 1]].slot : sm_queue[sm_q_index].model;
                int index = 0; for (int i = 0; i < (int)models.size(); ++i) if (models[i].slot == current) index = i;
                index = (index + d + (int)models.size()) % (int)models.size();
                sm_model_start[kind - 1] = index;
                if (!sm_queue.empty()) sm_queue[sm_q_index].model = models[index].slot;
                sm_q_confirm = 0; return;
            }
            int kind = sm_queue.empty() ? sm_item : sm_queue[sm_q_index].kind;
            auto& destinations = sm_q_slots(kind);
            if (destinations.empty()) return;
            int current = sm_queue.empty() ? destinations[sm_q_start % destinations.size()].slot : sm_queue[sm_q_index].slot;
            int index = 0; for (int i = 0; i < (int)destinations.size(); ++i) if (destinations[i].slot == current) index = i;
            for (size_t i = 0; i < destinations.size(); ++i) {
                index = (index + d + (int)destinations.size()) % (int)destinations.size();
                if (!sm_queue.empty()) {
                    int destination = destinations[index].slot;
                    for (int j = 0; j < (int)sm_queue.size(); ++j)
                        if (j != sm_q_index && sm_queue[j].kind == kind && sm_queue[j].slot == destination) sm_queue[j].slot = current;
                    sm_queue[sm_q_index].slot = destination;
                    sm_qsay(sm_qtr("A destination used by another queue entry swaps their assignments.", "Una destinazione gia usata in coda scambia le due assegnazioni.", "Ziele pruefen: belegte Ziele tauschen die beiden Mii-Zuweisungen.", "Revisa los destinos: uno ocupado intercambia los dos Mii de la cola.", "Verifiez les destinations : une destination occupee echange les deux Mii.", "Revise os destinos: um destino ocupado troca os dois Miis na fila."));
                    break;
                }
                if (!sm_q_used(destinations[index].slot, kind, sm_queue.empty() ? -1 : sm_q_index)) {
                    if (sm_queue.empty()) sm_q_start = index; else sm_queue[sm_q_index].slot = destinations[index].slot;
                    break;
                }
            }
            sm_q_confirm = 0;
        } else if (sm_q_sel == 1 && !sm_queue.empty()) { sm_q_index = (sm_q_index + d + (int)sm_queue.size()) % (int)sm_queue.size(); sm_q_confirm = 0; }
        else if (action == A_OK) {
            if (sm_q_sel == 2) sm_q_pick();
            else if (sm_q_sel == 3 && !sm_queue.empty()) { sm_queue.erase(sm_queue.begin() + sm_q_index); if (sm_q_index >= (int)sm_queue.size()) sm_q_index = 0; sm_q_confirm = 0; }
            else if (sm_q_sel == 4 && !sm_queue.empty()) {
                if (!sm_q_confirm) { sm_q_confirm = 1; sm_qsay(sm_qtr("Confirm again to apply ALL queued creations and reload once.", "Conferma ancora per applicare TUTTE le creazioni in coda e ricaricare una volta.", "Erneut bestaetigen: alle Eintraege anwenden und einmal neu laden.", "Confirma otra vez para aplicar toda la cola y recargar una vez.", "Confirmez encore pour appliquer toute la file et recharger.", "Confirme novamente para aplicar toda a fila e recarregar uma vez.")); }
                else { tomo_save_now(); sm_pending = 3; sm_qsay(sm_qtr("Saving... then backup, batch import and automatic reload.", "Salvataggio... poi backup, importazione della coda e ricaricamento automatico.", "Speichern... dann Sicherung, Stapelimport und automatisches Neuladen.", "Guardando... copia, importacion de la cola y recarga automatica.", "Sauvegarde... copie, import de la file et rechargement automatique.", "Salvando... copia, importacao da fila e recarga automatica.")); }
            } else if (sm_q_sel == 5) sm_q_ui = 0;
        }
    }
}
static void sm_q_draw(ImDrawList *dl, float bx, float bw, float rx, float ry, float rw, float pitch, float rh, float u, float in, double t, ImVec2 mouse, bool moved, bool click) {
    sm_q_collect();
    if (sm_pending == 3) {
        int state = tomo_save_state();
        if (state == 3) {
            sm_pending = 0;
            if (sm_q_handoff()) { sm_pending = 4; exit_game(); }
            else sm_qsay(sm_qtr("Could not start import. The game stays open.", "Avvio importazione non riuscito. Il gioco resta aperto.", "Import nicht gestartet. Das Spiel bleibt offen.", "No se pudo iniciar. El juego sigue abierto.", "Import non demarre. Le jeu reste ouvert.", "Nao foi possivel iniciar. O jogo continua aberto."));
        } else if (state == 4) { sm_pending = 0; sm_q_confirm = 0; sm_qsay(sm_qtr("Cannot save here. Return to the island and try again.", "Non puoi salvare qui. Torna sull'isola e riprova.", "Hier nicht speicherbar. Auf der Insel erneut versuchen.", "No se puede guardar aqui. Vuelve a la isla.", "Sauvegarde impossible ici. Retournez sur l'ile.", "Nao e possivel salvar aqui. Volte a ilha.")); }
    }
    bool selected_photo = sm_queue.empty() ? sm_mode >= 4 : sm_queue[sm_q_index].model != 0;
    const char *labels[] = {
        selected_photo ? sm_qtr("Photo model", "Modello foto", "Fotomodell", "Modelo de foto", "Modele photo", "Modelo de foto") : sm_qtr("Destination", "Destinazione", "Ziel", "Destino", "Destination", "Destino"),
        sm_qtr("Review queued creation", "Rivedi creazione in coda", "Eintrag pruefen", "Revisar creacion en cola", "Revoir la creation en attente", "Revisar criacao na fila"),
        sm_mode >= 4 ? sm_qtr("Add JPG / PNG...", "Aggiungi JPG / PNG...", "JPG / PNG hinzufuegen...", "Agregar JPG / PNG...", "Ajouter JPG / PNG...", "Adicionar JPG / PNG...") : sm_qtr("Add files...", "Aggiungi file...", "Dateien hinzufuegen...", "Agregar archivos...", "Ajouter des fichiers...", "Adicionar arquivos..."),
        sm_qtr("Remove selected creation", "Rimuovi creazione selezionata", "Eintrag entfernen", "Quitar creacion seleccionada", "Retirer la creation choisie", "Remover criacao selecionada"),
        sm_qtr("Apply queue and reload", "Applica coda e ricarica", "Anwenden und neu laden", "Aplicar cola y recargar", "Appliquer et recharger", "Aplicar fila e recarregar"),
        sm_qtr("Back", "Indietro", "Zurueck", "Volver", "Retour", "Voltar")};
    for (int row = 0; row < 6; ++row) {
        ImVec2 a(rx, ry + row * pitch), b(rx + rw, ry + row * pitch + rh);
        bool over = !sm_pending && sm_pick_state != 1 && mouse.x >= a.x && mouse.x < b.x && mouse.y >= a.y && mouse.y < b.y;
        if (over && moved) sm_q_sel = row;
        t_card(dl, a, b, u, row == sm_q_sel && !sm_pending, in, t);
        float cy = (a.y + b.y) * 0.5f;
        t_text(dl, g_ft_row, 32.0f * u, a.x + 30.0f * u, cy, 0, t_col(NAVY, in), labels[row]);
        SmString value;
        if (row == 0 && selected_photo) {
            int kind = sm_queue.empty() ? sm_item : sm_queue[sm_q_index].kind;
            int slot = sm_queue.empty() ? sm_models[kind - 1][sm_model_start[kind - 1]].slot : sm_queue[sm_q_index].model;
            for (auto& model : sm_models[kind - 1]) if (model.slot == slot) value = sm_short(model.name, 24);
            if (!sm_queue.empty()) value += " -> #" + sm_number(sm_queue[sm_q_index].slot);
        }
        else if (row == 0) value = sm_short(sm_q_resident_name(sm_queue.empty() ? sm_q_slots(sm_item)[sm_q_start % sm_q_slots(sm_item).size()].slot : sm_queue[sm_q_index].slot, sm_queue.empty() ? sm_item : sm_queue[sm_q_index].kind), 30);
        else if (row == 1 && !sm_queue.empty()) value = sm_number(sm_q_index + 1) + "/" + sm_number(sm_queue.size()) + " " + SmString(sm_q_category(sm_queue[sm_q_index].kind)) + " " + sm_short(sm_queue[sm_q_index].name, 18);
        else if (row == 2) value = sm_q_category(sm_item);
        else if (row == 4) value = sm_number(sm_queue.size());
        if (!value.empty()) t_text(dl, g_ft_row, 32.0f * u, b.x - 30.0f * u, cy, 1, t_col(NAVY, in), value.c_str());
        if (over && click) { sm_q_sel = row; sm_q_act(row < 2 && mouse.x < a.x + rw * 0.5f ? A_LEFT : A_OK); }
    }
    t_text(dl, g_ft_small, 24.0f * u, bx + bw * 0.5f, ry + 6.5f * pitch, 0.5f, t_col(NAVY, in), sm_note);
    t_text(dl, g_ft_small, 24.0f * u, bx + bw * 0.5f, ry + 7.1f * pitch, 0.5f, t_col(NAVY, in), sm_qtr("One backup, one reload. Original ShareMii codec by Star-F0rce.", "Un backup, un ricaricamento. Codec ShareMii originale di Star-F0rce.", "Eine Sicherung, einmal neu laden. ShareMii-Codec von Star-F0rce.", "Una copia, una recarga. Codec ShareMii de Star-F0rce.", "Une sauvegarde, un rechargement. Codec ShareMii de Star-F0rce.", "Uma copia, uma recarga. Codec ShareMii de Star-F0rce."));
}
