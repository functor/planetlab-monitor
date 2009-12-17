//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2003 - 2005.
//
//  File:       httpDigest.cpp 
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

#include "httpDigest.h"
#include "digcalc.h"

#define HDR_SIZE 1024

const char HTTP_DIGEST_ID[12] = "HTTP-Digest"; // plugin identification 

struct http_digest_data 
{
    struct soap *soap; // back pointer 

    // send buffer parameters
    char *sendBuffer;        // send buffer 
    size_t sendMsgSize;      // total length of the message 
    size_t sendBufferLength; // length of data in buffer 

    // receive buffer parameters
    char *rcvBuffer; // receive buffer 
    size_t rcvSize;  // length of buffer 
    size_t rcvIdx;   // currecnt index 
    size_t rcvRead;  // amount of data read 

    // open parameters
    char *endpoint;
    char *host;
    int port;

    // function pointers
    int (*fopen)(struct soap*, const char*, const char*, int); // open function 
    int (*fsend)(struct soap*, const char*, size_t); // send function 
    size_t (*frecv)(struct soap*, char*, size_t);    // receive function 
    int (*fposthdr)(struct soap*, const char*, const char*); // post header function 

    char *username;
    char *password;
    char requestUrl[128];
    char method[5];
};

static int http_digest_init(struct soap *soap, struct http_digest_data *data);
static int http_digest_copy(struct soap *soap, struct soap_plugin *dst, 
                            struct soap_plugin *src);
static void http_digest_delete(struct soap *soap, struct soap_plugin *p);

static int http_digest_fopen(struct soap *soap, const char *endpoint, const char *host, 
                             int port);
static int http_digest_fsend(struct soap *soap, const char *buf, size_t size);
static size_t http_digest_frecv(struct soap *soap, char *buf, size_t size);
static int http_digest_fposthdr(struct soap *soap, const char *key, const char *value);

/*
 * The entry point for HTTP digest plugin
 * Arguments:
 *  soap	- pointer to the soap runtime environment 
 *  p		- pointer to the soap plugin
 *  arg		- reserved. Should be NULL
 *
 * Returns SOAP_OK for suceess. Other values for error
 */
int http_digest(struct soap *soap, struct soap_plugin *p, void *arg) 
{
    p->id = HTTP_DIGEST_ID;
    p->data = (void*)malloc(sizeof(struct http_digest_data));
    p->fcopy = http_digest_copy;
    p->fdelete = http_digest_delete;
    if (p->data) {
        memset(p->data, 0, sizeof(struct http_digest_data));
        if (http_digest_init(soap, (struct http_digest_data*)p->data)) {
            free(p->data); 
            return SOAP_EOM;
        }
        return SOAP_OK;
    }
    return SOAP_EOM;
}

/*
 * Initializes the http digest data structure.
 * Arguments:
 *  soap	- pointer to the soap runtime environment 
 *  data	- pointer to the http digest data structure
 *
 * Returns SOAP_OK for suceess. Other values for error
 */
static int http_digest_init(struct soap *soap, struct http_digest_data *data) 
{
    data->soap = soap;
    data->fopen = soap->fopen;
    soap->fopen = http_digest_fopen;
    data->fsend = soap->fsend;
    soap->fsend = http_digest_fsend;
    data->frecv = soap->frecv;
    soap->frecv = http_digest_frecv;
    data->fposthdr = soap->fposthdr;
    soap->fposthdr = http_digest_fposthdr;

    return SOAP_OK;
}

/*
 * Creates the HTTP digest response
 * Arguments:
 *  userName	- the user name
 *  password    - the password
 *  method      - the HTTP method ("GET", "POST)     
 *  realm       - the realm for the authentication
 *  uri         - the URI from the HTTP request
 *  nonce       - the nonce from the challenge
 *  cnonce      - client generated nonce
 *  digestResponse - The result authorization string
 *  length      - size of buffer for response
 *
 * Returns 0 for suceess. -1 for error
 */
