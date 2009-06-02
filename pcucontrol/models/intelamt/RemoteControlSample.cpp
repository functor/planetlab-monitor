//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2004 - 2006.
//
//  File:       RemoteControlSample.cpp 
//
//  Contents:   Sample code for an Intel® AMT Network client.
//
//  Notes:      this file contains routines that call (using SOAP) 
//              the RemoteControl functions of the Intel(R) AMT 2.0 as 
//              defined in the "Intel(R) AMT Network Design Guide".
//
//----------------------------------------------------------------------------

#include "CommonDefinitions.h"
#include "RemoteControlTypes.h"
#include "RemoteControlSoapBinding.nsmap"

/*
 * Function prototypes
 */
void Usage(char *cmd);
bool GetUserValues(uint8 *&command, uint32 *&ianaOemNumber, 
				   uint8 *&specialCommand, uint16 *&specialCommandParameter, 
				   uint16 *&bootOptions, uint16 *&OEMParameters);
void DisplaySystemCapabilities(uint8 specialCommandsSupported);
void DisplaySpecialCommand(uint16 specialCommandsSupported);
void DisplaySystemFirmwareCapabilities(uint32 systemFirmwareCapabilities);
void DisplayOemDefinedCapabilities(uint32 OemDefinedCapabilities);
bool ExecuteGetSystemPowerstate(Soap *server, bool verbose = true);
bool ExecuteGetRemoteControlCapabilities(Soap *server, bool verbose = true);
bool ExecuteRemoteControl(Soap *server, bool default_val = false, uint8 icommand=Reset);
bool MainFlow(Soap *server,int option,bool verbose);
bool ValidateOption(char *option, int *parameter);

/*
 * This is the main entry point
 */
int main(int argc, char* argv[])
{
	// Command line parameter
	char *option = NULL;
	// Client certificate's name
	char *certName = NULL;
#ifndef _WIN32
	// Password for keys file openning
	char *certPass = NULL;
#else
    // True if an authentication scheme is Kerberos, 
    // otherwise the authentication scheme is digest
    bool krb = true;
#endif
	// Target URL
	char *target = NULL;
	// Target username
	char *username = NULL;
	// Target password
	char *password = NULL;
	// Command line without app name and parameter
	char **commandLine = NULL;
	int commandLineLength = argc;
	int parameter;
	bool verbose = false;
	

	if( !GetOption(&commandLineLength,argv,
		MIN_NUM_OF_CL_PARAMETERS,&option,&commandLine) ||
		!ValidateOption(option,&parameter) ||
#ifndef _WIN32
		!ParseCommandLine(commandLineLength,commandLine,&target,
		&certName,&certPass,&verbose,&username,&password)
#else
		!ParseCommandLine(commandLineLength,commandLine,&target,
		&certName,NULL,&krb,&verbose,&username,&password)
#endif
		)
	{
		Usage(argv[0]);
		return 1;
	}

    // The last parameter should be true for local application
    // and false for remote application
#ifndef _WIN32
	Soap server(target,certName,certPass,username,password);
#else
	Soap server(target,certName,username,password,false,krb);
#endif

	if(MainFlow(&server,parameter,verbose) != true)
	{
		return 1;
	}
	return 0;
}

/*
 * Validates an option passed in the command line.
 * Arguments:
 *	option - command line option
 *  parameter - pointer to the variable that will hold 
 *              type of the action the apllication 
 *              will perform.
 * Return value:
 *  true - on succeed
 *  false - on failure (command line option not recognized)
 */
bool ValidateOption(char *option, int *parameter)
{
	if(!option)
	{
		return false;
	}
	bool status = true;
	if(!strcmp(option,POWER))
	{
		*parameter = OPT_POWER;
	}
	else if(!strcmp(option,CAPABILITIES))
	{
		*parameter = OPT_CAPABILITIES;
	}
	else if(!strcmp(option,REMOTE))
	{
		*parameter = OPT_REMOTE;
	}
	else if(!strcmp(option,API_TEST))
	{
		*parameter = OPT_API_TEST;
	}
	else if(!strcmp(option,REDUCED_API_TEST))
	{
		*parameter = OPT_REDUCED_API_TEST;
	}
	else
	{
		status = false;
	}
	return status;
}

