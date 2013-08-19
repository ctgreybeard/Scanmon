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

$PortObj->alias("scanner");
$PortObj->baudrate(115200);
$PortObj->parity("none");
$PortObj->handshake("none");
$PortObj->databits(8);
$PortObj->stopbits(1); 
$PortObj->is_stty_eol($EOL);

$PortObj->are_match($EOLC);

$PortObj->write_settings;

# Save the current settings

$PortObj->save($ConfigurationFileName)
   || warn "Can't save $ConfigurationFileName: $!\n";

my $output_string = "$Cmd\r";
my $count_out = $PortObj->write($output_string);
	warn "write failed\n"         unless ($count_out);
	warn "write incomplete\n"     if ( $count_out != length($output_string) );

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
