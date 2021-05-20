#include "stdafx.h"
#include "launcher.h"
#include "os_utils.h"
#include <io.h>

#include "launcherDlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif


const char *CLauncherDlg::ROOT_INDEX_TITLE = "Family Tree Home Page";
const char *CLauncherDlg::FT_TRUECRYPT_VOL = "adm\\familyTree.tc";
const char *CLauncherDlg::TRUECRYPT_INSTALLER = "adm\\install_truecrypt.exe";

#define WM_USER_LAUNCH_BROWSER		(WM_USER+1)

BOOL CALLBACK EnumWindowsProc(HWND hWnd, LPARAM lParam) {
    char buff[255];
	bool *pFoundWindow = (bool *)lParam;

    if (IsWindowVisible(hWnd)) {
        GetWindowText(hWnd, (LPSTR) buff, sizeof(buff) - 1);
		//TRACE("%s\n", buff);

		*pFoundWindow = (strstr(buff, CLauncherDlg::ROOT_INDEX_TITLE) == buff);
		if (*pFoundWindow) return FALSE;
        
    }
    return TRUE;
}

CLauncherDlg::CLauncherDlg(CWnd* pParent /*=NULL*/) :
	CDialog(CLauncherDlg::IDD, pParent),
	m_state(eState_UNKNOWN)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
	CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
}

CLauncherDlg::~CLauncherDlg()
{
	CoUninitialize();
}

void CLauncherDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);

	DDX_Control(pDX, IDC_INFO, m_infoCtrl);
	DDX_Control(pDX, IDC_LOGIN, m_usernameCtrl);
	DDX_Control(pDX, IDC_PASSWORD, m_passwordCtrl);
	DDX_Control(pDX, IDC_LOGIN_LABEL, m_usernameLabel);
	DDX_Control(pDX, IDC_PASSWORD_LABEL, m_passwordLabel);
	DDX_Control(pDX, IDC_IMAGE, m_imageCtrl);
	DDX_Control(pDX, IDC_LOADING, m_gifCtrl);
	DDX_Control(pDX, IDOK, m_okButton);
}


BEGIN_MESSAGE_MAP(CLauncherDlg, CDialog)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_EN_CHANGE(IDC_LOGIN, OnEnChangeLogin)
	ON_EN_CHANGE(IDC_PASSWORD, OnEnChangePassword)
	ON_MESSAGE( WM_USER_LAUNCH_BROWSER, OnLaunchBrowser )
END_MESSAGE_MAP()


