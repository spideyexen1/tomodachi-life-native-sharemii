// SPDX-License-Identifier: GPL-3.0-only
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Web.Script.Serialization;

namespace NativeShareMiiSetup {
    static class Localization {
        internal static readonly string[] Codes = {"auto", "en", "it", "de", "es", "fr", "pt"};
        internal static readonly string[] Names = {"Auto · Windows", "English", "Italiano", "Deutsch", "Español", "Français", "Português"};
        static readonly Dictionary<string, Dictionary<string, string>> Catalogs = Load();
        internal static string Code = Resolve(CultureInfo.CurrentUICulture.Name);
        internal static string Resolve(string locale) {
            string code = (locale ?? "").Replace('_', '-').Split('-')[0].ToLowerInvariant();
            return Array.IndexOf(Codes, code) > 0 ? code : "en";
        }
        internal static void Select(int index) { Code = index == 0 ? Resolve(CultureInfo.CurrentUICulture.Name) : Codes[index]; }
        internal static string Get(string it, string en) {
            if (Code == "it") return it;
            Dictionary<string, string> catalog; string translated;
            return Catalogs.TryGetValue(Code, out catalog) && catalog.TryGetValue(en, out translated) ? translated : en;
        }
        static Dictionary<string, Dictionary<string, string>> Load() {
            Dictionary<string, Dictionary<string, string>> result = new Dictionary<string, Dictionary<string, string>>();
            using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("SetupSources"))
            using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read)) {
                foreach (string code in new string[] {"de", "es", "fr", "pt"}) {
                    ZipArchiveEntry entry = archive.GetEntry("payload/locales/" + code + ".json");
                    if (entry == null) throw new InvalidDataException("Missing setup language: " + code);
                    using (StreamReader reader = new StreamReader(entry.Open())) result[code] = new JavaScriptSerializer().Deserialize<Dictionary<string, string>>(reader.ReadToEnd());
                }
            }
            return result;
        }
    }
}
