# Generate Decode re's from scanner manual

import re, fileinput

cmdre = re.compile(r'([^,]*)')
sub1 = re.compile(r'\[')
sub2 = re.compile(r'\]')
brkre = re.compile('/')

model = '''
		b'{CMD}': {{	# {CMD}
			'recmd': rb'{RE}',
		}},
'''

for codestring in fileinput.input():

	if codestring.endswith('\n'): codestring = codestring[:-1]	# chomp
	
	cmdmatch = cmdre.match(codestring)
	
	if cmdmatch is None:
		print('No command match for:', codestring)
		continue
		
	cmd = cmdmatch.group(1)
	
	new1 = sub1.sub(r'(?P<', codestring)
	new1 = sub2.sub(r'>[^,]*)', new1)
	if new1.find('/') >= 0:	# Found a break, wrap it in an optional string
		new1 = brkre.sub('(:?', new1)	# Group these but don't remember them
		new1 += ')?'					# This group is optional		
	
	print(model.format(CMD=cmd, RE=new1))
	