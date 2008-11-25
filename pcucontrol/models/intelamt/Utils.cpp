//----------------------------------------------------------------------------
//
//  Copyright (C) Intel Corporation, 2004 - 2006.
//
//  File:       Utils.h
//
//  Contents:   Sample code for an Intel® AMT Network client.
//
//  Notes:      This file contains the function implementations 
//              used throughout the code of the all sample applications.
//
//----------------------------------------------------------------------------

#include <stdio.h> 
#include <string.h>
#include <stdlib.h>
#include "CommonDefinitions.h"

#ifdef _WIN32	
#define strncasecmp _strnicmp
#endif

// Constant definitions
static const char *URL_SEPARATOR = "://";
static const int NUM_OF_BYTES = 4;
static const int IP_BYTE_MASK = 0xFF;
static const int IP_BYTE_SHIFT = 0x8;

/*
 * Gets command line parameter that describes type of action to perform
 * Arguments:
 *	commandLineLength - number of the command line parameters
 *	argv - array of strings that holds command line parameters
 *	numOfArgs - minimal number of command line parameters
 *	option - pointer to the string that will hold command line
 *			 parameter that describes type of action to perform
 *	commandLine - pointer to the array of strings that will hold 
 *				  command line parameters without application name 
 *				  and parameter that describes type of action to perform
 * Return Value:
 *  true    - on success
 *  false   - on failure
 */
bool GetOption(int *commandLineLength, char *argv[], int numOfArgs,
			   char **option, char **commandLine[])
{
	if( !argv || 
		*commandLineLength < numOfArgs)
	{
		return false;
	}

	*option = NULL;
	*commandLine = &argv[1];
	// Skip the application name
	(*commandLineLength) --;

	if( argv[1][0] == '-')
	{
		if(strcmp(argv[1],CERT_NAME) && strcmp(argv[1],USER) && 
           strcmp(argv[1],VERBOSE)
#ifdef _WIN32
           && strcmp(argv[1],LOCAL)
#endif
           )
		{
			*option = argv[1];
			*commandLine = &argv[2];
            (*commandLineLength) --;
		}
	}
	
	return true;
}

#ifdef _WIN32
/*
 * Parses the user input text
 * Arguments:
 *  commandLineLength - number of arguments
 *  commandLine       - command line arguments received
 *  target   - pointer to the string that will hold the target url
 *  certName - pointer to the string that will hold client certificate's name 
 *  verbose - pointer to the verbose flag
 *  username - pointer to the string that will hold the username
 *  password - pointer to the string that will hold the password
 * Return Value:
 *  true    - on success
 *  false   - on failure
 */
