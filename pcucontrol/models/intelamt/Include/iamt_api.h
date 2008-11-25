/**********************************************************************
**                                                                   **
**                I N T E L   P R O P R I E T A R Y                  **
**                                                                   **
**   COPYRIGHT (c)  1993 - 2006       BY  INTEL  CORPORATION.  ALL   **
**   RIGHTS RESERVED.   NO PART OF THIS PROGRAM OR PUBLICATION MAY   **
**   BE  REPRODUCED,   TRANSMITTED,   TRANSCRIBED,   STORED  IN  A   **
**   RETRIEVAL SYSTEM, OR TRANSLATED INTO ANY LANGUAGE OR COMPUTER   **
**   LANGUAGE IN ANY FORM OR BY ANY MEANS, ELECTRONIC, MECHANICAL,   **
**   MAGNETIC,  OPTICAL,  CHEMICAL, MANUAL, OR OTHERWISE,  WITHOUT   **
**   THE PRIOR WRITTEN PERMISSION OF :                               **
**                                                                   **
**                      INTEL  CORPORATION                           **
**                                                                   **
**                2200 MISSION COLLEGE BOULEVARD                     **
**                                                                   **
**             SANTA  CLARA,  CALIFORNIA  95052-8119                 **
**                                                                   **
**********************************************************************/

//+--------------------------------------------------------------------
//
//
//  File:       iamt_api.h
//
//  Contents:   Header file for the Intel® AMT storage library.
//
//---------------------------------------------------------------------


#ifndef _PTHI_API_
#define _PTHI_API_

#include <wchar.h>
#ifdef _WIN32
#include <windows.h>
#include <Wincrypt.h>
#include <tchar.h>
#endif


