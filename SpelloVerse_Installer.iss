; ---------------------------------------
; SpelloVerse Installer Script
; ---------------------------------------

[Setup]
AppName=SpelloVerse
AppVersion=1.2
AppPublisher=Juhi Gupta
DefaultDirName={pf}\SpelloVerse
DefaultGroupName=SpelloVerse

OutputBaseFilename=SpelloVerse_Setup
Compression=lzma
SolidCompression=yes

SetupIconFile=game_icon.ico

DisableDirPage=yes
DisableProgramGroupPage=yes


[Files]
; ---- Main executable from PyInstaller dist ----
Source: "dist\main\main.exe"; DestDir: "{app}"; Flags: ignoreversion

; ---- Internal folder required by PyInstaller ----
Source: "dist\main\_internal\*"; DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---- Assets (images, sounds) ----
Source: "assets\*"; DestDir: "{app}\assets"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---- Dataset (word DB) ----
Source: "data\*"; DestDir: "{app}\data"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---- Modes ----
Source: "modes\*"; DestDir: "{app}\modes"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---- Systems (database manager, audio, etc.) ----
Source: "systems\*"; DestDir: "{app}\systems"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---- Icon ----
Source: "game_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu icon
Name: "{group}\SpelloVerse"; Filename: "{app}\main.exe"; \
    IconFilename: "{app}\game_icon.ico"

; Desktop icon (optional)
Name: "{commondesktop}\SpelloVerse"; Filename: "{app}\main.exe"; \
    IconFilename: "{app}\game_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; \
    GroupDescription: "Additional Icons:"
