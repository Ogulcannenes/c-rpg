#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>

static const char kMarker[24] = "CPPADVENTURE_PAYLOAD_V1";
struct Footer { char marker[24]; std::uint64_t payloadSize; };

static std::wstring quote(const std::wstring& value) {
    std::wstring out = L"\"";
    for (wchar_t c : value) {
        if (c == L'\"') out += L"\\\"";
        else out += c;
    }
    out += L"\"";
    return out;
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR commandLine, int) {
    const bool silent = commandLine && std::wstring(commandLine).find(L"--silent") != std::wstring::npos;
    wchar_t exePath[MAX_PATH], tempRoot[MAX_PATH];
    GetModuleFileNameW(nullptr, exePath, MAX_PATH);
    GetTempPathW(MAX_PATH, tempRoot);
    std::wstring setupFolder(exePath);
    setupFolder.resize(setupFolder.find_last_of(L"\\/"));
    std::wstring projectFolder = setupFolder;
    projectFolder.resize(projectFolder.find_last_of(L"\\/"));
    std::wstring legacyDb = projectFolder + L"\\data\\adventure.db";
    if (GetFileAttributesW(legacyDb.c_str()) != INVALID_FILE_ATTRIBUTES) SetEnvironmentVariableW(L"CPP_ADVENTURE_LEGACY_DB", legacyDb.c_str());
    if (commandLine && std::wstring(commandLine) == L"--verify-payload") {
        HANDLE check = CreateFileW(exePath, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (check == INVALID_HANDLE_VALUE) return 10;
        LARGE_INTEGER size{}; GetFileSizeEx(check, &size);
        Footer embedded{}; DWORD bytesRead = 0;
        LARGE_INTEGER seek{}; seek.QuadPart = size.QuadPart - static_cast<LONGLONG>(sizeof(embedded));
        bool valid = size.QuadPart >= static_cast<LONGLONG>(sizeof(embedded)) && SetFilePointerEx(check, seek, nullptr, FILE_BEGIN) && ReadFile(check, &embedded, sizeof(embedded), &bytesRead, nullptr) && bytesRead == sizeof(embedded) && std::string(embedded.marker, 23) == std::string(kMarker, 23) && embedded.payloadSize <= static_cast<std::uint64_t>(size.QuadPart - sizeof(embedded));
        CloseHandle(check);
        return valid ? 0 : 11;
    }
    std::wstring folder = std::wstring(tempRoot) + L"CppAdventure-Setup-" + std::to_wstring(GetCurrentProcessId());
    CreateDirectoryW(folder.c_str(), nullptr);
    std::wstring archive = folder + L"\\payload.zip";

    HANDLE source = CreateFileW(exePath, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (source == INVALID_HANDLE_VALUE) {
        MessageBoxW(nullptr, L"Kurulum dosyası okunamadı.", L"C++ Adventure", MB_ICONERROR | MB_OK);
        return 1;
    }
    LARGE_INTEGER total;
    GetFileSizeEx(source, &total);
    Footer footer{};
    DWORD read = 0;
    LARGE_INTEGER seek{};
    seek.QuadPart = total.QuadPart - static_cast<LONGLONG>(sizeof(footer));
    SetFilePointerEx(source, seek, nullptr, FILE_BEGIN);
    ReadFile(source, &footer, sizeof(footer), &read, nullptr);
    if (read != sizeof(footer) || std::string(footer.marker, 23) != std::string(kMarker, 23) || footer.payloadSize > static_cast<std::uint64_t>(total.QuadPart - sizeof(footer))) {
        CloseHandle(source);
        MessageBoxW(nullptr, L"Kurulum paketi bozuk veya eksik.", L"C++ Adventure", MB_ICONERROR | MB_OK);
        return 2;
    }
    const LONGLONG offset = total.QuadPart - static_cast<LONGLONG>(sizeof(footer)) - static_cast<LONGLONG>(footer.payloadSize);
    seek.QuadPart = offset;
    SetFilePointerEx(source, seek, nullptr, FILE_BEGIN);
    HANDLE target = CreateFileW(archive.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    std::vector<char> buffer(1024 * 1024);
    std::uint64_t remaining = footer.payloadSize;
    bool ok = target != INVALID_HANDLE_VALUE;
    while (ok && remaining) {
        DWORD wanted = static_cast<DWORD>(remaining > buffer.size() ? buffer.size() : remaining), got = 0, written = 0;
        ok = ReadFile(source, buffer.data(), wanted, &got, nullptr) && got == wanted && WriteFile(target, buffer.data(), got, &written, nullptr) && written == got;
        remaining -= got;
    }
    CloseHandle(source);
    if (target != INVALID_HANDLE_VALUE) CloseHandle(target);
    if (!ok) {
        MessageBoxW(nullptr, L"Kurulum dosyaları geçici klasöre çıkarılamadı.", L"C++ Adventure", MB_ICONERROR | MB_OK);
        return 3;
    }

    std::wstring extract = L"Expand-Archive -LiteralPath '" + archive + L"' -DestinationPath '" + folder + L"' -Force; & '" + folder + L"\\install.ps1'";
    std::wstring command = L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command " + quote(extract);
    STARTUPINFOW startup{}; startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(nullptr, command.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW, nullptr, folder.c_str(), &startup, &process)) {
        MessageBoxW(nullptr, L"Kurulum başlatılamadı. Windows PowerShell gerekli.", L"C++ Adventure", MB_ICONERROR | MB_OK);
        return 4;
    }
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD exitCode = 1;
    GetExitCodeProcess(process.hProcess, &exitCode);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    if (!silent && exitCode == 0) MessageBoxW(nullptr, L"C++ Adventure kuruldu. Masaüstü kısayolundan başlatabilirsin.", L"C++ Adventure", MB_ICONINFORMATION | MB_OK);
    else if (!silent) MessageBoxW(nullptr, L"Kurulum tamamlanamadı. PowerShell bir hata bildirdi.", L"C++ Adventure", MB_ICONERROR | MB_OK);
    return static_cast<int>(exitCode);
}
