This is a VERY fledgeling project! It is NOT useful yet! Please don't complain if it DOESN'T WORK!

BUT! If you are interested, what I am working on is getting control of my
brand new Uniden Bearcat BCD996XT scanner under Mac OSX.

I was appalled that there was no OSX version of any scanner programming/control
programs. It seemed "reasonable" that the commercial guys didn't offer OSX versions
but Freescan, which is a GREAT program, only has a Windoze version.  I hate running that
O/S just to program my scanner.

So, thinks I, why not write your own?

So I tried Perl, my go-to language and couldn't get it to work reliably for even
the most basic things.  Device::Serialport was not working correctly through the USB-Serial 
PL2303 apparently. And I wasn't going to go down that rat-hole to figure out who or where the fault
was.

So I noticed that Python had serial support and, although I'm not a "Python programmer" 
I figured I'd take a shot with that. I've been programming since 1965 (really!) so I figured
yet another language couldn't be that hard.

So, here we are. the current state is VERY particular to my own system! I'm an incremental
programmer so be warned. I program first in specifics and expand into generalities. This can
take MANY iterations! What you see is a Work In Progress. 
