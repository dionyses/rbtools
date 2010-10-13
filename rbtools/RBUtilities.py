import cookielib
import difflib
import marshal
import mimetools
import ntpath
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import urllib
import urllib2
from optparse import OptionParser
from tempfile import mkstemp
from urlparse import urljoin, urlparse

class RBUtilities:
	"""
	
	A Utility class that performs such tasks as finding out environment information, making system calls, and raising
	warnings and errors
	
	"""

	ERR_NO = 1

	log_file = None

	def __init__( self, log_file = 'rbproblems.log' ):
		"""__init__( self, log_file )
		
		Initializes the utility class
		
		Parameters:
			log_file, the file warnings and errors are logged in. set to None to prevent logging. DEFAULTS: 'rbproblems.log'
			
		"""
		
		self.log_file = log_file
		
	def get_repository( self, url = None, repo_types = ['svn', 'cvs', 'git', 'hg', 'perforce', 'clearcase'], additional_repos = []):
		"""get_repository( self, url, repo_types, additional_repos )
		
		Finds the correct type of Repository and returns it.
		
		Parameters:
			url, the url of the server. Defaults to None, but is required
			repo_types, types of repo this function would test. It builds
					the objects, passing them the url as a parameter. Defaults
					to trying svn, cvs, git, mercurial, perforce and clearcase
			additional_repos, a list of additional Repository objects (already
					created) to try (they will be tried first). This is separated
					from repo_types because repo_types autoinitializes the
					Repository objects, which it couldn't do for types it
					doesn't know. Defaults to []
		
		Returns a Repository object of the correct type or None, if none are found
											
		"""
		
		if not url:
			raise_error( "missingRequiredParameter", "get_repository requires url to be passed as a parameter")
	
		possible_repos = additional_repos
	
		for type in repo_types:
			type = type.lower()
		
			if type == 'svn':
				possible_repos.add( SVNRepo( url ) )
			elif type = 'cvs':
				possible_repos.add( CVSRepo( url ) )
			elif type = 'git':
				possible_repos.add( GitRepo( url ) )
			elif type = 'hg' or type = 'mercurial':
				possible_repos.add( MercurialRepo( url ) )
			elif type = 'perforce':
				possible_repos.add( PerforceRepo( url ) )
			elif type = 'clearcase' or type = 'clear case':
				possible_repos.add( ClearCaseRepo( url ) )
			else
				raise_warning( "UnreckognizedType", type + "is not a recognized type. If it is a Repository type, create it yourself and pass it in using additional_repos" )
		
		repo = None
		
		for rep in possible_repos:
			if rep.get_info()
				repo = rep
				break
			
		return repo
	
	def make_tempfile():
		"""
		Creates a temporary file and returns the path. The path is stored
		in an array for later cleanup.
		"""
		fd, tmpfile = mkstemp()
		os.close(fd)
		tempfiles.append(tmpfile)
		return tmpfile
				
	def check_install(command):
		"""
		Try executing an external command and return a boolean indicating whether
		that command is installed or not.  The 'command' argument should be
		something that executes quickly, without hitting the network (for
		instance, 'svn help' or 'git --version').
		"""
		try:
			p = subprocess.Popen(command.split(' '),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
			return True
		except OSError:
			return False

	def execute(command, env=None, split_lines=False, ignore_errors=False,
            extra_ignore_errors=(), translate_newlines=True):
		"""
		Utility function to execute a command and return the output.
		"""
		if isinstance(command, list):
			debug(subprocess.list2cmdline(command))
		else:
			debug(command)

		if env:
			env.update(os.environ)
		else:
			env = os.environ.copy()

		env['LC_ALL'] = 'en_US.UTF-8'
		env['LANGUAGE'] = 'en_US.UTF-8'

		if sys.platform.startswith('win'):
			p = subprocess.Popen(command,
								 stdin=subprocess.PIPE,
								 stdout=subprocess.PIPE,
								 stderr=subprocess.STDOUT,
								 shell=False,
								 universal_newlines=translate_newlines,
								 env=env)
		else:
			p = subprocess.Popen(command,
								 stdin=subprocess.PIPE,
								 stdout=subprocess.PIPE,
								 stderr=subprocess.STDOUT,
								 shell=False,
								 close_fds=True,
								 universal_newlines=translate_newlines,
								 env=env)
		if split_lines:
			data = p.stdout.readlines()
		else:
			data = p.stdout.read()
		rc = p.wait()
		if rc and not ignore_errors and rc not in extra_ignore_errors:
			die('Failed to execute command: %s\n%s' % (command, data))

		return data

	def check_gnu_diff():
		"""Checks if GNU diff is installed, and informs the user if it's not."""
		has_gnu_diff = False

		try:
			result = execute(['diff', '--version'], ignore_errors=True)
			has_gnu_diff = 'GNU diffutils' in result
		except OSError:
			pass

		if not has_gnu_diff:
			sys.stderr.write('\n')
			sys.stderr.write('GNU diff is required for Subversion '
							 'repositories. Make sure it is installed\n')
			sys.stderr.write('and in the path.\n')
			sys.stderr.write('\n')

			if os.name == 'nt':
				sys.stderr.write('On Windows, you can install this from:\n')
				sys.stderr.write(GNU_DIFF_WIN32_URL)
				sys.stderr.write('\n')

			die()
	
	def die(msg=None):
		"""
		Cleanly exits the program with an error message. Erases all remaining
		temporary files.
		"""
		for tmpfile in tempfiles:
			try:
				os.unlink(tmpfile)
			except:
				pass

		if msg:
			print msg

		sys.exit(1)
		
	def output( self, text = '' ):
		"""output( self, text )
		
		outputs text
		
		Parameters:
			text, the text being outputted. Defaults: ''
			
		"""
		
		print text
		
	def raise_error( self, errorType = 'UnknownErrorType', errorMessage = 'No message', logError = True ):
		"""raise_error( self, errorType, errorMessage, logError )
		
		Logs and reports an error, then exits the program.
		NOTE: Under the default implementation, the only difference between an error and a warning,
			is that errors call exit afterward.
		
		Parameters
			errorType, the kind of error that has occurred. Defaults: 'UnknownErrorType'
			errorMessage, A message explaining what caused the error. Defaults: 'No message'
			logError, whether the error should be logged. Defaults: True
		
		"""
	
		output( 'Error-' + errorType + ': ' + errorMessage )

		if logError:
			file = open( self.log_file, 'a' )
			
			if not file:
				output( 'Further Error, could not open logfile (located at "' + self.log_file + '").' )
				exit(ERR_NO)
				
			file.write('Error,' + errorType + ',' + errorMessage)
			
			file.close()
		
	def raise_warning( self, warningType = 'UnknownWarningType', warningMessage = 'No message', logWarning = True ):
		"""raise_error( self, warningType, warningMessage, logWarning
		
		Logs and reports a warning.
		NOTE: Under the default implementation, the only difference between an error and a warning,
			is that errors call exit afterward.
		
		Parameters
			warningType, the kind of warning that has occurred. Defaults: 'UnknownErrorType'
			warningMessage, A message explaining what caused the warning. Defaults: 'No message'
			logWarning, whether the warning should be logged. Defaults: True
		
		"""
	
		output( 'Warning-' + warningType + ': ' + warningMessage )
		
		if logWarning:
			file = open( self.log_file, 'a' )
			
			if not file:
				output( 'Error, could not open logfile (located at "' + self.log_file + '").' )
				exit(ERR_NO)
				
			file.write('Error,' + warningType + ',' + warningMessage)
			
			file.close()