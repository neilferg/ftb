// ft.h : main header file for the PROJECT_NAME application
//

#pragma once

#ifndef __AFXWIN_H__
	#error "include 'stdafx.h' before including this file for PCH"
#endif

#include "resource.h"		// main symbols


// CftApp:
// See ft.cpp for the implementation of this class
//

class CftApp : public CWinApp
{
public:
	CftApp();

// Overrides
	public:
	virtual BOOL InitInstance();

// Implementation

	DECLARE_MESSAGE_MAP()
};

extern CftApp theApp;

void errorMessage(const char *msg);