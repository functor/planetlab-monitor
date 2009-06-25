# Any configuration directives you include  here will override
# RT's default configuration file, RT_Config.pm

#Site Configurations

#Name of the site
Set($rtname, 'PLC_NAME');

#Site's Organization
Set($Organization , 'PLC_RT_HOSTNAME');

#Main email address for contacting the Support Team
Set($CorrespondAddress , 'support@PLC_RT_HOSTNAME');

#Default destination email address for replies
Set($CommentAddress , 'root@PLC_RT_HOSTNAME');

#System administrator mail address
Set($OwnerEmail , 'root@PLC_RT_HOSTNAME');

#Maximum attachment size
Set($MaxAttachmentSize , 10000000);

#Database configurations

#Type of database: Postgresql
Set($DatabaseType , 'Pg'); # e.g. Pg or mysql

#The name of the database user (inside the database)
Set($DatabaseUser , 'RT_DB_USER');

#Password the DatabaseUser should use to access the database
Set($DatabasePassword , 'RT_DB_PASSWORD');

#The name of the RT's database on your database server
Set($DatabaseName , 'RT_DB_NAME');

#Database host
Set($DatabaseHost , 'localhost');

#RT's Database host
Set($DatabaseRTHost , 'localhost');

#Webserver paramters

#Web path, such as https://rt.domain/web_path
Set($WebPath , "/rt3"); # e.g. Set($WebPath , "");

#URL
Set($WebBaseURL , "https://PLC_RT_HOSTNAME"); # Set($WebBaseURL , "http://rt.PLC_RT_HOSTNAME");

#Adding plugins
#Set(@Plugins,qw(RT::FM));

#Tuning Up the RT Config

#Log File
Set($LogToFile , 'debug');
Set($LogDir, '/var/log/rt3/');
#rt_debug.log should be created and set to the correct owner(apache ownerand group)/permissions (-rw-r--r--)Set($LogToFileNamed , "rt_debug.log");

#Notify requestor: True (1)
Set($NotifyActor, 1);

#Send a copy to RT owner: True
Set($LoopsToRTOwner , 1);

# Try to figure out CC watchers 
Set($ParseNewMessageForTicketCcs , 1);

# pattern to self-identify to avoid loops to itself.
Set($RTAddressRegexp , '^(support|monitor|legal|security)@PLC_RT_HOSTNAME$');

Set($WebImagesURL , $WebPath . "/NoAuth/images/");  # need this for below 
Set($LogoURL, "/misc/logo.gif"); 
Set($LogoLinkURL, 'http://PLC_WWW_HOSTNAME'); 
Set($LogoImageURL, "http://PLC_RT_HOSTNAME/misc/logo.gif"); 
Set($LogoAltText, "PLC_NAME");

1;
