import os
import re
import sys
from urllib2 import HTTPError

from rbtools.api.settings import Settings
from rbtools.api.resource import Resource, \
                                RootResource, \
                                ReviewRequest, \
                                ResourceList, \
                                DiffResource
from rbtools.api.serverinterface import ServerInterface
from rbtools.clients.getclient import get_client

MAKE = 'make'
VIEW = 'view'
GET = 'get'
RESOURCE_NAMES = [MAKE, VIEW, GET]

TIMESTAMP = 'timestamp'
ID = 'id'
LINKS = 'name'
FILE = 'files'


def main():
    diff(sys.argv[1:])

def diff(args):
    valid = False
    resource_map = {GET: 'diffs', VIEW: 'diffs'}
    settings = Settings()

    if len(args) > 0:  # command given
        cwd = os.getcwd()
        cookie_file = settings.get_cookie_file()
        cookie = os.path.join(cwd, cookie_file)
        server_url = settings.get_server_url()
        command = args[0]

        if command[0] == '-':
            command = command[1:]

        if RESOURCE_NAMES.count(command) == 1:
            valid = True

            if command == MAKE:
                """builds a local diff

                builds a diff of the local repository. call is:
                rb -diff <diff_file> <args>

                    diff_file: optional, the name of the file to write to
                    args: arguments required for build a diff. Unneaded for
                          most clients, but some (e.g. Perforce require it)
                """
                client = get_client(server_url)

                if client == None:
                    print 'could not find the source control manager'
                    exit()

                #determine the file to save to
                diff_file = None
                if len(args) > 1:
                    diff_file = args[1]
                else:
                    diff_file = settings.get_setting('client_diff')

                diff_args = None

                #diff_args is only used for certain clients (e.g. Perforce)
                if len(args) > 2:
                    diff_args = args[2]

                diff = client.diff(diff_args)

                #write the diff
                file = open(diff_file, 'w')

                if file < 0:
                    print 'could not open the file ' + diff_file + \
                            ' to write the diff.'

                diff = diff[0].split('\n')
                for line in diff:
                    file.write(line + '\n')

                file.close()

            elif command == VIEW or command == GET:
                """
                Viewing info about a diff and requesting the physical diff
                is almost completely the same operation, both are stored at
                the same location on the server. The only difference in the
                request is that to get the diff file, a specific mime-type
                is listed in the Accept header of the get request
                (currently text/x-patch, it is defined in config.dat).
                """
                resource_name = resource_map[command]

                #establish a connection to the server
                server = ServerInterface(server_url, cookie)
                root = RootResource(server, server_url \
                                + settings.get_api_uri())

                #find the review
                if len(args) > 1 and args[1].isdigit():
                    id = args[1]
                    review_requests = root.get('review_requests')
                    
                    try:
                        request = ReviewRequest(review_requests.get(id))
                    except HTTPError:
                        print 'Unknown review request id: ' + id
                        exit()

                    diffs = ResourceList(server, \
                                    request.get_link(resource_name))

                    """find out which diff is required

                    find the required diff. If no preference is given, will
                    default to diff 1. If diff_id of 'all' is requested,
                    the operation (VIEW or GET) will be run on each diff,
                    one at a time. In this case, diff files will be
                    prefixed with <diff_num>_.
                    """
                    diff_id = '1' if len(args) < 3 \
                                  else str(args[2])
                    if diff_id.isdigit():
                        #single diff
                        diff = DiffResource(diffs.get(diff_id))

                        if command == VIEW:
                            #VIEW will display all fields unless
                            #a specific field is requested
                            if len(args) > 3 and args[3] != 'all':
                                print diff.get_field(args[3])
                            else:
                                keys = diff.get_fields()

                                for key in keys:
                                    print str(key) + ': ' \
                                        + str(diff.get_field(key))
                        else:  # GET
                            if len(args) > 3:
                                diff_file = args[3]
                            else:
                                diff_file = \
                                    settings.get_setting('server_diff')

                            sd = diff.get_file( \
                                    settings.get_setting('diff_mime'))

                            file = open(diff_file, 'w')

                            if file < 0:
                                print 'could not open "' + diff_file \
                                                + '" for writing.'
                                exit()

                            file.write(sd)
                            file.close()
                    elif diff_id == 'all':
                        #deal with each dif, one at a time
                        ids = diffs.get_fields()
                        for diff_id in ids:
                            diff = DiffResource(diffs.get(diff_id))
                            print 'diff ' + str(diff_id) + ':'

                            if command == VIEW:
                                #VIEW will display all fields
                                #unless a specific field is requested
                                if len(args) > 3 and \
                                            args[3] != 'all':
                                    print diff.get_field(args[3])
                                else:
                                    keys = diff.get_fields()

                                    for key in keys:
                                        print '\t' + str(key) + ': ' \
                                            + str(diff.get_field(key))
                            else:  # GET
                                if len(args) > 3:
                                    diff_file = args[3]
                                else:
                                    diff_file = \
                                        settings.get_setting('server_diff')
                                diff_file = str(diff_id) + '_' + diff_file

                                sd = diff.get_file( \
                                    settings.get_setting('diff_mime'))

                                file = open(diff_file, 'w')

                                if file < 0:
                                    print 'could not open "' + diff_file \
                                                    + '" for writing.'
                                    exit()
                    else:
                        print diff_id + ' is not a valid diff ID'
                else:
                    if len(args) > 1:
                        print args[1] + ' is not a valid resource ID'
                    else:
                        print command + ' needs a valid resource ID'

        else:
            print 'Invalid command: ' + command

    if not valid:
        print 'usage rb diff -resource_name [resource_id]\nresource_names:'
        for name in RESOURCE_NAMES:
            print '     ' + name

if __name__ == '__main__':
    main()