bool ParseCommandLine(int commandLineLength,char* commandLine[],char **target,
					  char **certName, bool *local, bool *krb, bool *verbose,  
                      char **username, char **password)
{
#else
/*
 * Parses the user input text
 * Arguments:
 *  commandLineLength     - number of arguments
 *  commandLine     - command line arguments received
 *  target - pointer to the string that will hold the target url
 *  certName - pointer to the string that will hold client certificate's name*  
 *	certPass - pointer to the string that will hold passphrase for decryption
 *             the file that contains private key associated with the given
 *             client certificate
 *  verbose - pointer to the verbose flag
 *  username - pointer to the string that will hold the username
 *  password - pointer to the string that will hold the password
 * Return Value:
 *  true    - on success
 *  false   - on failure
 */
bool ParseCommandLine(int commandLineLength,char* commandLine[],char **target, 
					  char **certName,char **certPass, bool *verbose, 
					  char **username, char **password)
{
	*certPass = NULL;
#endif
	*certName = NULL;
	*target = NULL;
	*password = NULL;
	*username = NULL;

	if (verbose != NULL) {
		*verbose = false;
	}

	for(int i = 0; i < commandLineLength; i++)
    {		
        if( !strcmp(commandLine[i], CERT_NAME) )
        {
            if( i+1 < commandLineLength && ! *certName )
            {
                *certName = commandLine[++i];
            }
            else
            {
                return false;
            }
        }
#ifndef _WIN32
		else if( !strcmp(commandLine[i], CERT_PASS) )
		{
			if( i+1 < commandLineLength && ! *certPass )
			{
				*certPass = commandLine[++i];
			}
			else
			{
				return false;
			}
		}
#endif
		else if( !strcmp(commandLine[i], VERBOSE) && verbose != NULL)
		{
			*verbose = true;
		}
#ifdef _WIN32
        else if( !strcmp(commandLine[i], LOCAL) && local != NULL)
		{
			*local = true;
		}
#endif
		else if( !strcmp(commandLine[i], USER) )
		{
        
			if( i+1 < commandLineLength && ! *username )
			{
				*username = commandLine[++i];
			}
			else
			{
				return false;
			}
		}
		else if( !strcmp(commandLine[i], PASS) )
		{
         
			if( i+1 < commandLineLength && ! *password )
			{
				*password = commandLine[++i];
			}
			else
			{
				return false;
			}
		}
		else
		{
			//this is a target URL argument
			if( !ValidateIP(commandLine[i]) )
			{
				return false;
			}
			*target = commandLine[i];
		}
	}
	if( !*target || (!strncasecmp(*target, "http:", 5) && *certName != 0 ))
	{
		return false;
	}
	if( (*username && !*password) || (!*username && *password)) 
	{
		return false;
	}
#ifdef _WIN32
	else if(*username && *password)
	{
		*krb = false;
	}
#else
	else if(!*username)
	{
		return false;
	}
#endif
	return true;
}

/*
 * Checks if IP address exists in the URI
 * Arguments:
 *  uri - pointer to the string that represents the URI
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool ValidateIP(const char *uri)
{
	if( strncasecmp(uri, "http:", 5 ) && strncasecmp(uri, "https:", 6 ) )
	{
		return false;
	}
    bool retVal = true;
    
    // pointer to the start of the IP address
    const char *start = strstr(uri,URL_SEPARATOR);
    if(start != NULL)
    {
        start += (sizeof(URL_SEPARATOR) - 1);

        // pointer to the end of the IP address
        const char *end = strchr(start,':');

        if(end != NULL && start != end)
        {
            retVal = true;
        }
        else
        {
            retVal = false;
        }
    }
    else
    {
        retVal = false;
    }

    return retVal;
}

/*
 * Gets an input string from the user
 * Assumptions: caller pre-allocates string, and user must not overflow (!)
 * Arguments:
 *  msg         - message string
 *  s           - pre-allocated input string that will represent the binary data
 *  hidden      - echo input string (true / false)
 */
void GetString(char *msg, char *s, bool hidden)
{

	// Output informative message
	if(msg != NULL)
	{
		printf ("%s", msg);
	}
	fflush(NULL);

#ifdef _WIN32
	char c; // for the next input character
	int count = 0; // number of characters

	// Get input string character by character
	do 
	{
		c = _getch();

		count ++;

		if (c == '\r' || // carriage return
			c == '\n' || // new line
			c == '\t' || // TAB
			count == MAX_LINE_LEN ) // maximal line length
		{
			*s=0;
			break;
		}
		else if ( c==3 ) // <CTRL> + C
		{
			exit(0);
		}
        else if ( c == '\b' ) // backspace
        {
			count --;
			if(count > 0)
			{
				printf("%c", c);
				printf("%c", ' ');
				printf("%c", c);
				count --;
				s --;
			}
            continue;
        }

		// The password should be hidden
		if ( hidden )
		{
			printf("*");
		}
		else
		{
			printf("%c", c);
		}
		*s = c;
		s++;
	}
	while ( true );
	printf("\n");
#else

	if(hidden == false)
	{
		if(fgets(s,MAX_LINE_LEN,stdin))
		{
			char *tmp = strchr(s,'\n');
			if(tmp != NULL)
			{
				*tmp = '\0';
			}
		}
	}
	else
	{
		strcpy(s,getpass(""));
	}
#endif
}

/*
 * Receives yes or no answer from the user.
 * Arguments:
 *	msg	- pointer to the string that holds a question
 * Return value:
 *  true    - if answer is 'y' (yes)
 *  false   - otherwise
 */
bool DisplayWarning(const char *msg)
{
    printf("%s",msg);
    char c;
    scanf("%c",&c);
    
	if(c != 'y' && c != 'n')
	{
		printf("Illegal choice. Aborting.\n");
		return false;
	}
	else if(c == 'n')
	{
		return false;
	}
    scanf("%c",&c);

    return true;
}

/*
 * Gets a number from the user
 * Arguments:
 *  number - pointer to the variable that will be hold a number
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool GetNumber(int *number)
{
    scanf("%d",number);
    int c = getchar();
	if(c != '\n' && c != '\r')
	{
		return false;
	}
    return true;
}

/*
 * Checks the exit status of the SOAP query
 * Arguments:
 *  res	- exit statis of the gSOAP function call 
 *  status	- status codes that are returned by 
 *				Intel(R) AMT network API
 *  message	- string that holds the function name
 * Return value:
 *	true - if the query succeed
 *	false - if the query failed
 */
bool CheckReturnStatus(unsigned int res, unsigned long status, 
					   const char *message)
{
	if (res || status)
	{
		printf("\nError: failed while calling %s\n", message);
		if(res == 0)
		{
#ifndef _WIN32
            printf("Status = %lu\n", status);
#else
            wchar_t err[MAX_LINE_LEN];
            GetStatusString(status,err,MAX_LINE_LEN);
            wprintf(err);
            printf("\n");
#endif
		}
		else
		{
            printf("SOAP failure: error code = %u\n", res);
		}
		return false;
	}
	return true;
}

/*
 * Changes the service name at the URI
 * Arguments:
 *	uri	- null-terminated string which holds the whole URI as supplied 
 *		  at the command line
 *  newService	- string which represents the new service name
 *  newUri	- pre-allocated string which will hold the new service URI
 */
bool ChangeService(const char *uri, const char *newService, char *newUri)
{
    const char *tmp = strrchr(uri,'/');
    if(tmp == NULL)
    {
       return false;
    }

    int n = tmp - uri + 1;
    
    strncpy(newUri,uri,n);
    newUri[strlen(uri) - strlen(tmp) + 1] = '\0';
	//check new Uri allocated 
    if(&(newUri[n]) == NULL)
    {
        return false;
    }
    //copy newService to end of string instead '\o' 
    strcpy(&(newUri[n]),newService);
 
    return true;
}

/*
 * Replaces substring within given string
 * Arguments:
 *	oldString	- pointer to the old null-terminated string
 *  oldSubstr	- substring that will be replaced
 *  newSubstr	- string which represents the new substring
 *  newString	- pre-allocated buffer which will hold the new string
 */
void ReplaceSubstring(const char *oldString,const char *oldSubstr, 
					const char *newSubstr, char *newString)
{
	// Locate substring
	const char *tmp = strstr(oldString,oldSubstr);

	if(tmp == NULL)
	{
		printf("Error: cannot find '%s' within '%s'\n",oldSubstr,oldString);
		exit(1);
	}

	int len1 = strlen(oldSubstr);
	int len2 = strlen(newSubstr);
	int i,k,j;

	// Copy string to the buffer with appropriate change
	for(i = 0, k = 0; oldString[i] != '\0'; i ++, k ++)
	{
		if(tmp == &oldString[i])
		{
			for(j = 0; j < len2; k ++, j ++)
			{
				newString[k] = newSubstr[j];
			}
			i += len1;
		}
		newString[k] = oldString[i];
	}
	newString[k] = oldString[i];
}

/*
 * Converts the IP address from the dot-separated format
 * to the usigned long number
 * Arguments:
 *  address	- number that will hold a converted IP address 
 *  bytes	- array for IP address's bytes
 */
void SetIPAddress(unsigned long &address, unsigned long bytes[])
{
	address = 0;
	int i;
	for(i = 0; i < NUM_OF_BYTES - 1; i ++)
	{
		address += bytes[i];
		address <<= 8;
	}
	address += bytes[i];
}

/*
 * Extracts bytes from the IP address for the dot-separated representation
 * Arguments:
 *  address	- number that holds a IP address 
 *  bytes	- array that will hold IP address bytes
 */
void NumberToIP(unsigned long address, unsigned long bytes[])
{
	int i;
	for(i = NUM_OF_BYTES - 1; i > 0; i --)
	{
		bytes[i] = address & IP_BYTE_MASK;
		address >>= IP_BYTE_SHIFT;
	}
	bytes[i] = address & IP_BYTE_MASK;
}


/*
 * Converts a number to a string
 * Arguments & Return values:
 *	number	- number which will convert
 *	string	- string which will hold the converted number
 */
void NumberToString(unsigned long number, char *string)
{
	div_t res;
	int i = 0;
	char tmp[MAX_LINE_LEN];
	do
	{
		res = div(number,10);
		tmp[i++] = (char)('0' + res.rem);
		number = res.quot;
	}while(number != 0);

	for(i --; i >= 0; i --)
	{
		*string = tmp[i];
		string ++;
	}
	*string = '\0';
}

/*
 * Converts the IP address to the dot-separated string form
 * Arguments & Return values:
 *	address	- number which holds the IP address
 *	string	- string which will represent the IP address in
 *			  the dot-separated format
 */
void IpToString(unsigned long address, char *string)
{
	unsigned long bytes[NUM_OF_BYTES];
	NumberToIP(address,bytes);//one,two,three,four);

	char tmp[MAX_LINE_LEN];
	char *ptr = string;

	for(int i = 0; i < NUM_OF_BYTES; i ++)
	{
		NumberToString(bytes[i],tmp);
		strcpy(ptr,tmp);
		ptr += strlen(tmp);
		*ptr = '.';
		ptr ++;
	}
	ptr --;
	*ptr = '\0';	
}

/*
 * Converts the string that represents dot-separated 
 * format of the IP address to the number
 * Arguments:
 *	string	- string which represents IP address in
 *			  the dot-separated format
 *	address	- number which will hold the converted IP address
 */
void StringToIP(const char *string, unsigned long &address)
{
	// local copy of the string
	char tmpStr[MAX_LINE_LEN];
	strncpy(tmpStr,string,MAX_LINE_LEN - 1);
	tmpStr[MAX_LINE_LEN - 1] = '\0';

	char *tmpPtr1 = NULL;
	char *tmpPtr2 = tmpStr;
	unsigned long bytes[NUM_OF_BYTES];
	int i; 

	for(i = 0; i < NUM_OF_BYTES - 1; i ++)
	{
		if((tmpPtr1 = strstr(tmpPtr2,".")) == NULL)
		{
			goto FAULT_EXIT;
		}

		*tmpPtr1 = '\0';
		bytes[i] = atol(tmpPtr2);
		tmpPtr2 = tmpPtr1 + 1;
	}
	bytes[i] = atol(tmpPtr2);

	SetIPAddress(address,bytes);//one,two,three,four);

	return;

	FAULT_EXIT:
	printf("Error: invalid format\n");
	exit(1);
}

/* 
 * Converts the bunary guid to a string according to the representation
 * described in the CDE 1.1 RPC specification
 * Arguments & Return values:
 *	guid	- a pointer to the 16 byte guid
 *	string	- string which will hold the guid string
 */
void GuidToString(const unsigned char* guid, char* string)
{	   
	if(guid != NULL && string != NULL)
	{
		int j = sprintf(string, "%02X%02X%02X%02X", guid[3], guid[2], guid[1], guid[0]);
		j += sprintf(string + j, "-%02X%02X", guid[5], guid[4]);
		j += sprintf(string + j, "-%02X%02X", guid[7], guid[6]);
		j += sprintf(string + j, "-%02X%02X-", guid[8], guid[9]);		
		for(int i = 10; i <= 15; i ++)
		{
			j += sprintf(string + j, "%02X", guid[i]);
		}
	}
}

/*
 * Extracts IP address from the URI
 * Arguments:
 *  uri - pointer to the string that represents the URI
 * Return value:
 *  true  - on success
 *  false - on failure
 */
bool ExtractIPFromUri(const char *uri, char *baseUrl)
{
    char *ip = baseUrl;
    bool retVal = true;
    
    // pointer to the start of the IP address
    const char *start = strstr(uri,URL_SEPARATOR);
    if(start != NULL)
    {
        start += (sizeof(URL_SEPARATOR) - 1);

        // pointer to the end of the IP address
        const char *end = strchr(start,':');

        if(end != NULL && start != end)
        {
            while(start != end)
            {
                *ip = *start;
                ip ++;
                start ++;
            }
			*ip = '\0'; // NULL termination
        }
        else
        {
            retVal = false;
        }
    }
    else
    {
        retVal = false;
    }

    return retVal;
}

/* 
 * prints "success" to output
 * Argument: 
 *  printS - prints only if true
 */
void PrintSuccess(bool printS)
{	
	if(printS)
	{
		printf("success\n");
	}
}

/* 
 * prints function call to output
 * Argument: 
 *  message - name of function
 */
void FunctionCall(const char *message)
{
	printf("\nCalling function %s...   ", message);
}

/*
 * Performs testing of the URL
 * Arguments:
 *	targetUrl - string that represents URL of the target machine
 *	isEmulator - pointer to the variable that will be 1 if the targetUrl 
 *				 points to the Intel® AMT device or 0 if the targetUrl
 *				 points to the Intel® AMT Emulator
 */
void IsEmulator(const char *targetUrl, int *isEmulator)
{
	*isEmulator = 1;

	if((strstr(targetUrl,".asmx")) == (targetUrl + strlen(targetUrl) - 5))
	{
		*isEmulator = 0;
	}
}

/*
 * Prints notes for usage by authentication options
 */
void PrintAuthenticationNote()
{
#ifndef _WIN32
    printf("\t %s <username> %s <password>: for digest authentication.\n",USER,PASS);
#else
	printf("\n\t If %s <username> %s <password> are defined the Digest authentication" ,USER,PASS);
	printf(" scheme is used,\n\t otherwise the Kerberos authentication scheme will be attempted.\n");
#endif
    printf("\nClient authentication options (TLS Mutual Authentication mode only):\n");
#ifndef _WIN32
    printf("\t %s: If option defined <name> specify the full path of the ",
        CERT_NAME);
    printf("file containing client certificate and private keys.\n");
    printf("\t %s: If option defined <pass> specify the passphrase ",
        CERT_PASS);
    printf("that protects the private key. ");
#else
	printf("\t %s: If option defined, <name> specifies the client certificate's",
        CERT_NAME);
    printf(" Common Name (CN).\n");
     
	printf("\t\t    If option is not specified the sample application will search the certificate store \n");
	printf("\t\t    for a client certificate matching Intel(R) AMT requirements.  \n");
	printf("\t\t    The first one found will be used for authentication.\n");
#endif
}