/*
 * Function that performs the main flow of Remote Control sample
 * Arguments:
 *  soap - pointer to the runtime environment 
 *  option - variable that holds type of the action the apllication 
 *           will perform
 *  verbose - boolean value for API test 
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool MainFlow(Soap *server, int option, bool verbose)
{
	bool status = true;
	switch(option)
	{
		case OPT_POWER:
			status = ExecuteGetSystemPowerstate(server);
			break;
		case OPT_CAPABILITIES:
			status = ExecuteGetRemoteControlCapabilities(server);
			break;
		case OPT_REMOTE:
			status = ExecuteRemoteControl(server);
			break;
		case OPT_API_TEST:
			if((status = ExecuteGetSystemPowerstate(server,verbose)) == false)
			{
				return status;
			}
			if((status = ExecuteGetRemoteControlCapabilities(server,verbose)) == false)
			{
				return status;
			}	
			/* Ensure that the machine is powered up before trying to
			 * 'reset' it, since a reset on a down node will fail. */
			/*if ((status = ExecuteRemoteControl(server,true,PowerDown)) == false)
			{
				return status;
			}
			sleep(10); */
			if ((status = ExecuteRemoteControl(server,true,PowerUp)) == false)
			{
				return status;
			}
			sleep(5);
			if ((status = ExecuteRemoteControl(server,true,Reset)) == false)
			{
				return status;
			}
			break;
		case OPT_REDUCED_API_TEST:			
			if((status = ExecuteGetSystemPowerstate(server,verbose)) == false)
			{
				return status;
			}
			if((status = ExecuteGetRemoteControlCapabilities(server,verbose)) == false)
			{
				return status;
			}	
			break;
		default:
			status = false;
	}

	return status;
}

/*
 * Prints a usage information for the user.
 */
void Usage(char *cmd)
{
	printf("Usage:\n");
#ifndef _WIN32
    printf("\t %s <opt> [%s] [%s <name> %s <pass>] http[s]:", cmd, VERBOSE, CERT_NAME, CERT_PASS);
#else
	printf("\t %s <opt> [%s] [%s <username> %s <password>] [%s <name>] http[s]:", 
        cmd, VERBOSE, USER, PASS, CERT_NAME);
#endif
	printf("//<Hostname>:<Port>/<RemoteControlUri> ");
#ifndef _WIN32
	printf("[%s <username> %s <password>]\n",USER,PASS); 
#endif
	printf("\nWhere <opt> is :\n");
	printf("\t %s : GetSystemPowerstate\n",POWER);
	printf("\t %s : GetRemoteControlCapabilities\n",CAPABILITIES);
	printf("\t %s : RemoteControl\n",REMOTE);
	printf("\t %s : perform API test\n",API_TEST);
	printf("\t %s : perform API test without boot\n",REDUCED_API_TEST);
	printf("\t To run API test in verbose mode include %s option\n", VERBOSE);
	PrintAuthenticationNote();
	printf("\nExample:\n");
	printf("\t %s %s ", cmd, POWER);
	printf("http://hostname:16992/RemoteControlService\n");
#ifndef _WIN32
    printf("\t %s %s %s MyCert %s Pass https://hostname:16993/RemoteControlService\n",   
        cmd, POWER, CERT_NAME, CERT_PASS);
#else
	printf("\t %s %s %s MyCert https://hostname:16993/RemoteControlService\n",   
		cmd, POWER, CERT_NAME);
#endif
}