int CalculateResponse(char *userName, char *password, char *method, char *realm, char *uri,
                       char *nonce, char *cnonce, char *digestResponse, size_t *length) 
{
    size_t currOffset = 0, segmentLength;
    static const char *INITIAL_HDR = "Authorization: Digest username=\"";
    static const char *REALEM_HDR = "\", realm=\"";
    static const char *ALGO_HDR = "\", qop=\"auth\", algorithm=\"MD5\", uri=\"";
    static const char *NONCE_HDR = "\", nonce=\"";
    static const char *NC_HDR = "\", nc=00000002, cnonce=\"";
    static const char *RSP_HDR = "\", response=\"";

    HASHHEX HA1;
    HASHHEX HA2 = "";
    HASHHEX response;

    //"Authorization: Digest username="
    segmentLength = strlen(INITIAL_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, INITIAL_HDR, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username
    segmentLength = strlen(userName);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, userName, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="
    segmentLength = strlen(REALEM_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, REALEM_HDR, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="realm
    segmentLength = strlen(realm);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, realm, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="
    segmentLength = strlen(ALGO_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, ALGO_HDR, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service
    segmentLength = strlen(uri);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, uri, segmentLength);
    currOffset+= segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="
    segmentLength = strlen(NONCE_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, NONCE_HDR, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...
    segmentLength = strlen(nonce);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, nonce, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...", nc=00000002,
    //cnonce="
    segmentLength = strlen(NC_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, NC_HDR, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...", nc=00000002,
    //cnonce="ab341...
    segmentLength = strlen(cnonce);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, cnonce, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...", nc=00000002,
    //cnonce="ab341...", response="
    segmentLength = strlen(RSP_HDR);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, RSP_HDR, segmentLength);
    currOffset += segmentLength;

    //calc response
    DigestCalcHA1("MD5", userName, realm, password, nonce, cnonce, HA1);
    DigestCalcResponse(HA1, nonce, "00000002", cnonce, "auth", method, uri,
                       HA2, response);

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...", nc=00000002,
    //cnonce="ab341...", response="8bbf2...
    segmentLength = strlen(response);
    if (*length < (currOffset + segmentLength)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, response, segmentLength);
    currOffset += segmentLength;

    //"Authorization: Digest username="username", realm="myRealm", qop="auth",
    //algorithm="MD5", uri="/....Service", nonce="7a5c...", nc=00000002,
    //cnonce="ab341...", response="8bbf2..."
    if (*length < (currOffset + 2)) {
        return -1;
    }
    memcpy(digestResponse + currOffset, "\"", 1);
    currOffset += 1;

    //add null termination
    *(digestResponse+currOffset) = 0;
    *length = currOffset;

    return 0;
}

/*
 * generate a 32 byte random hexadecimal string such as "4f6ba982..."
 * Arguments:
 *  outbuff	- buffer to fill 
 */
void GenerateCNonce(char *outbuff) 
{
    srand((unsigned int)time(NULL));
    for(int i = 0; i < 32; i++) {
        int num = (int)(((double) rand()/ ((double)RAND_MAX+1)) * 16);
        switch(num) {
        case 0: case 1: case 2: case 3: case 4: case 5:
        case 6: case 7: case 8: case 9: 
            outbuff[i] = '0' + num;
            break;
        case 10: case 11: case 12: case 13: case 14: case 15:
            outbuff[i] = 'a' + (num-10);
            break;
        default:
            outbuff[i] = 'f';
        }
    }
    outbuff[32] = 0;
}

/*
 * Creates the HTTP digest response
 * Arguments:
 *  data	- the HTTP digest structure
 *  authHeader - the HTTP digest challenge
 *  responseLength - size of response buffer
 *  digestResponse - buffer for HTTP digest response
 *
 * Returns 0 for suceess. -1 for error
 */
int CreateDigestResponse(struct http_digest_data *data, char *authHeader,
                          size_t *responseLength, char *digestResponse) 
{
    char cnonce[33];
    char *realmPtrStart, *realmPtrEnd, *noncePtrStart, *noncePtrEnd;
    size_t segmentLength;
    char realm[HDR_SIZE], nonce[HDR_SIZE];;
    
    if (digestResponse == NULL || authHeader == NULL) {
        return -1;
    }

    GenerateCNonce(cnonce);

    //grep realm from challange
    realmPtrStart = strstr(authHeader, "realm=");
    if (realmPtrStart == NULL) {
        return -1;
    }
    //point to start of realm
    realmPtrStart += 7;
    realmPtrEnd = strstr(realmPtrStart, "\"");
    segmentLength = realmPtrEnd - realmPtrStart;
    memcpy(realm, realmPtrStart, segmentLength);
    //add NULL termination
    realm[segmentLength] = 0;

    //grep nonce from challange
    noncePtrStart = strstr(authHeader, "nonce=");
    if (noncePtrStart == NULL) {
        return -1;
    }
    //point to start of nonce
    noncePtrStart += 7;
    noncePtrEnd = strstr(noncePtrStart, "\"");
    segmentLength = noncePtrEnd - noncePtrStart;
    memcpy(nonce, noncePtrStart, segmentLength);
    //add NULL termination
    nonce[segmentLength]=0;

    return CalculateResponse(data->username, data->password, data->method, realm, 
                             data->requestUrl, nonce, cnonce,digestResponse, responseLength);
}


/*
 * Copies the contents of the plugin
 * Arguments:
 *  soap	- pointer to the soap runtime environment
 *  dst     - the destination plugin
 *  src     - the original plugin
 *
 * Returns SOAP_OK for suceess. Error value for error
 */
static int http_digest_copy(struct soap *soap, struct soap_plugin *dst, 
                            struct soap_plugin *src) 
{
    *dst = *src;
    dst->data = (void*)malloc(sizeof(struct http_digest_data));
    if (!dst->data) {
        return SOAP_EOM;
    }
    memcpy(dst->data, src->data, sizeof(struct http_digest_data));

    ((struct http_digest_data*)dst->data)->sendBuffer = NULL;
    return SOAP_OK;
}

/*
 * Deletes the contents of the plugin
 * Arguments:
 *  soap	- pointer to the soap runtime environment
 *  p       - the plugin
 */
static void http_digest_delete(struct soap *soap, struct soap_plugin *p) 
{
    struct http_digest_data *data = 
        (struct http_digest_data*)soap_lookup_plugin(soap, HTTP_DIGEST_ID);

    if (data) {
        if (data->sendBuffer) {
            free(data->sendBuffer);
        }
        free(data);
    }
}

/*
 * Open function. Will be called when connection opened. Used for saving parameters.
 * Arguments:
 *  soap	 - pointer to the soap runtime environment
 *  endpoint - the URL
 *  host     - machine to connect to
 *  port     - port on the host
 *
 * Returns SOAP_OK for suceess. Error value for error 
 */
static int http_digest_fopen(struct soap *soap, const char *endpoint, const char *host, 
                             int port) 
{
    struct http_digest_data *data =
                    (struct http_digest_data *)soap_lookup_plugin(soap, HTTP_DIGEST_ID);
    data->endpoint = (char*)endpoint;
    data->host = (char*)host;
    data->port = port;
    return data->fopen(soap, endpoint, host, port);
}

/*
 * Post header function. Used to identify parameters of the HTTP message
 * Arguments:
 *  soap	 - pointer to the soap runtime environment
 *  key      - the header key
 *  value    - the header value
 *
 * Returns SOAP_OK for suceess. Error value for error 
 */
static int http_digest_fposthdr(struct soap *soap, const char *key, const char *value) 
{
    struct http_digest_data *data = 
        (struct http_digest_data *)soap_lookup_plugin(soap, HTTP_DIGEST_ID);
    char *s1, *s2;

    // if this is the initial POST header then we initialize our send buffer 
    if (key && !value) {
        data->sendMsgSize = 0;
        data->sendBufferLength = 0;

        if (data->sendBuffer) {
            free(data->sendBuffer);
            data->sendBuffer = NULL;
        }

        data->password = soap->passwd;
        data->username = soap->userid;   
        soap->passwd = soap->userid = NULL;
        soap->frecv = http_digest_frecv;
    
        // read the method and URI form the key
        if (!strncmp(key, "GET", 3))
            memcpy(data->method, "GET", 4);
        else if (!strncmp(key, "POST", 4))
            memcpy(data->method, "POST", 5);
        else
            return soap->error = SOAP_EOM;

        s1 = const_cast<char*>(strstr(key, " "));
        if (!s1) {
            return soap->error = SOAP_EOM;
        }
        s1++;

        s2 = strstr(s1, " ");
        if (!s2) {
            return soap->error = SOAP_EOM;
        }
        
        if (sizeof(data->requestUrl) <= (size_t)(s2 - s1)) {
            return soap->error = SOAP_EOM;
        }
        memcpy(data->requestUrl, s1, s2-s1);
        data->requestUrl[s2-s1] = '\0';

    } else if (value) {
        // determine the maximum length of this message so that we can
        // correctly determine when we have completed the send 
        if (!strcmp(key, "Content-Length" )) {
            data->sendMsgSize += strtoul(value, NULL, 10);
        }
    }

    // calculate the header size
    data->sendMsgSize += 2;
    if (key) {
        data->sendMsgSize += strlen(key);
        if (value) {
            data->sendMsgSize += (strlen(value) + 2);
        }
    }
    return data->fposthdr(soap, key, value);
}

/*
 * Send function. Used to buffer the sent data and save for resends
 * Arguments:
 *  soap	 - pointer to the soap runtime environment
 *  buf      - buffer to be sent
 *  size     - size of data to send
 *
 * Returns SOAP_OK for suceess. Error value for error 
 */
static int http_digest_fsend(struct soap *soap, const char *buf, size_t size) 
{
    struct http_digest_data *data =
                    (struct http_digest_data *)soap_lookup_plugin(soap, HTTP_DIGEST_ID);
    size_t newBufferLen = data->sendBufferLength + size;

    if (!data->sendBuffer || (newBufferLen > data->sendMsgSize)) {
        if (newBufferLen > data->sendMsgSize) {
            data->sendMsgSize = newBufferLen;
        }
        data->sendBuffer = (char *)realloc(data->sendBuffer, data->sendMsgSize);
        if (!data->sendBuffer) {
            return SOAP_EOM;
        }
    }
    memcpy(data->sendBuffer + data->sendBufferLength, buf, size);
    data->sendBufferLength = newBufferLen;

    // if we haven't got the entire length of the message yet, then
    // we return to gsoap and let it continue 
    if (data->sendBufferLength < data->sendMsgSize) {
        return SOAP_OK;
    }

    // we've now got the entire message, now we can send the buffer 
    return data->fsend(soap, data->sendBuffer, data->sendBufferLength);
}

/*
 * Reads the next character. May need to read from the network
 * Arguments:
 *  data	 - pointer to the http digest structure
 *
 * Returns the next character or EOF for failure. 
 */
static char http_digest_getchar(struct http_digest_data *data) 
{
    size_t res;
    if (data->rcvIdx < data->rcvRead)
        return data->rcvBuffer[data->rcvIdx++];
    res = data->frecv(data->soap, (data->rcvBuffer + data->rcvRead),
                      (data->rcvSize - data->rcvRead));
    if (res <= 0)
        return EOF;
    data->rcvRead += res;
    return data->rcvBuffer[data->rcvIdx++];
}

/*
 * Reads the next HTTP header line.
 * Arguments:
 *  data	 - pointer to the http digest structure
 *  line     - buffer to store the line read
 *  len      - length of the line buffer
 *
 * Returns SOAP_OK for suceess. Error value for error. 
 */
static int http_digest_getline(struct http_digest_data *data, char *line, size_t len) 
{
    unsigned int i = len;
    char c = 0, *s = line;
    for (;;) {
        while (--i > 0) {
            c = http_digest_getchar(data);
            if (c == '\r')
                break;
            if (c == EOF)
                return SOAP_EOF;
            *s++ = c;
        }
        c = http_digest_getchar(data);
        if (c == '\n') {
            *s = '\0';
            if (i+1 == len) // empty line: end of HTTP header
                break;
            c = http_digest_getchar(data);
            data->rcvIdx--; // return to previous character
            if (c != ' ' && c != '\t') // HTTP line continuation? 
                break;
        } else if ((int)c == EOF)
            return SOAP_EOF;
    }
    return SOAP_OK;
}

/*
 * receive function. Used to look for digest authentication challenge.
 * If the challenge is found will calculate the response and resend.
 * Arguments:
 *  soap	 - pointer to the soap runtime environment
 *  buf      - buffer read data into
 *  size     - size of buf
 *
 * Returns number of characters read. 0 for error. 
 */
static size_t http_digest_frecv(struct soap *soap, char *buf, size_t size) {
    struct http_digest_data *data =
                    (struct http_digest_data *)soap_lookup_plugin(soap, HTTP_DIGEST_ID);
    char header[HDR_SIZE], authResponse[HDR_SIZE];
    static const char *CHALLANGE = "WWW-Authenticate: Digest";
    static const unsigned int SYN_DELAY = 400000;
    char *s;
    unsigned long httpStatus;
    size_t len;
    int found = 0;

    data->rcvBuffer = buf;
    data->rcvSize = size;
    data->rcvIdx = 0;
    data->rcvRead = 0;

    do {
        if (http_digest_getline(data, header, HDR_SIZE))
            goto _out;
        if ((s = strchr(header, ' ')))
            httpStatus = soap_strtoul(s, NULL, 10);
        else
            httpStatus = 0;

        if ((httpStatus != 100) && (httpStatus != 401))
            goto _out;

        for (;;) {
            if (http_digest_getline(data, header, SOAP_HDRLEN))
                goto _out;

            if (!*header)
                break;

            if ((httpStatus == 401) && !strncmp(header, CHALLANGE, strlen(CHALLANGE))) {
                found = 1;
                break;
            }
        }
    } while (httpStatus == 100);

    // if we got here httpStatus==401
    if (!found)
        goto _out;

    // header is HTTP digest challenge
    len = HDR_SIZE;
    if (CreateDigestResponse(data, header, &len, authResponse))
        goto _out;

    s = strstr(data->sendBuffer, "\r\n");
    if (!s)
        goto _out;

    s += 2; // point to the start of second line

    // reset rcvRead so that if error occurs will return 0.
    data->rcvRead = 0;

    //delay sending SYN to allow AMT to close connection gracefully
    usleep(SYN_DELAY); 
    
    soap->socket = data->fopen(soap, data->endpoint, data->host, data->port);
    if (soap->error || !soap_valid_socket(soap->socket))
        goto _out;
    
    if (data->fsend(soap, data->sendBuffer, s-data->sendBuffer) || 
        data->fsend(soap, authResponse, len) ||
        data->fsend(soap, "\r\n", 2) ||
        data->fsend(soap, s, data->sendBufferLength - (s-data->sendBuffer)))
        goto _out;
    
    // after send - send FIN if needed
#ifdef WITH_OPENSSL
    if (!soap->ssl && soap_valid_socket(soap->socket) && !soap->keep_alive)
        soap->fshutdownsocket(soap, (SOAP_SOCKET)soap->socket, 1); // Send TCP FIN 
#else
    if (soap_valid_socket(soap->socket) && !soap->keep_alive)
        soap->fshutdownsocket(soap, (SOAP_SOCKET)soap->socket, 1); // Send TCP FIN 
#endif

    data->rcvRead = data->frecv(soap, buf, size);

_out:
    if (data->sendBuffer) {
        free(data->sendBuffer);
        data->sendBuffer = NULL;
    }
    soap->frecv = data->frecv;
    return data->rcvRead;
}





