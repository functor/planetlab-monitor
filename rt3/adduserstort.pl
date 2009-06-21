#!/usr/bin/perl -w
#
# rtadduser: Batch add local users to RT based on a csv file named users_data.csv located # in the same directory
# Mohamed El Erian <mohamed.elerian@britishcouncil.org.eg,melerian@gmail.com>
# Partly based on script provided by David Maze <dmaze@cag.lcs.mit.edu>
# File format is username,realname,email_address,organization,address1,city,country
# $Id$
#

use lib "/usr/lib";
use strict;
use English;
use RT::Interface::CLI qw(CleanEnv);
use RT::User;

CleanEnv();
RT::LoadConfig();
RT::Init();
my @raw_data;
my $bc_user = '';
my $username = '';
my $realname = '';
my $email_address = '';
my $organization = '';
my $address1 = '';
my $city = '';
my $country = '';

open(USERS_DATA, "./users_data.csv") || die("Could not open file!");
@raw_data=<USERS_DATA>;
close(USERS_DATA);
foreach $bc_user (@raw_data)
{
 chop($bc_user);
 ($email_address,$realname,$organization)=split(/\,/,$bc_user);

  my $UserObj = new RT::User(RT::SystemUser);
  $UserObj->Create(Name => $email_address,
             RealName => $realname,
             EmailAddress => $email_address,
             Password => 'Passw0rd',
             Organization => $organization,
             Privileged => 1);
             #Address1 => $address1,
             #City => $city,
             #Country => country,
}