/*
 * Queries (using SOAP) and display the system power state
 * Arguments:
 *  server	- pointer to the runtime environment 
 *  url		- address of the web service		
 *  verbose - boolean value for API test 
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool ExecuteGetSystemPowerstate(Soap* server, bool verbose)
{
	int res;
	bool status;

	server->Init();

	// gSOAP structures for handling 
	// request and response information
	_rci__GetSystemPowerState request;
	_rci__GetSystemPowerStateResponse response;

	FunctionCall("GetSystemPowerState");	
	res = soap_call___rci__GetSystemPowerState(server->GetSoap(),
		server->GetIp(),NULL, &request, &response);

	if((status = 
		CheckReturnStatus(res,
		response.Status,
		"GetSystemPowerState")) == true)
	{
		if(verbose)
		{
			printf("\nSystemPowerstate is: %u\n", response.SystemPowerState);
		}
		else
		{
			PrintSuccess();
		}
	}

	return status;
}

/*
 * Queries (using SOAP) and display the Intel(R) AMT
 * device remote control capabilities
 * Arguments:
 *  server	- pointer to the runtime environment 
 *  url		- address of the web service
 *  verbose - boolean value for API test 
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool ExecuteGetRemoteControlCapabilities(Soap* server, bool verbose)
{
	int res;
	bool status;

	server->Init();

	// gSOAP structures for handling 
	// request and response information
	_rci__GetRemoteControlCapabilities request;
	_rci__GetRemoteControlCapabilitiesResponse response;

	FunctionCall("GetRemoteControlCapabilities");	
	res = soap_call___rci__GetRemoteControlCapabilities(server->GetSoap(), 
		server->GetIp(),NULL, &request, &response);

	if((status = CheckReturnStatus(res,response.Status,"GetRemoteControlCapabilities")) == true)
	{
		if(verbose)
		{
			printf("\nRemote Control Capabilities\n");
			printf("---------------------------------------\n");

			printf("IanaOemNumber = %u\n", response.IanaOemNumber);

			DisplayOemDefinedCapabilities(response.OemDefinedCapabilities);

			printf("\n");
			DisplaySpecialCommand(response.SpecialCommandsSupported);

			printf("\n");
			DisplaySystemCapabilities(response.SystemCapabilitiesSupported);

			printf("\n");
			DisplaySystemFirmwareCapabilities(response.SystemFirmwareCapabilities);

			printf("\n");
		}
		else
		{
			PrintSuccess();
		}
	}

	return status;
}

/*
 * Controls remotely (using SOAP) the boot and power state of 
 * Intel(R) AMT-managed PC.
 * Arguments:
 *  server	- pointer to the runtime environment 
 *  url		- address of the web service 
 *  def_values - if false request values from user  
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool ExecuteRemoteControl(Soap* server,bool def_values, uint8 icommand)
{
	int res;
	bool status = true;

	server->Init();

	// gSOAP structures for handling 
	// request and response information
	_rci__RemoteControl request;
	_rci__RemoteControlResponse response;

	// example values
	uint8 *command = new uint8(icommand);
	uint32 *ianaOemNumber = new uint32(IntelIanaNumber);
	uint8 *specialCommand = NULL; //none
	uint16 *oemParameter = NULL; //none
	uint16 *bootOptions = NULL; //none
	uint16 *specialCommandParameters = NULL; //none

	if(!def_values)
	{
		// To use default values above, comment the following line.
		if(!GetUserValues(command, ianaOemNumber, specialCommand, oemParameter, 
			bootOptions, specialCommandParameters))
		{
			status = false;
		}
	}

	if(status == true)
	{
		switch(*command)
		{
		case Reset:
			request.Command = rci__RemoteControlCommandType__16;
			break;
		case PowerUp:
			request.Command = rci__RemoteControlCommandType__17;
			break;
		case PowerDown:
			request.Command = rci__RemoteControlCommandType__18;
			break;
		case PowerCycleReset:
			request.Command = rci__RemoteControlCommandType__19;
			break;
		case SetBootOptions:
			request.Command = rci__RemoteControlCommandType__33;
			break;
		default:
			break;
		}

		if(specialCommand == NULL)
		{
			request.SpecialCommand = NULL;
		}
		else
		{
			request.SpecialCommand = new rci__SpecialCommandType;
			switch(*specialCommand)
			{
			case NOP:
				*(request.SpecialCommand) = rci__SpecialCommandType__0;
				break;
			case ForcePxeBoot:
				*(request.SpecialCommand) = rci__SpecialCommandType__1;
				break;
			case ForceHardDriveBoot:
				*(request.SpecialCommand) = rci__SpecialCommandType__2;
				break;
			case ForceHardDriveSafeModeBoot:
				*(request.SpecialCommand) = rci__SpecialCommandType__3;
				break;
			case ForceDiagnosticsBoot:
				*(request.SpecialCommand) = rci__SpecialCommandType__4;
				break;
			case ForceCdOrDvdBoot:
				*(request.SpecialCommand) = rci__SpecialCommandType__5;
				break;
			case IntelOemCommand:
				*(request.SpecialCommand) = rci__SpecialCommandType__193;
				break;
			default:
				break;
			}
		}

		request.IanaOemNumber = *ianaOemNumber;
		request.BootOptions = bootOptions;
		request.OEMparameters = oemParameter;
		request.SpecialCommandParameter = specialCommandParameters;

		FunctionCall("RemoteControl");	
		res = soap_call___rci__RemoteControl(server->GetSoap(),
			server->GetIp(),NULL, &request, &response);

		if((status = CheckReturnStatus(res,response.Status,"RemoteControl")) == true)
		{
			PrintSuccess();
		}

		if(request.SpecialCommand != NULL)
		{
			delete request.SpecialCommand;
			request.SpecialCommand = NULL;
		}
	}

	// cleanup heap allocated memory 
	if(command != NULL)
	{
		delete command;
		command = NULL;
	}
	if(ianaOemNumber != NULL)
	{
		delete ianaOemNumber;
		ianaOemNumber = NULL;
	}
	if(specialCommand != NULL)
	{
		delete specialCommand;
		specialCommand = NULL;
	}
	if(oemParameter != NULL)
	{
		delete oemParameter;
		oemParameter = NULL;
	}
	if(bootOptions != NULL)
	{
		delete bootOptions;
		bootOptions = NULL;
	}
	if(specialCommandParameters != NULL)
	{
		delete specialCommandParameters;
		specialCommandParameters = NULL;
	}

	return status;
}

/*
 * Get user's settings for the RemoteControl function
 * Arguments & return values:
 *	command	- specifies the boot or power state operation to be performed
 *	ianaOemNumber	- specifies an IANA-assigned Enterprise Number
 *	specialCommand	- specifies an optional modification to the boot behavior
 *	OemParameter	- specifies Intel® AMT proprietary boot options 
 *	bootOptions		- specifies standard boot options 
 *	specialCommandParameters - specifies an optional modification to the 
 *							   boot behavior
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool GetUserValues(uint8 *&command, uint32 *&ianaOemNumber, 
				   uint8 *&specialCommand, uint16 *&oemParameter, 
				   uint16 *&bootOptions, uint16 *&specialCommandParameters)
{
	uint32 tmp;

	printf("Please specify the following parameters\n");

	// Get mandatory parameters

	// Get Command
	printf("\n\tCommand");
    printf("\n\t=======");
	printf("\nPossible values:");
	printf("\n\t%u (Reset)",Reset);
	printf("\n\t%u (PowerUp)",PowerUp);
	printf("\n\t%u (PowerDown)",PowerDown);
	printf("\n\t%u (PowerCycleReset)",PowerCycleReset);
	printf("\n\t%u (SetBootOptions)\n>",SetBootOptions);
	scanf("%u", &tmp);

	// verify command value 
	if ( tmp == Reset ||
		 tmp == PowerUp ||
		 tmp == PowerDown ||
		 tmp == PowerCycleReset ||
		 tmp == SetBootOptions)
	{
		// sanity check
		if ( command == NULL )
		{
			command = new uint8();
		}
		*command = (uint8)tmp;
	}
	else
	{
		goto ILLEGAL_INPUT;
	}

	// If command is Set Boot Options, ianaOemNumber 
	// should be IntelIanaNumber.
	if( *command == SetBootOptions )
	{
		// sanity check
		if ( ianaOemNumber == NULL )
		{
			ianaOemNumber = new uint32();
		}

		printf("\nSetBootOptions command selected. ");
		printf("Iana OEM Number is IntelIanaNumber (%u)\n",IntelIanaNumber);

		*ianaOemNumber = (uint32)IntelIanaNumber;

	}
	else
	{
		// Get Iana number
		printf("\n\tIana OEM Number");
        printf("\n\t===============");
		printf("\nPossible values:");
		printf("\n\t%u (IntelIanaNumber)", IntelIanaNumber);
		printf("\n\t%u (ASFIanaNumber)\n>", ASFIanaNumber);
		scanf("%u", &tmp);

		// verify ianaOemNumber value
		if ( tmp == IntelIanaNumber ||
			tmp == ASFIanaNumber )
		{
			// sanity check
			if ( ianaOemNumber == NULL )
			{
				ianaOemNumber = new uint32();
			}
			*ianaOemNumber = (uint32)tmp;
		}
		else
		{
			goto ILLEGAL_INPUT;
		}
	}

	// if power down, all other parameters should not be sent.
	if ( *command == PowerDown )
	{
		specialCommand = NULL;
		oemParameter = NULL;
		bootOptions = NULL;
		specialCommandParameters = NULL;
		return true;
	}

	// Get optional parameters

	// Get Special Command
	printf("\n\tSpecial Command");
    printf("\n\t===============");
	printf("\nPossible values:");

	printf("\n\t%d (No Special Command)",-1);
	printf("\n\t%u (NOP)",NOP);
	printf("\n\t%u (ForcePxeBoot)",ForcePxeBoot);
	printf("\n\t%u (ForceHardDriveBoot)",ForceHardDriveBoot);
	printf("\n\t%u (ForceHardDriveSafeModeBoot)",ForceHardDriveSafeModeBoot);
	printf("\n\t%u (ForceDiagnosticsBoot)",ForceDiagnosticsBoot);
	printf("\n\t%u (ForceCdOrDvdBoot)",ForceCdOrDvdBoot);
	printf("\n\t%u (IntelOemCommand)\n>",IntelOemCommand);
	scanf("%u", &tmp);

	// verify specialCommand value
	if ( tmp == NO_VALUE ||
		 tmp == NOP ||
		 tmp == ForcePxeBoot ||
		 tmp == ForceHardDriveBoot ||
		 tmp == ForceHardDriveSafeModeBoot ||
		 tmp == ForceDiagnosticsBoot ||
		 tmp == ForceCdOrDvdBoot ||
		 tmp == IntelOemCommand )
	{
		if ( tmp == NO_VALUE )
		{
			specialCommand = NULL;
		}
        else if(tmp == IntelOemCommand &&
                *ianaOemNumber != IntelIanaNumber)
        {
            printf("Error: Special Command value %d is legal", IntelOemCommand);
            printf(" only for IanaOemNumber value %d", IntelIanaNumber);
            exit(1);
        }
		else
		{
			// sanity check
			if ( specialCommand == NULL )
			{
				specialCommand = new uint8();
			}
			*specialCommand = (uint8)tmp;
		}
	}
	else
	{
		goto ILLEGAL_INPUT;
	}

	// Get OEM Parameter
	// if ianaOemNumber is ASFIanaNumber, oemParameters should not be sent .
	if ( *ianaOemNumber != IntelIanaNumber )
	{
		oemParameter = NULL;
	}
	else
	{
		printf("\n\tOEM Parameters");
        printf("\n\t==============");
        printf("\nPossible values:");
        printf("\n\t%d (No OEM Parameters)",-1);
		printf("\n\t%d (Undefined OEM Parameter)",UndefinedOEMParameter);
		printf("\n\t%u (UseSol)\n>",UseSol);
		scanf("%u", &tmp);
		if ( tmp == NO_VALUE )
		{
			oemParameter = NULL;
		}
		else
		{
			// sanity check
			if ( oemParameter == NULL )
			{
				oemParameter = new uint16();
			}
			*oemParameter = (uint16) tmp;
		}
	}

	// Get Special Command Parameters
	printf("\n\tSpecial Command Parameters");
    printf("\n\t==========================");
	printf("\nPossible values:");

	// Special Command is not equal to 0xC1 (IntelOemCommand)
	if ( specialCommand == NULL ||
		(specialCommand != NULL) && (*specialCommand != IntelOemCommand) )
	{
		printf("\n\tSpecial command not equal to %d",IntelOemCommand);
		printf("\n\tSee ASF specification for the Special Command Parameter legal values");
		printf("\n\n\t%d (No Special Command Parameter)\n>",-1);
		scanf("%u", &tmp);
	}
	// Special Command is 0xC1, hence Special Command Parameter
	// used to augment the Special Command
	else
	{
		printf("\n\t%d (No Special Command Parameter)",-1);
        printf("\n\t%d (Undefined Special Command Parameter)",
            UndefinedSpecialCommandParameter);
		printf("\n\t%u (UseIderFloppy)",UseIderFloppy);
		printf("\n\t%u (ReflashBios)",ReflashBios);
		printf("\n\t%u (BiosSetup)",BiosSetup);
		printf("\n\t%u (BiosPause)",BiosPause);
		printf("\n\t%u (UseIderCD)\n",UseIderCD);

		printf("\nYou can choose several options by using bitwise OR operation\n\n>");
		scanf("%u", &tmp);

		// verify specialCommandParameters value
		if ( (tmp != NO_VALUE) && (tmp & SpecialCommandParametersReservedBits) )
		{
			goto ILLEGAL_INPUT;
		}
	}

	if ( tmp == NO_VALUE )
	{
		specialCommandParameters = NULL;
	}
	else
	{
		// sanity check
		if ( specialCommandParameters == NULL )
		{
			specialCommandParameters = new uint16();
		}
		*specialCommandParameters = (uint16)tmp;
	}
		
	

	// Get Boot Options
	printf("\n\tBoot Options");
    printf("\n\t============");
	printf("\nPossible values:");

	printf("\n\t%d (No boot options)", -1);
	printf("\n\t%u (LockPowerButton)",LockPowerButton);
	printf("\n\t%u (LockResetButton)",LockResetButton);
	printf("\n\t%u (LockKeyboard)",LockKeyboard);
	printf("\n\t%u (LockSleepButton)",LockSleepButton);
	printf("\n\t%u (UserPasswordBypass)",UserPasswordBypass);
	printf("\n\t%u (ForceProgressEvents)",ForceProgressEvents);

    printf("\n\n\tFirmware Verbosity Options:");
    printf(  "\n\t---------------------------");
	printf("\n\t%u (FirmwareVerbositySystemDefault)",FirmwareVerbositySystemDefault);
	printf("\n\t%u (FirmwareVerbosityQuiet)",FirmwareVerbosityQuiet);
	printf("\n\t%u (FirmwareVerbosityVerbose)",FirmwareVerbosityVerbose);
	printf("\n\t%u (FirmwareVerbosityScreen)",FirmwareVerbosityScreen);
	printf("\n\n\t%u (ConfigurationDataReset)\n",ConfigurationDataReset);

	printf("\nYou can choose several options by using bitwise OR operation\n\n>");
	scanf("%u", &tmp);

	// verify bootOptions value
	if ( (tmp != NO_VALUE) && (tmp & BootOptionsReservedBits) )
	{
		goto ILLEGAL_INPUT;
	}
	else
	{
		if ( tmp == NO_VALUE )
		{
			bootOptions = NULL;
		}
		else
		{
			// sanity check
			if ( bootOptions == NULL )
			{
				bootOptions = new uint16();
			}
			*bootOptions = (uint16)tmp;
		}
	}
	return true;

	ILLEGAL_INPUT:
	printf("Error: %u is an illegal value. Aborting.\n", tmp);
	return false;
}

/*
 * Prints system capabilities supported by the Intel(R) AMT device
 * Arguments:
 *	systemCapabilitiesSupported	- set of flags that indicate the values
 *								the Intel(R) AMT device supports in the 
 *								Command parameter of the RemoteControl method
 */
