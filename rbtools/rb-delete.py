#import API STUFF

rb_server_url = "http://reviews.reviewboard.org"
local_repository = Repository.Repository(rb_server_url)

rb_interface = RBInterface.RBInterface()
server_mgr = ServerManager.ServerManager(rb_interface, local_repository)

if !server_mgr.login()
    print "Login unsuccessfull!"

#Get the review request to delete
try:
    review_request = server_mgr.GetReviewRequest(<review request number>)

    print "Going to delete review request #%s" % <review request number>
    print "The summary of this request is: %s" % review_request.get_field("summary")
    print "Please confirm that you would like to delete this request."
   
    confirmation = raw_input("(yes/no): ")
    if confirmation == "yes" or confirmation == "y"
        review_request.delete()

except APIError, e:
    if e.error_code == <Access Denied>, <Request DNE>
	print "There was some error retrieving the request..  Request not deleted!"

