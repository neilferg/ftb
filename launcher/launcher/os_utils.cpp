#include "stdafx.h"
#include "launcher.h" // for errorMessage()
#include <io.h>
#include "os_utils.h"

bool FileExists(const TCHAR *fileName)
{
    DWORD fileAttr = GetFileAttributes(fileName);
    return (0xFFFFFFFF != fileAttr);
}

BOOL isUserAnAdmin()
{
#if _WIN32_WINNT >= 0x0600 

   BOOL isAdmin = FALSE;

   DWORD bytesUsed = 0;

   TOKEN_ELEVATION_TYPE tokenElevationType;

   if (!::GetTokenInformation(m_hToken, TokenElevationType, &tokenElevationType, sizeof(tokenElevationType), &bytesUsed))
   {
      const DWORD lastError = ::GetLastError();

      throw CWin32Exception(_T("CProcessToken::IsUserAnAdmin() - GetTokenInformation - TokenElevationType"), lastError);
   }

   if (tokenElevationType == TokenElevationTypeLimited)
   {
      CSmartHandle hUnfilteredToken;

      if (!::GetTokenInformation(m_hToken, TokenLinkedToken, reinterpret_cast<void *>(hUnfilteredToken.GetHandle()), sizeof(HANDLE), &bytesUsed))
      {
         const DWORD lastError = ::GetLastError();

         throw CWin32Exception(_T("CProcessToken::IsUserAnAdmin() - GetTokenInformation - TokenLinkedToken"), lastError);
      }

      BYTE adminSID[SECURITY_MAX_SID_SIZE];

      DWORD sidSize = sizeof(adminSID);

      if (!::CreateWellKnownSid(WinBuiltinAdministratorsSid, 0, &adminSID, &sidSize))
      {
         const DWORD lastError = ::GetLastError();

         throw CWin32Exception(_T("CProcessToken::IsUserAnAdmin() - CreateWellKnownSid"), lastError);
      }

      BOOL isMember = FALSE;

      if (::CheckTokenMembership(hUnfilteredToken, &adminSID, &isMember))
      {
         const DWORD lastError = ::GetLastError();

         throw CWin32Exception(_T("CProcessToken::IsUserAnAdmin() - CheckTokenMembership"), lastError);
      }

      isAdmin = (isMember != FALSE);
   }
   else
   {
      isAdmin = ::IsUserAnAdmin();         
   }

   return isAdmin;

#else
   return ::IsUserAnAdmin();
#endif
}

bool findFreeDriveLetter(char &driveLetter)
{
	const char drives[] = "TUVWXYZHIJKLMNOPQRS"; // ordered by preference
	char *pDrive = (char *)drives;
	while (*pDrive != NULL)
	{
		CString drivePath; drivePath.Format("%c:\\", *pDrive);
		if (_access(drivePath, 0 ) == -1 && errno == ENOENT)
		{
			driveLetter = *pDrive;
			return true;
		}
		++pDrive;
	}
	return false;
}

#define READ_BUF_SIZE 16384

void spawnApp(PHANDLE rPipe, CString csExeName, CString csArguments, CString csCustomErrorMsg)
{
    CString csExecute;
    csExecute=csExeName + " " + csArguments;
  
    SECURITY_ATTRIBUTES secattr; 
    ZeroMemory(&secattr,sizeof(secattr));
    secattr.nLength = sizeof(secattr);
    secattr.bInheritHandle = TRUE;

    HANDLE wPipe;

    //Create pipes to write and read data
    if (CreatePipe(rPipe,&wPipe,&secattr,0) == 0)
		ReportLastError("Creating pipe");
  
    STARTUPINFO sInfo; 
    ZeroMemory(&sInfo,sizeof(sInfo));
    PROCESS_INFORMATION pInfo; 
    ZeroMemory(&pInfo,sizeof(pInfo));
    sInfo.cb=sizeof(sInfo);
    sInfo.dwFlags=STARTF_USESTDHANDLES;
    sInfo.hStdInput=NULL; 
    sInfo.hStdOutput=wPipe; 
    sInfo.hStdError=wPipe;
  
    //Create the process here.
    if (CreateProcess( 0,                                      // pszImageName
				 //command,                                // pszCmdLine
				 csExecute.GetBuffer(csExecute.GetLength()),
	             0,                                      // psaProcess
				 0,                                      // psaThread
				 TRUE,                                   // fInheritHandles
				 NORMAL_PRIORITY_CLASS|CREATE_NO_WINDOW, // fdwCreate
				 0,                                      // pvEnvironment
				 0,                                      // pszCurDir
				 &sInfo,                                 // psiStartInfo
				 &pInfo)==0)// pProcInfo
	{
		CString errorMsg = "Error running command: '" + csExecute + "'";

		if (csCustomErrorMsg != "")  
		{  
			// Append Custom Error Message/Hint  
			errorMsg += csCustomErrorMsg;  
		} 

		ReportLastError(errorMsg.GetBuffer(errorMsg.GetLength()));
	}

    CloseHandle(wPipe);
}

CString BlockingExecuteExternalApp(CString csExeName, CString csArguments, CString csCustomErrorMsg)
{
    HANDLE rPipe;

	spawnApp(&rPipe, csExeName, csArguments, csCustomErrorMsg);

    //now read the output pipe here.
    char buf[READ_BUF_SIZE];
    DWORD reDword; 
    CString csOutput, csTemp;
    BOOL res;
    do
    {
        res = ::ReadFile(rPipe,buf,READ_BUF_SIZE,&reDword,0);
		buf[reDword] = 0;
        csTemp = buf;
        csOutput += csTemp.Left(reDword);
    }
    while(res);

	CloseHandle(rPipe);
    return csOutput;
}

