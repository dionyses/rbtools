import ServerInterface
import ServerManager

mgr = ServerManager.ServerManager('http://demo.reviewboard.org/', \
    ServerInterface.ServerInterface("._cookie.tmp"), "._cookie.tmp")

if mgr.login():
    print "logged in"

    if mgr.create_review_request('2'):
        print "created rr"

        if mgr.update_draft_review_request( \
            {'summary':'from api test client'} \
        ):
            print "updated rr"

            if mgr.publish_review_request():
                print "published rr"

                if mgr.close_review_request():
                    print "it worked!"
