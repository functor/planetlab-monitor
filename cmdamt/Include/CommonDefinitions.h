//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2004 - 2006.
//
//  File:       CommonDefinitions.h
//
//  Contents:   Sample code for an Intel® AMT Network client.
//
//  Notes:      This file contains type, function and constant definitions
//              used throughout the code of the all sample applications.
//
//----------------------------------------------------------------------------

#ifndef COMMON_DEFINITIONS_H
#define COMMON_DEFINITIONS_H


#include "StatusCodeDefinitions.h"
#ifdef _WIN32
/*
 * gsoapWinHTTP.h for gSoap WinHTTP extension - needed for TLS support
 */
#include "gsoapWinHttp.h"
#include "StatusStrings.h"
#include <conio.h>
#else
/*
 * httpDigest.h for gSoap HTTP Digest support
 */
#include "httpDigest.h"
#endif

/*
 * Function prototypes
 */
void PrintAuthenticationNote();
bool CheckReturnStatus(unsigned int res, unsigned long status,const char *message);
bool ValidateIP(const char *uri);
void GetString(char *msg, char *s, bool hidden);
bool ChangeService(const char *uri, const char *newService, char *newUri);
bool DisplayWarning(const char *msg);
bool GetNumber(int *number);
void ReplaceSubstring(const char *oldString,const char *oldSubstr, 
					const char *newSubstr, char *newString);
void SetIPAddress(unsigned long &address, unsigned long bytes[]);
void NumberToIP(unsigned long address, unsigned long bytes[]);
void NumberToString(unsigned long number, char *string);
void IpToString(unsigned long address, char *string);
void StringToIP(const char *string, unsigned long &address);
void GuidToString(const unsigned char* guid, char* string);
bool ExtractIPFromUri(const char *uri, char *baseUrl);
void IsEmulator(const char *targetUrl, int *isEmulator);
bool GetOption(int *commandLineLength, char *argv[], int numOfArgs,
			   char **option, char **commandLine[]);
void PrintSuccess(bool print = true);
void FunctionCall(const char *message);
#ifdef _WIN32
bool ParseCommandLine(int commandLineLength,char* commandLine[],char **target,
					  char **certName, bool *local, bool *krb,bool *verbose = NULL, 
                      char **username = NULL, char **password = NULL);
#define CHAR _TCHAR
#else
bool ParseCommandLine(int commandLineLength,char* commandLine[],char **target, 
					  char **certName = NULL,char **certPass = NULL, 
                      bool *verbose = NULL, 
					  char **username = NULL, char **password = NULL);
#define CHAR char
#endif

/*
 * Constants for the common use
 */
static const int MAX_LINE_LEN = 1024;
static const int TIMEOUT = 80;
static const char *DEFAULT_USERNAME = "admin";
static const char *DEFAULT_PASSWORD = "admin";
static const char *CERT_NAME = "-certName";
static const char *USER = "-user";
static const char *PASS = "-pass";
static const char *VERBOSE = "-verbose";
#ifdef _WIN32
static const char *LOCAL = "-local";
static const char *KRB = "-krb";
#else
static const char *CERT_PASS = "-certPass";
#endif

/*
 * The structure that represents 
 * the gSOAP rintime environment
 */