CString NonblockingExecuteExternalApp(CString csExeName, CString csArguments, CString csCustomErrorMsg)
{
	HANDLE rPipe;
	spawnApp(&rPipe, csExeName, csArguments, csCustomErrorMsg);
	CloseHandle(rPipe);
	return 0;
}

void BrowserOpenUrl(CString url)
{
	ShellExecute(NULL, "open", url, NULL, NULL, SW_SHOWNORMAL);
}

void ReportLastError(char *msgPrefix)
{
    LPVOID errorStr;

    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |FORMAT_MESSAGE_IGNORE_INSERTS,
        			NULL,
                    GetLastError(),
        			MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        			(LPTSTR) &errorStr,
        			0, NULL );

	char tmpStr[260]="";
	sprintf(tmpStr,"%s\n%s", msgPrefix, errorStr);
	errorMessage(tmpStr);
}

CString getAppDir()
{
	char szAppPath[MAX_PATH] = "";
	::GetModuleFileName(0, szAppPath, sizeof(szAppPath) - 1);

	// Extract directory
	CString strAppDirectory = szAppPath;
	strAppDirectory = strAppDirectory.Left(strAppDirectory.ReverseFind('\\'));
	return strAppDirectory;
}

// Process windows GUI messages, ignoring all WM_USER messages
void flushGuiMessages( void )
{
	MSG message;
	const int filter = WM_USER - 1;

	while ( ::PeekMessage( &message, NULL, 0, filter, PM_REMOVE ) ) 
	{
		::TranslateMessage( &message );
		::DispatchMessage( &message );
	} 
}

CString getProgramFilesDir()
{
TCHAR pf[MAX_PATH];
SHGetSpecialFolderPath(
    0,
    pf, 
    CSIDL_PROGRAM_FILES, 
    FALSE );
return CString(pf);
}

CString getDesktopDir()
{
TCHAR pf[MAX_PATH];
SHGetSpecialFolderPath(
    0,
    pf, 
    CSIDL_COMMON_DESKTOPDIRECTORY, // 
    FALSE );
return CString(pf);
}

CString getFileVersion(const char *path)
{
	DWORD dwDummy;
	DWORD dwFVISize = GetFileVersionInfoSize(path , &dwDummy);
	LPBYTE lpVersionInfo = new BYTE[dwFVISize];
	GetFileVersionInfo(path ,0 ,dwFVISize ,lpVersionInfo);
	UINT uLen;
	VS_FIXEDFILEINFO *lpFfi;
	VerQueryValue(lpVersionInfo , _T("\\") , (LPVOID *)&lpFfi , &uLen);
	DWORD dwFileVersionMS = lpFfi->dwFileVersionMS;
	DWORD dwFileVersionLS = lpFfi->dwFileVersionLS;
	delete [] lpVersionInfo;

	DWORD dwLeftMost = HIWORD(dwFileVersionMS);
	DWORD dwSecondLeft = LOWORD(dwFileVersionMS);
	DWORD dwSecondRight = HIWORD(dwFileVersionLS);
	DWORD dwRightMost = LOWORD(dwFileVersionLS);
	CString txt; txt.Format("%d.%d.%d.%d", dwLeftMost, dwSecondLeft,
							dwSecondRight, dwRightMost); 
	return txt;
}

// CreateLink - uses the Shell's IShellLink and IPersistFile interfaces 
//              to create and store a shortcut to the specified object. 
//
// Returns the result of calling the member functions of the interfaces. 
//
// Parameters:
// lpszPathObj  - address of a buffer containing the path of the object. 
// lpszPathLink - address of a buffer containing the path where the 
//                Shell link is to be stored. 
// lpszDesc     - address of a buffer containing the description of the 
//                Shell link. 

HRESULT CreateLink(LPCSTR lpszPathObj, LPCSTR lpszPathLink, LPCSTR lpszDesc) 
{ 
    HRESULT hres; 
    IShellLink* psl; 
 
    // Get a pointer to the IShellLink interface. 
    hres = CoCreateInstance(CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, 
                            IID_IShellLink, (LPVOID*)&psl); 
    if (SUCCEEDED(hres)) 
    { 
        IPersistFile* ppf; 
 
        // Set the path to the shortcut target and add the description. 
        psl->SetPath(lpszPathObj); 
        psl->SetDescription(lpszDesc); 
 
        // Query IShellLink for the IPersistFile interface for saving the 
        // shortcut in persistent storage. 
        hres = psl->QueryInterface(IID_IPersistFile, (LPVOID*)&ppf); 
 
        if (SUCCEEDED(hres)) 
        { 
            WCHAR wsz[MAX_PATH]; 
 
            // Ensure that the string is Unicode. 
            MultiByteToWideChar(CP_ACP, 0, lpszPathLink, -1, wsz, MAX_PATH); 
			
            // Add code here to check return value from MultiByteWideChar 
            // for success.
 
            // Save the link by calling IPersistFile::Save. 
            hres = ppf->Save(wsz, TRUE); 
            ppf->Release(); 
        } 
        psl->Release(); 
    } 
    return hres; 
}
