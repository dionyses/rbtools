import sys
import os
import serverinterface
import resource

cwd = os.getcwd()
cookie = os.path.join(cwd, '.my_cookie')
srvr = serverinterface.ServerInterface('http://demo.reviewboard.org/', cookie)

if srvr.login():
    pass

root_list = resource.ResourceList(srvr, 'http://demo.reviewboard.org/api/')
print "RETRIEVING THE ROOT LIST"
#print root_list
print ""

review_requests_list = root_list.get('review_requests')
print "RETRIEVING REVIEW REQUESTS"
#print review_requests_list
print ""

review_request = review_requests_list.get(4569)
print "RETRIEVING REVIEW REQUEST 4569"
#print review_request
print ""

reviews = review_request.get_or_create('reviews')
print "RETRIEVING REVIEWS"
print reviews
print ""

old_review = reviews.get('4825')
print "RETRIEVING A REVIEW"
print old_review
print ""

old_review_draft = reviews.get('review_draft')
print "RETRIEVING A REVIEW DRAFT"
print old_review_draft
print ""

review = reviews.create()
review.update_field('body_top', 'patrick')
review.update_field('body_bottom', 'and patricia')
review.update_field('public', 'true')
review.save()
print "MAKING NEW REVIEW"
print review
print ""


