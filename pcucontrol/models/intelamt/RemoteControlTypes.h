//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2004 - 2006.
//
//  File:       RemoteControlTypes.h
//
//  Contents:   Sample code for an Intel® AMT Network client.
//
//  Notes:      This file contains type definitions used throughout the code
//				and constants as described in the "Intel® AMT Network Design 
//				Guide".
//
//----------------------------------------------------------------------------

#ifndef _REMOTE_CONTROL_TYPES__H_
#define _REMOTE_CONTROL_TYPES__H_

/*
 * limits.h for UINT_MAX
 */
#include <limits.h>

/*
 * Type definitions
 */
typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long uint64;
typedef unsigned char BYTE;

/*
 * Remote Control sample
 * command line parameters
 */
static const char *POWER = "-p";
static const char *CAPABILITIES = "-c";
static const char *REMOTE = "-r";
static const char *API_TEST = "-A";
static const char *REDUCED_API_TEST = "-B";
static const int MIN_NUM_OF_CL_PARAMETERS = 3;

/*
 * Command line options
 */
enum Options
{
	// Remote Control sample options
	OPT_POWER,
	OPT_CAPABILITIES,
	OPT_REMOTE,
	OPT_API_TEST,
	OPT_REDUCED_API_TEST,
};

/*
 * Constants
 */
static const uint32 NO_VALUE = UINT_MAX;

/* 
 * Remote control commands
 */
enum RemoteControlCommand
{
	Reset           = 16, //0x10
	PowerUp         = 17, //0x11
	PowerDown       = 18, //0x12
	PowerCycleReset = 19, //0x13
	SetBootOptions  = 33, //0x21
};

/*
 * Special commands
 */
enum SpecialCommand
{

	NOP                         = 0, // 0x00
	ForcePxeBoot                = 1, // 0x01
	ForceHardDriveBoot          = 2, // 0x02
	ForceHardDriveSafeModeBoot  = 3, // 0x03
	ForceDiagnosticsBoot        = 4, // 0x04
	ForceCdOrDvdBoot            = 5, // 0x05
	// 06h-0BFh Reserved for future ASF definition 
	IntelOemCommand             = 193, // 0x0C1
	// 0C1h-0FFh Reserved FOR OEM 
}; 

/*
 * Standard boot options
 *
 * Following boot options can be defined by using the bitwise OR operator. 
 * For example: 
 * unsigned short bootOptions = LockPowerButton | LockKeyboard | FirmwareVerbosityVerbose
 */
enum BootOptions
{

	LockPowerButton     = 2,	// 1 << 1
	LockResetButton     = 4,	// 1 << 2
	LockKeyboard        = 32,	// 1 << 5
	LockSleepButton     = 64,	// 1 << 6
	UserPasswordBypass  = 2048,	// 1 << 11 
	ForceProgressEvents = 4096,	// 1 << 12

	// only one from the Firmware verbosity options can be used
	FirmwareVerbositySystemDefault  = 0,	 // system default
	FirmwareVerbosityQuiet          = 8192,	 // 1 << 13 minimal screen activity
	FirmwareVerbosityVerbose        = 16384, // 1 << 14 all messages appear on the screen
	FirmwareVerbosityScreen         = 24576, // 3 << 13 blank, no messages appear on the screen.

	ConfigurationDataReset          = 32768, // 1 << 14
};

/*
 * Reserved bits for checking
 * correctness of the Boot Options settings
 */
const uint32 BootOptionsReservedBits = 1817;


/*
 * Special Command Parameters
 *
 * Following boot options can be defined by using the bitwise OR operator. 
 * For example: 
 * unsigned short specialCommParam = UseIderCD | ReflashBios
 */
enum SpecialCommandParameters
{
    UndefinedSpecialCommandParameter = 0,
	UseIderFloppy	= 1,   // use floppy as IDER boot device
	ReflashBios     = 4,   // 1 << 2
	BiosSetup       = 8,   // 1 << 3
	BiosPause       = 16,  // 1 << 4
	UseIderCD		= 257, // 1 | (1 << 8) use CD/DVD as IDER boot device
};

/*
 * Reserved bits for checking
 * correctness of the Special Parameters settings
 */
const uint32 SpecialCommandParametersReservedBits = 65248;

/*
 * OEM Parameters - Intel(R) AMT proprietary boot options
 */
enum OEMParameters
{
    UndefinedOEMParameter = 0,
	UseSol          = 1,   // 1 << 1
};

/*
 * IANA numbers
 */
enum IanaNumbers
{
	IntelIanaNumber = 343,
	ASFIanaNumber   = 4542,
};


/*
 * The remote control capabilities supported by the Intel(R) AMT:
 *
 * OEM defined capabilities
 */
enum OemDefinedCapabilitiesSupported
{
	SuppIDER        = 1,
	SuppSOL         = 2,
	SuppBiosReflash = 4,
	SuppBiosSetup   = 8,
	SuppBiosPause   = 16,

};

/*
 * System capabilities
 */
enum SystemCapabilitiesSupported
{
	SuppPowerCycleReset  = 1,
	SuppPowerDown        = 2,
	SuppPowerUp          = 4,
	SuppReset            = 8,
};

/*
 * Special commands
 */
enum SpecialCommandSupported
{
	SuppForcePXEBoot                = 256,
	SuppForceHardDriveBoot          = 512,
	SuppForceHardDriveSafeModeBoot  = 1024,
	SuppForceDiagnosticBoot         = 2048,
	SuppForceCDorDVDBoot            = 4096,
};


/*
 * System Firmware capabilities
 */
enum SystemFirmwareCapabilitiesSupported
{
	SuppVerbosityScreenBlank    = 1,
	SuppPowerButtonLock         = 2,
	SuppResetButtonLock         = 4,
	SuppKeyboardLock            = 32,
	SuppSleepButtonLock         = 64,
	SuppUserPasswordBypass      = 2048,
	SuppForcedProgressEvents    = 4096,
	SuppVerbosityVerbose        = 8192,
	SuppVerbosityQuiet          = 16384,
	SuppConfigurationDataReset  = 32768,
};

#endif // _REMOTE_CONTROL_TYPES__H_

