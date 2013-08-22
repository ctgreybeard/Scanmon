#!/sw/bin/perl 

use strict;
use warnings;

use Device::SerialPort;
use Getopt::Long;

my $PortName = 'none';
my $PortObj;
my $Cmd = "MD";
my $ConfigurationFileName = "serialconfig.cfg";
my $EOLC = "\r";
my $EOL  = ord($EOLC);

my %options = (
	'port:s' => \$PortName,
	'cmd:s'  => \$Cmd,
	);

GetOptions(%options) or die "Invalid options: $!\n";

$PortObj = new Device::SerialPort ($PortName, 0)
   || die "Can't open $PortName: $!\n";
$PortObj->debug(1);

$PortObj->alias("scanner");
$PortObj->baudrate(19200) if $PortObj->can_baud;
$PortObj->handshake("none") if $PortObj->can_handshake;
$PortObj->databits(8) if $PortObj->can_databits;
$PortObj->stopbits(1) if $PortObj->can_stopbits; 
$PortObj->is_stty_eol($EOL);

$PortObj->are_match($EOLC);

$PortObj->write_settings || die "Can't write settings to $PortName\n";

printf "Serial Port can_rtscts: %s\n", $PortObj->can_rtscts ? "Yes" : "No";
printf "Serial Port can_handshake: %s\n", $PortObj->can_handshake ? "Yes: " . join(", ", $PortObj->handshake) : "No";
printf "Serial Port can_status: %s\n", $PortObj->can_status ? "Yes" : "No";
printf "Serial Port can_write_done: %s\n", $PortObj->can_write_done ? "Yes" : "No";
#printf "Serial Port can_write_drain: %s\n", $PortObj->can_write_drain ? "Yes" : "No";

# Save the current settings

$PortObj->save($ConfigurationFileName)
   || warn "Can't save $ConfigurationFileName: $!\n";

sleep(2); # Wait a bit
$PortObj->purge_rx;
$PortObj->purge_tx;
sleep(2); # Wait a bit more

my $output_string = "$Cmd$EOLC";
#$PortObj->purge_all;
#$PortObj->write_drain;
printf "Writing command \"%s\" to scanner\n", $Cmd;
my $count_out = $PortObj->write($output_string);
	warn "write failed\n"         unless ($count_out);
	warn "write incomplete\n"     if ( $count_out != length($output_string) );
#$PortObj->write_drain;

# Read the response ...
#my $gotit = "";
#until ("" ne $gotit) {
#	$gotit = $PortObj->lookfor;       # poll until data ready
#	die "Aborted without match\n" unless (defined $gotit);
#	sleep 1;                          # polling sample time
#}
#
#printf "gotit = %s\n", $gotit;                # input BEFORE the match

my $STALL_DEFAULT=10; # how many seconds to wait for new input
 
 my $timeout=$STALL_DEFAULT;
 
 $PortObj->read_char_time(0);     # don't wait for each character
 $PortObj->read_const_time(1000); # 1 second per unfulfilled "read" call
 
 my $chars=0;
 my $buffer="";
 while ($timeout>0) {
        my ($count,$saw)=$PortObj->read(255); # will read _up to_ 255 chars
        if ($count > 0) {
                $chars+=$count;
                $buffer.=$saw;
 
				last if ($buffer =~ m/$EOLC/);
		} else {
                $timeout--;
        }
 }

 if ($timeout==0) {
        warn "Waited $STALL_DEFAULT seconds and never saw what I wanted\n";
 }

printf "Read: %s\n", $chars ? $buffer : "nothing";

$PortObj->close || die "failed to close";
	undef $PortObj;                               # frees memory back to perl
