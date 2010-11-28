import os
import re
import sys

from rbtools.api.resource import Resource, RootResource, ReviewRequest, ResourceList, DiffResource
from rbtools.api.serverinterface import ServerInterface

VIEW = 'view'
RESOURCE_NAMES = [VIEW]

TIMESTAMP = 'timestamp'
ID = 'id'
LINKS = 'name'
FILE = 'files'


def main():
    valid = False
    resource_map = {}
    resource_map[VIEW] = 'diffs'

    if len(sys.argv) > 1:
        cwd = os.getcwd()
        cookie = os.path.join(cwd, '.rb_cookie')
        server_url = 'http://demo.reviewboard.org/'
        command = sys.argv[1]

        if command[0] == '-':
            command = command[1:]

            if RESOURCE_NAMES.count(command) == 1:
                valid = True

                resource_name = resource_map[command]
                server = ServerInterface(server_url, cookie)
                root = RootResource(server, server_url + 'api/')

                if command == VIEW:
                    if len(sys.argv) > 2 and sys.argv[2].isdigit():
                        id = sys.argv[2]
                        review_requests = root.get('review_requests')
                        request = ReviewRequest(review_requests.get(id))
                        diffs = ResourceList(server,request.get_link(resource_name))
                        
                        diff_id = '1' if len(sys.argv) < 4 else sys.argv[3]
                        
                        if diff_id.isdigit():
                            diff = DiffResource(diffs.get(diff_id))
                            print diff.get_field('timestamp')
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
