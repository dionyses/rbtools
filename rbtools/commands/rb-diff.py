import os
import re
import sys

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
RESOURCE_NAMES = [MAKE, VIEW]

TIMESTAMP = 'timestamp'
ID = 'id'
LINKS = 'name'
FILE = 'files'


def main():
    valid = False
    resource_map = {}
    resource_map[VIEW] = 'diffs'
    settings = Settings()

    if len(sys.argv) > 1: #command given
        cwd = os.getcwd()
        cookie_file = settings.get_cookie_file()
        cookie = os.path.join(cwd, cookie_file)
        server_url = settings.get_server_url()
        command = sys.argv[1]

        if command[0] == '-':
            command = command[1:]

            if RESOURCE_NAMES.count(command) == 1:
                valid = True

                if command == MAKE:
                    #build a diff
                    client = get_client(server_url)

                    if client == None:
                        print 'could not find the source control manager'
                        exit()

                    diff_file = None

                    if len(sys.argv) > 2:
                        diff_file = sys.argv[2]
                    else:
                        diff_file = settings.get_setting('diff_file')

                    args = None

                    #args is only used for certain clients (e.g. Perforce)
                    if len(sys.argv) > 3:
                        args = sys.argv[3]

                    diff = client.diff(args)

                    file = open(diff_file, 'w')

                    if file < 0:
                        print 'could not open the file ' + diff_file + \
                                ' to write the diff.'

                    diff = diff[0].split('\n')
                    for line in diff:
                        file.write(line + '\n')

                    file.close()

                elif command == VIEW:
                    resource_name = resource_map[command]
                    server = ServerInterface(server_url, cookie)
                    api_uri = settings.get_api_uri()
                    root = RootResource(server, server_url + api_uri)

                    if len(sys.argv) > 2 and sys.argv[2].isdigit():
                        id = sys.argv[2]
                        review_requests = root.get('review_requests')
                        request = ReviewRequest(review_requests.get(id))
                        diffs = ResourceList(server, \
                                        request.get_link(resource_name))

                        diff_id = '1' if len(sys.argv) < 4 else str(sys.argv[3])

                        if diff_id.isdigit():
                            diff = DiffResource(diffs.get(diff_id))

                            if len(sys.argv) > 4 and sys.argv[4] != 'all':
                                print diff.get_field(sys.argv[4])
                            else:
                                keys = diff.get_fields()

                                for key in keys:
                                    print str(key) + ': ' \
                                        + str(diff.get_field(key))
                        #elif diff_id == 'all':
                        #    for i in range(len(diffs)):
                        #        diff = DiffResource(diffs.get(i))
                        #
                        #        if len(sys.argv) > 3 and sys.argv[3] != 'all':
                        #            print diff.get_field(sys.argv[3])
                        #        else:
                        #            keys = diff.get_fields()
                        #
                        #            for key in keys:
                        #                print str(key) + ': ' \
                        #                   + diff.get_field(key)
                        else:
                            print diff_id + ' is not a valid diff ID'
                    else:
                        if len(sys.argv) > 2:
                            print sys.argv[2] + ' is not a valid resource ID'
                        else:
                            print VIEW + ' needs a valid resource ID'

            else:
                print 'Invalid command: ' + command

    if not valid:
        print 'usage rb diff -resource_name [resource_id]\nresource_names:'
        for name in RESOURCE_NAMES:
            print '     ' + name

if __name__ == '__main__':
    main()
