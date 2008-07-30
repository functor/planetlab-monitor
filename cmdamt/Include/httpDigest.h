//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2003 - 2005.
//
//  File:       httpDigest.h 
//
//  Contents:   Sample code for a gSOAP plugin to implement HTTP Digest 
//              authentication.
//
//  Limitations:
//          - MIME, DIME and HTTP chunks (SOAP_IO_CHUNK) are not supported.
//          - This implementationn will internally buffer the entire outgoing 
//            message before sending
//          - This implementation will fail if challenge isn't received within 
//            SOAP_BUFLEN bytes read.
//          - This implementation will fail if challenge or response are larger
//            than the constants we used.
//          - This implementation calculates the digest response for each call 
//            and doesn't save information. 
//          - This implementation assumes that the algorithm is MD5 and that 
//            qop="auth".
//
// Usage:   Add the httpDigest.h and httpDigest.cpp files to your project 
//
//          In your source, just after calling soap_init(), register this 
//          plugin with soap_register_plugin( soap, http_digest ). 
//          Use soap.userid and soap.passwd for the username and password.
//          As in gSOAP, username and password have to be provided for each call.
//
//          e.g.
//              struct soap soap;
//              soap_init( &soap );
//              soap_register_plugin( &soap, http_digest );
//              soap.userid = "admin";
//              soap.passwd = "admin";
//              ...
//              soap_done(&soap);
//
//----------------------------------------------------------------------------

#ifndef HTTP_DIGEST_H
#define HTTP_DIGEST_H

#include "stdsoap2.h"

int http_digest(struct soap *soap, struct soap_plugin *p, void *arg);

#endif
