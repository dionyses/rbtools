import sys
import ServerInterface
import ServerManager

mgr = ServerManager.ServerManager('http://demo.reviewboard.org/', \
    ServerInterface.ServerInterface("._cookie.tmp"), "._cookie.tmp")

if mgr.login():
    print "logged in"

    if mgr.select_review_request(sys.argv[1]):
        print "selected rr #%s" % sys.argv[1]

        if mgr.publish_review_request():
            print "published rr"

            if mgr.close_review_request():
                print "it worked!"
