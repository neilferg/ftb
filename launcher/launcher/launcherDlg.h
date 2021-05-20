#pragma once
#include "afxwin.h"
#include "PictureEx.h"

class CLauncherDlg : public CDialog
{
public:
	CLauncherDlg(CWnd* pParent = NULL);
	virtual ~CLauncherDlg();

	enum { IDD = IDD_FT_DIALOG };

	void writeToStatus(const char *msg, bool isError = false);

	static const char *ROOT_INDEX_TITLE;

protected:
	virtual void DoDataExchange(CDataExchange* pDX);

	enum State {
		eState_UNKNOWN,
		eState_noInstallRights,
		eState_okTrueCryptInstall,
		eState_trueCryptInstalling,
		eState_loginPrompt,
		eState_loggedIn,

		eState_errorExit
	};

	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()

	void OnOK();

	enum State determineState();
	bool getTrueCryptExe(CString &path);
	bool getBrowserExe(CString &path);
	bool findMount(CString &drive);
	CString getRootIndex();
	void launchBrowser();
	void installTrueCrypt();
	void mountVolume();
	void dismountAll();

	void HideAllPanels();
	void ViewLoginPanel();
	void ViewStatusPanel();
	void updateOkEnable();
	void waitBrowserLaunch();
	CString getVersionFileName();
	void createShortcuts();

private:

	static const char *TRUECRYPT_INSTALLER;
	static const char *FT_TRUECRYPT_VOL;

	enum State m_state;

	HICON m_hIcon;
	CStatic m_infoCtrl;
	CEdit m_usernameCtrl;
	CEdit m_passwordCtrl;
	CStatic m_usernameLabel;
	CStatic m_passwordLabel;
	CStatic m_imageCtrl;
	CPictureEx m_gifCtrl;
	CButton m_okButton;

	afx_msg void OnEnChangeLogin();
	afx_msg void OnEnChangePassword();
	LRESULT OnLaunchBrowser( WPARAM wParam, LPARAM lParam );
};
