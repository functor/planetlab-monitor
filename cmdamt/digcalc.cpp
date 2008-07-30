//-------------------------------------------------------------------
//   Copyright (C) The Internet Society (1999).  All Rights Reserved.
//
//   This document and translations of it may be copied and furnished to
//   others, and derivative works that comment on or otherwise explain it
//   or assist in its implementation may be prepared, copied, published
//   and distributed, in whole or in part, without restriction of any
//   kind, provided that the above copyright notice and this paragraph are
//   included on all such copies and derivative works.  However, this
//   document itself may not be modified in any way, such as by removing
//   the copyright notice or references to the Internet Society or other
//   Internet organizations, except as needed for the purpose of
//   developing Internet standards in which case the procedures for
//   copyrights defined in the Internet Standards process must be
//   followed, or as required to translate it into languages other than
//   English.
//
//   The limited permissions granted above are perpetual and will not be
//   revoked by the Internet Society or its successors or assigns.
//
//   This document and the information contained herein is provided on an
//   "AS IS" basis and THE INTERNET SOCIETY AND THE INTERNET ENGINEERING
//   TASK FORCE DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING
//   BUT NOT LIMITED TO ANY WARRANTY THAT THE USE OF THE INFORMATION
//   HEREIN WILL NOT INFRINGE ANY RIGHTS OR ANY IMPLIED WARRANTIES OF
//   MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
//   
//   
//   Modifiyed by Intel Corporation, 2005
//-------------------------------------------------------------------------

#include <stddef.h>
#include <openssl/md5.h>
#include <string.h>
#include <ctype.h>
#include "digcalc.h"

int stricmp(const char *b, const char *a)
{
    while (*a != '\0' && *b != '\0' && tolower(*a) == tolower(*b))
    {   a++;
        b++;
    }
    return *a == *b ? 0 :
           tolower(*a) < tolower(*b) ? -1 : 1;
}

void CvtHex(
    HASH Bin,
    HASHHEX Hex
    )
{
    unsigned short i;
    unsigned char j;

    for (i = 0; i < HASHLEN; i++) {
        j = (Bin[i] >> 4) & 0xf;
        if (j <= 9)
            Hex[i*2] = (j + '0');
         else
            Hex[i*2] = (j + 'a' - 10);
        j = Bin[i] & 0xf;
        if (j <= 9)
            Hex[i*2+1] = (j + '0');
         else
            Hex[i*2+1] = (j + 'a' - 10);
    };
    Hex[HASHHEXLEN] = '\0';
};

/* calculate H(A1) as per spec */
void DigestCalcHA1(
    char * pszAlg,
    char * pszUserName,
    char * pszRealm,
    char * pszPassword,
    char * pszNonce,
    char * pszCNonce,
    HASHHEX SessionKey
    )
{
      MD5_CTX Md5Ctx;
      HASH HA1;
      HASHHEX HA1HEX;

      MD5_Init(&Md5Ctx);
      MD5_Update(&Md5Ctx, pszUserName, strlen(pszUserName));
      MD5_Update(&Md5Ctx, ":", 1);
      MD5_Update(&Md5Ctx, pszRealm, strlen(pszRealm));
      MD5_Update(&Md5Ctx, ":", 1);
      MD5_Update(&Md5Ctx, pszPassword, strlen(pszPassword));
      MD5_Final(HA1, &Md5Ctx);
      if (stricmp(pszAlg, "md5-sess") == 0) {
            CvtHex(HA1, HA1HEX); 
            MD5_Init(&Md5Ctx);
            MD5_Update(&Md5Ctx, HA1HEX, HASHHEXLEN);
            MD5_Update(&Md5Ctx, ":", 1);
            MD5_Update(&Md5Ctx, pszNonce, strlen(pszNonce));
            MD5_Update(&Md5Ctx, ":", 1);
            MD5_Update(&Md5Ctx, pszCNonce, strlen(pszCNonce));
            MD5_Final(HA1, &Md5Ctx);
      };
      CvtHex(HA1, SessionKey);
};

/* calculate request-digest/response-digest as per HTTP Digest spec */
void DigestCalcResponse(
    HASHHEX HA1,           /* H(A1) */
    char * pszNonce,       /* nonce from server */
    char * pszNonceCount,  /* 8 hex digits */
    char * pszCNonce,      /* client nonce */
    char * pszQop,         /* qop-value: "", "auth", "auth-int" */
    char * pszMethod,      /* method from the request */
    char * pszDigestUri,   /* requested URL */
    HASHHEX HEntity,       /* H(entity body) if qop="auth-int" */
    HASHHEX Response      /* request-digest or response-digest */
    )
{
      MD5_CTX Md5Ctx;
      HASH HA2;
      HASH RespHash;
      HASHHEX HA2Hex;

      // calculate H(A2)
      MD5_Init(&Md5Ctx);
      MD5_Update(&Md5Ctx, pszMethod, strlen(pszMethod));
      MD5_Update(&Md5Ctx, ":", 1);
      MD5_Update(&Md5Ctx, pszDigestUri, strlen(pszDigestUri));
      if (stricmp(pszQop, "auth-int") == 0) {
            MD5_Update(&Md5Ctx, ":", 1);
            MD5_Update(&Md5Ctx, HEntity, HASHHEXLEN);
      };
      MD5_Final(HA2, &Md5Ctx);
      CvtHex(HA2, HA2Hex);

      // calculate response
      MD5_Init(&Md5Ctx);
      MD5_Update(&Md5Ctx, HA1, HASHHEXLEN);
      MD5_Update(&Md5Ctx, ":", 1);
      MD5_Update(&Md5Ctx, pszNonce, strlen(pszNonce));
      MD5_Update(&Md5Ctx, ":", 1);
      if (*pszQop) {
          MD5_Update(&Md5Ctx, pszNonceCount, strlen(pszNonceCount));
          MD5_Update(&Md5Ctx, ":", 1);
          MD5_Update(&Md5Ctx, pszCNonce, strlen(pszCNonce));
          MD5_Update(&Md5Ctx, ":", 1);
          MD5_Update(&Md5Ctx, pszQop, strlen(pszQop));
          MD5_Update(&Md5Ctx, ":", 1);
      };
      MD5_Update(&Md5Ctx, HA2Hex, HASHHEXLEN);
      MD5_Final(RespHash, &Md5Ctx);
      CvtHex(RespHash, Response);
};