BOOL CLauncherDlg::OnInitDialog()
{
	CDialog::OnInitDialog();
	
	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	CString windowText; windowText.Format("FamilyTree Launcher (%s)", getVersionFileName());
	this->SetWindowText(windowText);

	m_state = determineState();
	updateOkEnable();

	switch (m_state)
	{
	case eState_loggedIn:
		this->PostMessage(WM_USER_LAUNCH_BROWSER);
		break;
	case eState_loginPrompt:
		ViewLoginPanel();
		break;
	case eState_okTrueCryptInstall:
		writeToStatus("Family tree needs to install TrueCrypt.\n\n"
					  "Press OK to proceed, and DO NOT TOUCH THE KEYBOARD until this dialog reappears.");
		break;
	case eState_noInstallRights:
		errorMessage("You need to have Administrator rights to allow installation to proceed.\n(This is only necessary for the first time install.)");
		break;
	default:
		errorMessage("Unknown Error");
		break;
	}
	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CLauncherDlg::HideAllPanels()
{
	m_imageCtrl.ShowWindow(FALSE);
	m_gifCtrl.ShowWindow(FALSE);
	m_infoCtrl.ShowWindow(FALSE);
	m_usernameCtrl.ShowWindow(FALSE);
	m_passwordCtrl.ShowWindow(FALSE);
	m_usernameLabel.ShowWindow(FALSE);
	m_passwordLabel.ShowWindow(FALSE);
}

void CLauncherDlg::ViewStatusPanel()
{
	HideAllPanels();
	m_infoCtrl.ShowWindow(TRUE);
}

void CLauncherDlg::ViewLoginPanel()
{
	updateOkEnable();
	HideAllPanels();
	m_usernameCtrl.ShowWindow(TRUE);
	m_passwordCtrl.ShowWindow(TRUE);
	m_usernameLabel.ShowWindow(TRUE);
	m_passwordLabel.ShowWindow(TRUE);
	m_usernameCtrl.SetFocus();
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CLauncherDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this function to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CLauncherDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

void CLauncherDlg::OnOK()
{
	CWnd* pWndCtrl = GetFocus();
	CWnd* pWndCtrlNext = pWndCtrl;
	INT nCtrlID = pWndCtrl->GetDlgCtrlID();

	if (nCtrlID == IDOK)
	{
		switch (m_state)
		{
		case eState_errorExit:
		case eState_noInstallRights:
			CDialog::OnOK();
			return;
		case eState_okTrueCryptInstall:
			writeToStatus("Installing TrueCrypt...");
			installTrueCrypt();
			if (m_state != eState_errorExit)
			{
				m_state = eState_loginPrompt;
				ViewLoginPanel();
			}
			createShortcuts();
			break;
		case eState_loginPrompt:
			mountVolume();
			if (m_state == eState_loggedIn)
			{
				launchBrowser();
				CDialog::OnOK();
			}
			break;
		}
	}
	else
	{
		switch ( nCtrlID )
		{
		case IDC_LOGIN:
			pWndCtrlNext = GetDlgItem(IDC_PASSWORD);
			break;
		case IDC_PASSWORD:
			pWndCtrlNext = GetDlgItem(IDOK)->SetFocus();
			OnOK();
			return;
			break;
		}
	}
	pWndCtrlNext->SetFocus();
}

enum CLauncherDlg::State CLauncherDlg::determineState()
{
	CString dummy;
	if (findMount(dummy)) // drive already mounted
	{
		return eState_loggedIn;
	}
	else if (! getTrueCryptExe(dummy))
	{
		if (isUserAnAdmin())
			return eState_okTrueCryptInstall;
		else
			return eState_noInstallRights;
	}
	return eState_loginPrompt;
}

bool CLauncherDlg::getTrueCryptExe(CString &path)
{
	const char *locs[] = { "TrueCrypt\\TrueCrypt.exe",
							"Security\\TrueCrypt\\TrueCrypt.exe" };
	CString programFiles = getProgramFilesDir();
	for (int i = 0; i < sizeof(locs) / sizeof(locs[0]); ++i)
	{
		path = programFiles + "\\" + locs[i];
		if (FileExists(path)) return true;
	}
	return false;
}

bool CLauncherDlg::getBrowserExe(CString &path)
{
	const char *locs[] = { "Mozilla Firefox\\firefox.exe",
							"SeaMonkey\\seamonkey.exe" };
	CString programFiles = getProgramFilesDir();
	for (int i = 0; i < sizeof(locs) / sizeof(locs[0]); ++i)
	{
		path = programFiles + "\\" + locs[i];
		if (FileExists(path)) return true;
	}
	return false;
}

void CLauncherDlg::launchBrowser()
{
	CString rootIndex = getRootIndex();
	if (rootIndex.GetLength() == 0)
	{
		errorMessage("Couldn't find Home Page");
		return;
	}

	writeToStatus("Launching Family Tree (browser)...");

	CString browserExe;
	if (getBrowserExe(browserExe))
		NonblockingExecuteExternalApp(browserExe, rootIndex, "");
	else
		BrowserOpenUrl(rootIndex);

	waitBrowserLaunch();
	CDialog::OnOK();
}

void CLauncherDlg::installTrueCrypt()
{
	CString path = getAppDir();
	path += "\\";
	path += TRUECRYPT_INSTALLER;

	BlockingExecuteExternalApp(path, "", " when trying to install TrueCrypt.\n");
}

void CLauncherDlg::writeToStatus(const char *msg, bool isError)
{
	ViewStatusPanel();
	if (isError)
	{
		m_state = eState_errorExit;
		m_imageCtrl.SetIcon( ::LoadIcon(NULL, IDI_ERROR) );
		m_imageCtrl.ShowWindow(TRUE);
	}
	m_infoCtrl.SetWindowText(msg);
}

bool CLauncherDlg::findMount(CString &drive)
{
	TCHAR drives[MAX_PATH + 1] = { 0 };

	DWORD numBytes = GetLogicalDriveStrings(sizeof(drives), drives);
	const int driveStrSize = 4;
	const char *pLim = drives + numBytes;
	const CString fv = getVersionFileName();
	for (char *pDrive = drives; pDrive < pLim; pDrive += driveStrSize)
	{
		CString verFile; verFile.Format("%c:\\%s", *pDrive, fv);
		if (_access(verFile, 0) == 0)
		{
			drive = pDrive;
			return true;
		}
	}
	return false;
}

void CLauncherDlg::mountVolume()
{
	dismountAll();

	char driveLetter;
	bool success = findFreeDriveLetter(driveLetter);
	if (! success)
	{
		errorMessage("Couldn't find a free drive to mount on");
		return;
	}

	CString username; m_usernameCtrl.GetWindowText(username);
	CString password; m_passwordCtrl.GetWindowText(password);
	username += password;

	CString path = getAppDir();
	path += "\\";
	path += FT_TRUECRYPT_VOL;

	CString truecrypt_exe;
	getTrueCryptExe(truecrypt_exe);
	CString args; args.Format("/q /s /l%c /p %s /m rm /m ro /v \"%s\"", driveLetter, username, path);
	BlockingExecuteExternalApp(truecrypt_exe, args, " when trying to mount TrueCrypt volume.\n");
	if (getRootIndex().GetLength() == 0)
		MessageBox("Incorrect username/password", "Login Failed", MB_OK | MB_ICONERROR);
	else
		m_state = eState_loggedIn;
}

void CLauncherDlg::dismountAll()
{
	CString truecrypt_exe;
	getTrueCryptExe(truecrypt_exe);
	CString args; args.Format("/q /s /f /d");
	BlockingExecuteExternalApp(truecrypt_exe, args, " when trying to mount TrueCrypt volume.\n");
}

CString CLauncherDlg::getRootIndex()
{
	CString drive;
	if (findMount(drive))
	{
		CString filename; filename.Format("file:///%c:/index.html", drive[0]);
		return filename;
	}
	return "";
}

void CLauncherDlg::OnEnChangeLogin()
{
	updateOkEnable();
}

void CLauncherDlg::OnEnChangePassword()
{
	updateOkEnable();
}

LRESULT CLauncherDlg::OnLaunchBrowser( WPARAM wParam, LPARAM lParam )
{
	launchBrowser();
	return 0;
}

void CLauncherDlg::updateOkEnable()
{
	BOOL enable = TRUE;
	if (m_state == eState_loginPrompt)
	{
		CString username; m_usernameCtrl.GetWindowText(username);
		CString password; m_passwordCtrl.GetWindowText(password);
		enable = ( (username.GetLength() != 0) && (password.GetLength() != 0) );
	}
	else if (m_state == eState_loggedIn)
	{
		enable = FALSE;
	}
	m_okButton.EnableWindow(enable);
}

void CLauncherDlg::waitBrowserLaunch()
{
	writeToStatus("Waiting for browser to launch...");

	m_gifCtrl.ShowWindow(TRUE);
	if (m_gifCtrl.Load(MAKEINTRESOURCE(IDR_LOADING), _T("GIF")))
		m_gifCtrl.Draw();

	const int sleepDelayMs = 200;

	for (int i = 0; i < 100; ++i)
	{
		flushGuiMessages();

		bool foundWindow = false;
		EnumWindows(EnumWindowsProc, (LPARAM)(&foundWindow));
		if (foundWindow) return;

		Sleep(sleepDelayMs);
	}
}

CString CLauncherDlg::getVersionFileName()
{
	char szAppPath[MAX_PATH] = "";
	::GetModuleFileName(0, szAppPath, sizeof(szAppPath) - 1);
	CString version = getFileVersion(szAppPath);
	version.Replace('.', '_');
	version = "FT_" + version;
	return version;
}

void CLauncherDlg::createShortcuts()
{
	const char *descr = "Lauches Family Tree\n(Ensure CD is inserted first)";
	char szAppPath[MAX_PATH] = { NULL };
	::GetModuleFileName(0, szAppPath, sizeof(szAppPath) - 1);
	CString desktop = getDesktopDir();
	CString desktopLink; desktopLink.Format("%s\\FamilyTree.lnk", desktop);
	CreateLink(szAppPath, desktopLink, descr);
}