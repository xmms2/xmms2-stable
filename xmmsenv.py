import SCons

import os;
import sys;



class XmmsEnvironment(SCons.Environment.Environment):
	pass
	def __init__(self, options=None, **kw):
		self.sys = os.popen("uname").read().strip()
		SCons.Environment.Environment.__init__(self, options=options)
		self.flag_groups = {}
		apply(self.Replace, (), kw)
		self.install_prefix=self['PREFIX']
		self.pluginpath=self.install_prefix + "/lib/xmms/"
		self.binpath=self.install_prefix + "/bin/"
		self.libpath=self.install_prefix + "/lib/"
		self.sysconfdir=self['SYSCONFDIR']
		self.installdir=self['INSTALLDIR']
		self.mandir=self['MANDIR']
		self.Append(CPPPATH=['#src/include'])
		self['ENV']['TERM']=os.environ['TERM']
		self.Append(CPPFLAGS=['-DPKGLIBDIR=\\"'+self.pluginpath+'\\"'])
		self.Append(CPPFLAGS=['-DSYSCONFDIR=\\"'+self.sysconfdir+'\\"'])

	def XmmsConfig(self,source):
		self.Install(self.installdir+self.sysconfdir, source)

	def XmmsManual(self,source):
		self.Install(self.installdir+self.mandir, source)

	def XmmsPlugin(self,target,source):
		if self.sys == 'Darwin':
			self['SHLINKFLAGS'] = '$LINKFLAGS -bundle -flat_namespace -undefined suppress'
			self['SHLIBSUFFIX'] = '.so'
		self.SharedLibrary(target, source)
		self.Install(self.installdir+self.pluginpath,self['LIBPREFIX']+target+self['SHLIBSUFFIX'])

	def XmmsProgram(self,target,source):
		self.Program(target,source)
		self.Install(self.installdir+self.binpath,target)

	def XmmsLibrary(self,target,source):
		if self.sys == 'Darwin':
			self['SHLINKFLAGS'] = '$LINKFLAGS -dynamiclib'
			self['SHLIBSUFFIX'] = '.dylib'
		self.SharedLibrary(target, source)
		self.Install(self.installdir+self.libpath, self['LIBPREFIX']+target+self['SHLIBSUFFIX'])

	def AddFlagsToGroup(self, group, flags):
		if self.flag_groups.has_key(group) :
			self.flag_groups[group] += flags
		else:
			self.flag_groups[group] = flags

	def HasGroup(self,group):
		return self.flag_groups.has_key(group)

	def CheckAndAddFlagsToGroup(self, group, cmd, fail=0):
		res = os.popen(cmd).read().strip()
		if res == "":
			if fail != 0:
				print "Could not find "+group+". Aborting!"
				sys.exit(1)
			return 0
		self.AddFlagsToGroup(group, res)
		return 1

	def AddFlagsFromGroup(self, group):
		self.ParseConfigFlagsString(self.flag_groups[group])

	def CheckLibAndAddFlagsToGroup(self, group, library, function, depends=""):
		test_env = self.Copy()
		if depends != "":
			if not self.HasGroup(depends):
				return 0
			test_env.AddFlagsFromGroup(depends)

		my_conf = SCons.SConf.SConf( test_env )
		if my_conf.CheckLib(library, function, 0):
			self.AddFlagsToGroup(group, '-l'+library)
			my_conf.Finish()
			return 1
		my_conf.Finish()
		return 0

	def ParseConfigFlagsString(self, flags ):
		"""We want our own ParseConfig, that supports some more
		flags, and that takes the argument as a string"""

		params = self.Split(flags)
		i = 0
		while( i < len( params ) ):
			arg = params[i]
			switch = arg[0:1]
			opt = arg[1:2]

			if switch == '-':
				if opt == 'L':
					self.Append( LIBPATH = [ arg[2:] ] )
	    			elif opt == 'l':
					self.Append( LIBS = [ arg[2:] ] )
		    		elif opt == 'I':
					self.Append( CPPPATH = [ arg[2:] ] )
		    		elif opt == 'D':
					self.Append( CPPFLAGS = [ arg ] )
	    			elif arg[1:] == 'pthread':
					self.Append( LINKFLAGS = [ arg ] )
					self.Append( CPPFLAGS = [ arg ] )
	    			elif arg[1:4] == 'Wl,':
					self.Append( LINKFLAGS = [ arg ] )
				elif arg[1:] == 'framework':
					self.Append( LINKFLAGS = [ arg ] )
					self.Append( LINKFLAGS = [ params[i+1] ] )
					i = i + 1
				elif arg[1:5] == 'arch':
					i = i + 1
		    		else:
					print 'garbage in flags: ' + arg
					sys.exit(1)
			elif switch == '/':
				if arg[-3:] == '.la':
# Ok, this is a libtool file, someday maybe we should parse it.
# Hate this shit. This is the reason we switch from autobajs.
# Please do the same!
					print "I have found some autobajs in " + arg + ". I'm just guessing here."
					self.Append( LINKFLAGS = [ arg[:-3] + '.a' ] )
			else:
				print 'garbage error: ' + arg

			i = i + 1

