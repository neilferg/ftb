#pragma once

bool FileExists(const TCHAR *fileName);
BOOL isUserAnAdmin();
bool findFreeDriveLetter(char &driveLetter);

void spawnApp(PHANDLE rPipe, CString csExeName, CString csArguments, CString csCustomErrorMsg);
CString BlockingExecuteExternalApp(CString csExeName, CString csArguments, CString csCustomErrorMsg);
CString NonblockingExecuteExternalApp(CString csExeName, CString csArguments, CString csCustomErrorMsg);
void ReportLastError(char *outstr);
void BrowserOpenUrl(CString url);
CString getAppDir();
void flushGuiMessages( void );
CString getProgramFilesDir();
CString getDesktopDir();
CString getFileVersion(const char *path);
HRESULT CreateLink(LPCSTR lpszPathObj, LPCSTR lpszPathLink, LPCSTR lpszDesc);