class Soap
{
private:
  struct soap *m_soap;
  char *m_username;
  char *m_password;
  char *m_ip;

public:
    // Constructor
#ifdef _WIN32
  Soap(const char *url, const char *certName, 
	   const char *username, const char *password,
       bool local, bool krb)
#else
  Soap(const char *url, const char *certName, 
	   const char *certPass, const char *username, 
       const char *password)
#endif
  {
    m_username = new char[MAX_LINE_LEN];
    m_password = new char[MAX_LINE_LEN];
    m_ip = new char[MAX_LINE_LEN];
    SetIp(url);
    SetUsername(DEFAULT_USERNAME);
    SetPassword(DEFAULT_PASSWORD);

	if (
#ifdef _WIN32
        krb == false &&
#endif
        !username)
	{
		// To use the default user name, comment the following line:
		GetString("Username: ", m_username, false);  
	}
	else
	{
		SetUsername(username);
	}

	if (
#ifdef _WIN32
        krb == false &&
#endif
        !password)
	{
		// To use the default password, comment the following line:
		GetString("Password: ", m_password, true);
	}
	else
	{
		SetPassword(password);
	}
	m_soap = soap_new();
	if( m_soap )
	{
#ifdef _WIN32
	  SetSoap(certName,local,krb);
#else
	  SetSoap(certName,certPass);
#endif

	}
  }

  void Init(SOAP_NMAC struct Namespace *name = NULL)
  {
    m_soap->userid = m_username;
    m_soap->passwd = m_password;

    if(name != NULL)
    {
        // setting namespace for the runtime environment
	    soap_set_namespaces(m_soap, name);
    }
  }

  char *GetIp()
  {
      return m_ip;
  }

  char *GetUsername()
  {
      return m_username;
  }

  char *GetPassword()
  {
      return m_password;
  }

  struct soap *GetSoap()
  {
      return m_soap;
  }

  void SetIp(const char *url)
  {
      memset(m_ip, 0, MAX_LINE_LEN);
      if(url != NULL)
      {
        strncpy(m_ip, url, MAX_LINE_LEN - 1);
      }
  }

  void SetUsername(const char *username)
  {
      memset(m_username,0,MAX_LINE_LEN);
      if(username != NULL)
      {
        strncpy(m_username, username, MAX_LINE_LEN - 1);
      }
  }

  void SetPassword(const char *password)
  {
      memset(m_password,0,MAX_LINE_LEN);
      if(password != NULL)
      {
        strncpy(m_password, password, MAX_LINE_LEN - 1);
      }
  }

#ifdef _WIN32
  void SetSoap(const CHAR *certName, bool local, bool krb)
#else
  void SetSoap(const CHAR *certName, const char *certPass)
#endif
  {
    m_soap->recv_timeout    = TIMEOUT;
    m_soap->send_timeout    = TIMEOUT;
    m_soap->connect_timeout = TIMEOUT;
    m_soap->accept_timeout  = TIMEOUT;

#ifdef _WIN32
	// gsoap winhttp extension 
	soap_register_plugin( m_soap, winhttp_plugin );
    soap_omode(m_soap, SOAP_IO_KEEPALIVE);
	if( certName )
	{
		winhttp_set_certificate_name(m_soap, certName);
	}

    winhttp_set_local(m_soap,local);
    winhttp_set_auth_scheme(m_soap,krb);
#else
    // gsoap HTTP Digest plugin
 if ( strncmp(m_ip+strlen(m_ip)-5, ".asmx", 5)) {
        soap_register_plugin(m_soap, http_digest);
    }
  soap_omode(m_soap, SOAP_IO_KEEPALIVE);
  soap_imode(m_soap, SOAP_IO_KEEPALIVE);
	if ( !strncmp(m_ip, "https:", 6) )
	{
		soap_ssl_client_context(m_soap,
								SOAP_SSL_DEFAULT,
								certName,
								certPass,
								"/usr/share/ssl/cert.pem",
								"/usr/share/ssl/certs/", NULL);
	}
#endif
  }

  // Destructor
  ~Soap()
  {
      if(m_username)
      {
          delete [] m_username;
          m_username = NULL;
      }
      if(m_password)
      {
          delete [] m_password;
          m_password = NULL;
      }
      if(m_ip)
      {
          delete [] m_ip;
          m_ip = NULL;
      }
	  if( m_soap ){
		soap_destroy(m_soap);
		soap_end(m_soap);
		soap_done(m_soap);
		free(m_soap);
		m_soap = NULL;
	  }
  }
};




#endif