#ifdef __cplusplus
extern "C" {
#endif

/* 
To enable compile time checking for Intel(r) AMT2 compatible usage use the following definition:
#define ENFORCE_IAMT2_USAGE
*/

#define ISVS_VERSION_MAJOR      2
#define ISVS_VERSION_MINOR      0


#ifndef VOID
typedef void                VOID;
#endif
typedef char                CHAR;
typedef unsigned char       UINT8;
typedef unsigned short      UINT16;
typedef unsigned int        UINT32;

#ifndef _WIN32
typedef char _TCHAR;
#endif

typedef UINT8 PT_UUID[16];

typedef UINT32  ISVS_APPLICATION_HANDLE;

#define ISVS_APPLICATION_NAME_FILTER    0xFFFFFFF0
#define ISVS_VENDOR_NAME_FILTER         0xFFFFFFF1
#define ISVS_INVALID_HANDLE             0xFFFFFFFF


typedef UINT32 PT_BOOLEAN;
static const   PT_BOOLEAN PTHI_FALSE = 0;
static const   PT_BOOLEAN PTHI_TRUE  = 1;


// ------------------------
// ISVS_VERSION
// ------------------------
typedef struct _ISVS_VERSION
{
	UINT8   MajorNumber;
	UINT8   MinorNumber;

} ISVS_VERSION;


// ------------------------
// PTSDK_UNICODE_STRING
// ------------------------
// UTF16 Unicode String
//  Length - The length in bytes of the string stored in Buffer.
//  MaximumLength - The maximum length in bytes of Buffer.
//  Buffer - Points to a buffer used to contain a string of wide characters.
//
// PTSDK_UNICODE_STRING types may not be null terminated
//
typedef struct _PTSDK_UNICODE_STRING
{
    UINT16  Length;
    UINT16  MaximumLength;
    UINT16  *Buffer;

} PTSDK_UNICODE_STRING;




// -----------------
// ISVS_GROUP
// -----------------
typedef UINT32  ISVS_GROUP_HANDLE;

typedef UINT32 ISVS_GROUP_PERMISSIONS;
static const   ISVS_GROUP_PERMISSIONS ISVS_GROUP_PERMISSIONS_READ_ONLY = 1;
static const   ISVS_GROUP_PERMISSIONS ISVS_GROUP_PERMISSIONS_READ_WRITE = 2;

typedef struct _PTSDK_PERMISSIONS_GROUP_ATTRIBUTES
{
    PTSDK_UNICODE_STRING     Name;
    ISVS_GROUP_PERMISSIONS   Permissions;

} PTSDK_PERMISSIONS_GROUP_ATTRIBUTES;


// -----------------
// ISVS_BLOCK
// -----------------

typedef UINT32  ISVS_BLOCK_HANDLE;

typedef struct _PTSDK_BLOCK_ATTRIBUTES
{
    UINT32                 BlockSize;
    PT_BOOLEAN             BlockHidden;
    PTSDK_UNICODE_STRING   BlockName;

} PTSDK_BLOCK_ATTRIBUTES;


// -----------------
// ISVS_APPLICATION
// -----------------

typedef struct _PTSDK_APPLICATION_ATTRIBUTES
{
    PTSDK_UNICODE_STRING    VendorName;
    PTSDK_UNICODE_STRING    ApplicationName;

} PTSDK_APPLICATION_ATTRIBUTES;


// ------------
// PT_STATUS
// ------------

typedef UINT32 PT_STATUS;

static const PT_STATUS PT_STATUS_SUCCESS                          = 0;
static const PT_STATUS PT_STATUS_INTERNAL_ERROR                   = 0x0001;
static const PT_STATUS PT_STATUS_NOT_READY                        = 0x0002;
static const PT_STATUS PT_STATUS_INVALID_PT_MODE                  = 0x0003;
static const PT_STATUS PT_STATUS_INVALID_MESSAGE_LENGTH           = 0x0004;
static const PT_STATUS PT_STATUS_TABLE_FINGERPRINT_NOT_AVAILABLE  = 0x0005;
static const PT_STATUS PT_STATUS_INTEGRITY_CHECK_FAILED           = 0x0006;
static const PT_STATUS PT_STATUS_UNSUPPORTED_ISVS_VERSION         = 0x0007;
static const PT_STATUS PT_STATUS_APPLICATION_NOT_REGISTERED       = 0x0008;
static const PT_STATUS PT_STATUS_INVALID_REGISTRATION_DATA        = 0x0009;
static const PT_STATUS PT_STATUS_APPLICATION_DOES_NOT_EXIST       = 0x000a;
static const PT_STATUS PT_STATUS_NOT_ENOUGH_STORAGE               = 0x000b;
static const PT_STATUS PT_STATUS_INVALID_NAME                     = 0x000c;
static const PT_STATUS PT_STATUS_BLOCK_DOES_NOT_EXIST             = 0x000d;
static const PT_STATUS PT_STATUS_INVALID_BYTE_OFFSET              = 0x000e;
static const PT_STATUS PT_STATUS_INVALID_BYTE_COUNT               = 0x000f;
static const PT_STATUS PT_STATUS_NOT_PERMITTED                    = 0x0010;
static const PT_STATUS PT_STATUS_NOT_OWNER                        = 0x0011;
static const PT_STATUS PT_STATUS_BLOCK_LOCKED_BY_OTHER            = 0x0012;
static const PT_STATUS PT_STATUS_BLOCK_NOT_LOCKED                 = 0x0013;
static const PT_STATUS PT_STATUS_INVALID_GROUP_PERMISSIONS        = 0x0014;
static const PT_STATUS PT_STATUS_GROUP_DOES_NOT_EXIST             = 0x0015;
static const PT_STATUS PT_STATUS_INVALID_MEMBER_COUNT             = 0x0016;
static const PT_STATUS PT_STATUS_MAX_LIMIT_REACHED                = 0x0017;
static const PT_STATUS PT_STATUS_INVALID_AUTH_TYPE                = 0x0018;
static const PT_STATUS PT_STATUS_AUTHENTICATION_FAILED            = 0x0019;
static const PT_STATUS PT_STATUS_INVALID_DHCP_MODE                = 0x001a;
static const PT_STATUS PT_STATUS_INVALID_IP_ADDRESS               = 0x001b;
static const PT_STATUS PT_STATUS_INVALID_DOMAIN_NAME              = 0x001c;

static const PT_STATUS PT_STATUS_REQUEST_UNEXPECTED               = 0x001e;
static const PT_STATUS PT_STATUS_INVALID_TABLE_TYPE               = 0x001f;
static const PT_STATUS PT_STATUS_INVALID_PROVISIONING_MODE        = 0x0020;
static const PT_STATUS PT_STATUS_UNSUPPORTED_OBJECT               = 0x0021;
static const PT_STATUS PT_STATUS_INVALID_TIME                     = 0x0022;
static const PT_STATUS PT_STATUS_INVALID_INDEX                    = 0x0023;
static const PT_STATUS PT_STATUS_INVALID_PARAMETER                = 0x0024;

static const PT_STATUS PT_STATUS_FLASH_WRITE_LIMIT_EXCEEDED       = 0x0026;

static const PT_STATUS PT_STATUS_NETWORK_IF_ERROR_BASE            = 0x0800;
static const PT_STATUS PT_STATUS_SDK_DEFINED_ERROR_BASE           = 0x1000;

static const PT_STATUS PTSDK_STATUS_INTERNAL_ERROR                = 0x1000;
static const PT_STATUS PTSDK_STATUS_NOT_INITIALIZED               = 0x1001;
static const PT_STATUS PTSDK_STATUS_LIB_VERSION_UNSUPPORTED       = 0x1002;
static const PT_STATUS PTSDK_STATUS_INVALID_PARAM                 = 0x1003;
static const PT_STATUS PTSDK_STATUS_RESOURCES                     = 0x1004;
static const PT_STATUS PTSDK_STATUS_HARDWARE_ACCESS_ERROR         = 0x1005;
static const PT_STATUS PTSDK_STATUS_REQUESTOR_NOT_REGISTERED      = 0x1006;
static const PT_STATUS PTSDK_STATUS_NETWORK_ERROR                 = 0x1007;
static const PT_STATUS PTSDK_STATUS_PARAM_BUFFER_TOO_SHORT        = 0x1008;
static const PT_STATUS PTSDK_STATUS_COM_NOT_INITIALIZED_IN_THREAD = 0x1009;
static const PT_STATUS PTSDK_STATUS_URL_REQUIRED				  = 0x100a;

// -------------------
// IN/OUT definitions
// -------------------
#ifdef IN
#undef IN
#endif
#define IN      const   /* input parameter (const)  */
#define OUT             /* output parameter         */
#define INOUT           /* input & output parameter */
#define OPTIONAL        /* optional parameter       */


#undef FALSE
#undef TRUE
#undef NULL

#define FALSE   0
#define TRUE    1
#define NULL    0

typedef int             BOOL;
typedef unsigned long   ULONG;
typedef char *          PCHAR;
typedef unsigned long * PULONG;

typedef struct _SESSION_HANDLE *SESSION_HANDLE;
typedef struct _SESSION_AUTHENTICATION_INFO SESSION_AUTHENTICATION_INFO;


PT_STATUS
ISVS_Initialize (
    INOUT   UINT32 *LibMajorVersion,
    INOUT   UINT32 *LibMinorVersion,
    OUT     UINT32 *LibBuildNumber
    );


PT_STATUS
ISVS_Uninitialize();
#ifdef _WIN32

PT_STATUS
ISVS_InitializeCOMinThread();

PT_STATUS 
ISVS_UninitializeCOMinThread();

#endif


#ifndef ENFORCE_IAMT2_USAGE
// ISVS 1.0 support 
PT_STATUS
ISVS_RegisterApplication(
    OUT SESSION_HANDLE              *SessionHandle,
    IN wchar_t                     *Username    OPTIONAL,
    IN wchar_t                     *Password    OPTIONAL,
    IN CHAR                        *TargetUrl,
    IN PT_UUID                     MachineUUID  OPTIONAL,
    IN PTSDK_UNICODE_STRING        *VendorName,
    IN PTSDK_UNICODE_STRING        *AppName,
    IN PTSDK_UNICODE_STRING        *EnterpriseName
    );
#endif


PT_STATUS
ISVS_RegisterApplicationEx(
    OUT SESSION_HANDLE             *SessionHandle,
    IN  wchar_t                    *Username    OPTIONAL,
    IN  wchar_t                    *Password    OPTIONAL,
    IN  CHAR                       *TargetUrl   ,
    IN  PT_UUID                    MachineUUID  OPTIONAL,
    IN  PTSDK_UNICODE_STRING       *VendorName,
    IN  PTSDK_UNICODE_STRING       *AppName,
    IN  PTSDK_UNICODE_STRING       *EnterpriseName,
	IN  SESSION_AUTHENTICATION_INFO          *AuthInfo   OPTIONAL
    );



SESSION_AUTHENTICATION_INFO* 
ISVS_CreateAuthInfo(
	IN  _TCHAR						*certificateName,
#ifdef _WIN32
	IN  PCCERT_CONTEXT				certificate,
	IN	BOOL						krb
#else
	IN  _TCHAR						*certificatePass
#endif
	);

VOID
ISVS_FreeAuthInfo(
	IN SESSION_AUTHENTICATION_INFO* authInfo
	);


PT_STATUS
ISVS_GetRegisteredApplications(
    IN    SESSION_HANDLE           SessionHandle,
    IN    UINT32                   StartIndex,
    OUT   UINT32                   *TotalRegisteredAppCount,
    INOUT UINT32                   *AppHandleCount,
    OUT   ISVS_APPLICATION_HANDLE  AppHandles[]        // [<AppHandleCount>]
    );


PT_STATUS
ISVS_GetCurrentApplicationHandle (
    IN  SESSION_HANDLE             SessionHandle,
    OUT	ISVS_APPLICATION_HANDLE    *AppHandle
    );


PT_STATUS
ISVS_GetApplicationAttributes(
    IN    SESSION_HANDLE                    SessionHandle,
    IN    ISVS_APPLICATION_HANDLE           ApplicationBeingRequested,
    INOUT PTSDK_APPLICATION_ATTRIBUTES      *ApplicationAttributes
    );


PT_STATUS
ISVS_UnregisterApplication(
    IN SESSION_HANDLE       SessionHandle
    );


PT_STATUS
ISVS_RemoveApplication(
    SESSION_HANDLE          SessionHandle
    );


PT_STATUS
ISVS_GetBytesAvailable(
    IN  SESSION_HANDLE      SessionHandle,
    OUT UINT32              *BytesAvailable
    );


PT_STATUS
ISVS_AllocateBlock(
    IN  SESSION_HANDLE          SessionHandle,
    IN  UINT32                  BytesRequested,
    IN  PT_BOOLEAN              BlockHidden,
    IN  PTSDK_UNICODE_STRING    *BlockName,
    OUT ISVS_BLOCK_HANDLE       *BlockHandle
    );


PT_STATUS
ISVS_GetAllocatedBlocks(
    IN    SESSION_HANDLE            SessionHandle,
    IN    ISVS_APPLICATION_HANDLE   BlockOwnerApplication,
    IN    UINT32                    StartIndex,
    OUT   UINT32                    *TotalAllocatedBlockCount,
    INOUT UINT32                    *BlockHandleCount,
    OUT   ISVS_BLOCK_HANDLE         BlockHandles[]      // [<BlockHandleCount>]
    );


PT_STATUS
ISVS_GetBlockAttributes(
    IN    SESSION_HANDLE            SessionHandle,
    IN    ISVS_BLOCK_HANDLE         BlockHandle,
    INOUT PTSDK_BLOCK_ATTRIBUTES    *BlockAttributes
    );


PT_STATUS
ISVS_DeallocateBlock(
    IN  SESSION_HANDLE          SessionHandle,
    IN  ISVS_BLOCK_HANDLE       BlockHandle
    );


PT_STATUS
ISVS_WriteBlock(
    IN  SESSION_HANDLE          SessionHandle,
    IN  ISVS_BLOCK_HANDLE       BlockHandle,
    IN  UINT32                  ByteOffset,
    IN  UINT32                  ByteCount,
    OUT UINT32                  *BytesWritten,
    IN  UINT8                   Data[]
    );


PT_STATUS
ISVS_ReadBlock(
    IN    SESSION_HANDLE        SessionHandle,
    IN    ISVS_BLOCK_HANDLE     BlockHandle,
    IN    UINT32                ByteOffset,
    IN    UINT32                ByteCount,
    OUT   UINT32                *BytesRead,
    OUT   UINT8                 Data[]
    );


PT_STATUS
ISVS_LockBlock(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle
    );


PT_STATUS
ISVS_UnlockBlock(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle
    );


PT_STATUS
ISVS_SetBlockName(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN PTSDK_UNICODE_STRING     *BlockName
    );


PT_STATUS
ISVS_SetBlockVisibility(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN PT_BOOLEAN               BlockHidden
    );


PT_STATUS
ISVS_AddPermissionsGroup(
    IN  SESSION_HANDLE          SessionHandle,
    IN  ISVS_BLOCK_HANDLE       BlockHandle,
    IN  ISVS_GROUP_PERMISSIONS  GroupPermissions,
    IN  PTSDK_UNICODE_STRING    *GroupName,
    OUT ISVS_GROUP_HANDLE       *GroupHandle
    );


PT_STATUS
ISVS_GetPermissionsGroups(
    IN    SESSION_HANDLE        SessionHandle,
    IN    ISVS_BLOCK_HANDLE     BlockHandle,
    IN    UINT32                StartIndex,
    OUT   UINT32                *TotalGroupCount,
    INOUT UINT32                *GroupHandleCount,
    OUT   ISVS_GROUP_HANDLE     GroupHandles[]  // [<HandleCount>]
    );


PT_STATUS
ISVS_GetPermissionsGroupAttributes(
    IN    SESSION_HANDLE                        SessionHandle,
    IN    ISVS_BLOCK_HANDLE                     BlockHandle,
    IN    ISVS_GROUP_HANDLE                     GroupHandle,
    INOUT PTSDK_PERMISSIONS_GROUP_ATTRIBUTES    *GroupAttributes
    );


PT_STATUS
ISVS_RemovePermissionsGroup(
    IN SESSION_HANDLE          SessionHandle,
    IN ISVS_BLOCK_HANDLE       BlockHandle,
    IN ISVS_GROUP_HANDLE       GroupHandle
    );


PT_STATUS
ISVS_SetPermissionsGroupName(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN ISVS_GROUP_HANDLE        GroupHandle,
    IN PTSDK_UNICODE_STRING     *GroupName
    );


PT_STATUS
ISVS_SetPermissionsGroupPermissions(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN ISVS_GROUP_HANDLE        GroupHandle,
    IN ISVS_GROUP_PERMISSIONS   Permissions
    );


PT_STATUS
ISVS_AddPermissionsGroupMembers(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN ISVS_GROUP_HANDLE        GroupHandle,
    IN UINT32                   MemberHandleCount,
    IN ISVS_APPLICATION_HANDLE  MemberHandles[]      // [<MemberHandleCount>]
    );


PT_STATUS
ISVS_GetPermissionsGroupMembers(
    IN    SESSION_HANDLE            SessionHandle,
    IN    ISVS_BLOCK_HANDLE         BlockHandle,
    IN    ISVS_GROUP_HANDLE         GroupHandle,
    IN    UINT32                    StartIndex,
    OUT   UINT32                    *TotalMemberCount,
    INOUT UINT32                    *MemberHandleCount,
    OUT   ISVS_APPLICATION_HANDLE   MemberHandles[]      // [<MemberHandleCount>]
    );


PT_STATUS
ISVS_RemovePermissionsGroupMembers(
    IN SESSION_HANDLE           SessionHandle,
    IN ISVS_BLOCK_HANDLE        BlockHandle,
    IN ISVS_GROUP_HANDLE        GroupHandle,
    IN UINT32                   MemberHandleCount,
    IN ISVS_APPLICATION_HANDLE  MemberHandles[]      // [<MemberHandleCount>]
    );


PT_STATUS
ISVS_GetTimeoutValues(
    IN  SESSION_HANDLE          SessionHandle,
    OUT UINT32                  *RegistrationTimeout,
    OUT UINT32                  *LockTimeout
    );


PT_STATUS
ISVS_GetHostUUID(
    OUT PT_UUID         Uuid
    );

#ifndef ENFORCE_IAMT2_USAGE
// ISVS 1.0 support 
PT_STATUS
ISVS_GetAPIVersion(
    IN  wchar_t             *Username   OPTIONAL,
    IN  wchar_t             *Password   OPTIONAL,
    IN  CHAR                *TargetUrl,
    OUT ISVS_VERSION        *Version
    );
#endif


PT_STATUS
ISVS_GetAPIVersionEx(
    OUT ISVS_VERSION    *Version,
    IN  wchar_t             *Username   OPTIONAL,
    IN  wchar_t             *Password   OPTIONAL,
    IN  CHAR                *TargetUrl  ,
	IN  SESSION_AUTHENTICATION_INFO   *AuthInfo   OPTIONAL
    );


PT_STATUS
ISVS_GetBlockWriteEraseLimit(
    IN SESSION_HANDLE       SessionHandle,
    IN ISVS_BLOCK_HANDLE    BlockHandle,
    OUT UINT32              *WriteEraseLimit
    );



VOID
ISVS_GetLastNetworkError(
    IN  SESSION_HANDLE  SessionHandle  OPTIONAL,
    OUT VOID            *NetworkError
    );


#ifdef __cplusplus
}
#endif

#endif // _PTHI_API_