void DisplaySystemCapabilities(uint8 systemCapabilitiesSupported)
{
	printf("\nSystemCapabilitiesSupported = %u", systemCapabilitiesSupported);

	if ( systemCapabilitiesSupported & SuppPowerCycleReset )
	{
		printf("\nPowerCycleReset ");
	}
	if ( systemCapabilitiesSupported & SuppPowerDown )
	{
		printf("\nPowerDown ");
	}
	if ( systemCapabilitiesSupported & SuppPowerUp )
	{
		printf("\nPowerUp ");
	}
	if ( systemCapabilitiesSupported & SuppReset )
	{
		printf("\nReset");
	}
}

/*
 * Prints special commands supported by the Intel(R) AMT device
 * Arguments:
 *	specialCommandsSupported	- set of flags that indicate the values
 *								the Intel(R) AMT device supports in the 
 *								SpecialCommand parameter of the 
 *								RemoteControl method
 */
void DisplaySpecialCommand(uint16 specialCommandsSupported)
{
	printf("\nSpecialCommandsSupported = %u", specialCommandsSupported);

	if ( specialCommandsSupported & SuppForcePXEBoot )
	{
		printf("\nForcePXEBoot ");
	}
	if ( specialCommandsSupported & SuppForceHardDriveBoot )
	{
		printf("\nForceHardDriveBoot ");
	}
	if ( specialCommandsSupported & SuppForceHardDriveSafeModeBoot )
	{
		printf("\nForceHardDriveSafeModeBoot ");
	}
	if ( specialCommandsSupported & SuppForceDiagnosticBoot )
	{
		printf("\nForceDiagnosticBoot ");
	}
	if ( specialCommandsSupported & SuppForceCDorDVDBoot )
	{
		printf("\nForceCDorDVDBoot");
	}
}


