# Generate Decode re's from scanner manual

import re

cmdre = re.compile(r'([^,]*)')
sub1 = re.compile(r'\[')
sub2 = re.compile(r'\]')

model = '''
		b'{CMD}': {{	# {CMD}
			'recmd': rb'{RE}',
		}},
'''

print('model=', model)

while True:
	codestring = input('Enter scanner codestring from reference:')
	if len(codestring) == 0: break
	
	cmdmatch = cmdre.match(codestring)
	
	if cmdmatch is None:
		print('No command match')
		continue
		
	cmd = cmdmatch.group(1)
	
	new1 = sub1.sub(r'(?P<', codestring)
	new1 = sub2.sub(r'>[^,]*)', new1)
#	print(new1)
	
	print(model.format(CMD=cmd, RE=new1))
	