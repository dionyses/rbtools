import os
import sys

from rbtools.api.resource import Resource, RootResource, ReviewRequest
from rbtools.api.serverinterface import ServerInterface


def main():
    valid = False

    if len(sys.argv) > 1:
        cwd = os.getcwd()
        cookie = os.path.join(cwd, '.rb_cookie')
        server_url = 'http://demo.reviewboard.org/'
        resource_id = sys.argv[1]

        if resource_id.isdigit():
            valid = True
            server = ServerInterface(server_url, cookie)
            root = RootResource(server, server_url + 'api/')
            review_requests = root.get('review_requests')
            review_request = ReviewRequest(review_requests.get(resource_id))
            review_request.reopen()

    if not valid:
        print "usage: rb open <review_request_id>"

if __name__ == '__main__':
    main()
