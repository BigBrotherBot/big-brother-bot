#!/usr/bin/python
#
# nbcalc is a netblock calculator: you give it netblocks or facsimiles
# thereof, it adds (or subtracts) them together, and finishes off by
# spitting out the resulting netblock(s) in CIDR format. If it is given
# no arguments it reads standard input.
#
# The simple usage is:
#	nbcalc START - END
#	nbcalc IPARG [IPARG ...]
#
# where IPARG is one of IPADDR, START-END, or CIDR. (I am not going to
# try to define a CIDR here, except to say that the CIDR must be proper
# and that both '127/8' and '127.0.0.1/8' are allowed.)
#
# The full 'calculator mode' intermixes '+' and '-' arguments in the
# IPARGs. '+' means 'start adding IPARGs to the IP address range being
# accumulated', '-' means 'start removing IPARGs from the IP address
# range being accumulated'.
# Eg:
#	nbcalc.py 127/8 - 127/16 + 127.0.0.0/24 + 127.0.6.0/24

import sys

# look ma, netblock caculations:
from b3.plugins.netblocker.netblock import netblock


def die(str):
	sys.stderr.write(sys.argv[0] + ': ' + str + '\n')
	sys.exit(1)
def warn(str):
	sys.stderr.write(sys.argv[0] + ': ' + str + '\n')

def dumpout(r):
	res = r.tocidr()
	if len(res) > 0:
		print "\n".join(res)

def process(args):
	r = netblock.IPRanges()

	# people's republic of glorious special cases.
	if len(args) == 3 and args[1] == "-":
		process(["%s-%s" % (args[0], args[2]),])
		return

	# We permit the rarely used calculator mode.
	opd = r.add
	for a in args:
		op = opd
		# Are we changing the operation?
		if a == "-":
			opd = r.remove
			continue
		elif a == "+":
			opd = r.add
			continue
		# We might be asking for a one-shot subtraction.
		if a[0] == '-':
			op = r.remove
			a = a[1:]
		# We notice bad input by the errors that netblock throws.
		try:
			op(a)
		except netblock.BadCIDRError as e:
			# Because this happens SO OFTEN, give a specific
			# message.
			c = netblock.convcidr(a, 0)
			die("bad CIDR %s. Should start at IP %s" % \
			    (a, netblock.ipstr(c[0])))
		except netblock.NBError as e:
			die("bad argument %s: %s" % (a, str(e)))
	dumpout(r)

def maybestdin(args):
	if len(args) == 0:
		process([x.strip() for x in sys.stdin.readlines()])
	else:
		process(args)

#import profile
if __name__ == "__main__":
	#profile.run('process(sys.argv[1:])')
	maybestdin(sys.argv[1:])
