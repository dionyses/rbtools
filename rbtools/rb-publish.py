#import API STUFF

rb_server_url = "http://reviews.reviewboard.org"
local_repository = Repository.Repository(rb_server_url, '')

rb_interface = RBInterface.RBInterface()
server_mgr = ServerManager.ServerManager(rb_interface, local_repository)

#CONSIDERATION:  should login() return a success/error code, for a more specific indication of what went wrong 
if !server_mgr.login()
    print "Login unsuccessfull!"


#Make a new review request object.  Note that first creating a review request creates a draft.  This will have to be published eventually.
review_request = server_mgr.CreateNewReviewRequest(local_repository)

#Set any fields that need to be set
review_request.set_field(<some field name>, <some field data>)
#...

#Finally, publish the review request
review_request.publish()  