/*
 * Prints firmware capabilities supported by the Intel(R) AMT device
 * Arguments:
 *	systemCapabilitiesSupported	- set of flags that indicate the values
 *								the Intel(R) AMT device supports in the 
 *								BootOptions parameter of the RemoteControl 
 *								method
 */
void DisplaySystemFirmwareCapabilities(uint32 systemFirmwareCapabilities)
{
	printf("\nSystemFirmwareCapabilities = %u", systemFirmwareCapabilities);

	if ( systemFirmwareCapabilities & SuppVerbosityScreenBlank )
	{
		printf("\nVerbosityScreenBlank ");
	}
	if ( systemFirmwareCapabilities & SuppPowerButtonLock )
	{
		printf("\nPowerButtonLock ");
	}
	if ( systemFirmwareCapabilities & SuppResetButtonLock )
	{
		printf("\nResetButtonLock ");
	}
	if ( systemFirmwareCapabilities & SuppKeyboardLock )
	{
		printf("\nKeyboardLock ");
	}
	if ( systemFirmwareCapabilities & SuppSleepButtonLock )
	{
		printf("\nSleepButtonLock ");
	}
	if ( systemFirmwareCapabilities & SuppUserPasswordBypass )
	{
		printf("\nUserPasswordBypass ");
	}
	if ( systemFirmwareCapabilities & SuppForcedProgressEvents )
	{
		printf("\nForcedProgressEvents ");
	}
	if ( systemFirmwareCapabilities & SuppVerbosityVerbose )
	{
		printf("\nVerbosityVerbose ");
	}
	if ( systemFirmwareCapabilities & SuppVerbosityQuiet )
	{
		printf("\nVerbosityQuiet ");
	}
	if ( systemFirmwareCapabilities & SuppConfigurationDataReset )
	{
		printf("\nConfigurationDataReset");
	}
}


/*
 * Prints OEM defined capabilities supported by the Intel(R) AMT device
 * Arguments:
 *	systemCapabilitiesSupported	- set of flags that indicate the values
 *								the Intel(R) AMT device supports in the 
 *								OemParameters parameter of the RemoteControl 
 *								method
 */
void DisplayOemDefinedCapabilities(uint32 oemDefinedCapabilities)
{
	printf("\nOemDefinedCapabilities = %u", oemDefinedCapabilities);

	if ( oemDefinedCapabilities & SuppIDER )
	{
		printf("\nIDER");
	}
	if ( oemDefinedCapabilities & SuppSOL )
	{
		printf("\nSOL");
	}
	if ( oemDefinedCapabilities & SuppBiosReflash )
	{
		printf("\nBiosReflash");
	}
	if ( oemDefinedCapabilities & SuppBiosSetup )
	{
		printf("\nBiosSetup");
	}
	if ( oemDefinedCapabilities & SuppBiosPause )
	{
		printf("\nBiosPause");
	}
}

