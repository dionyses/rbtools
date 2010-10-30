import os
import RBUtilities
import Repository
import Resource
import ServerInterface
import urllib2


class ServerManager(object):
    """
    ServerManager is the class responsible for handling server/client
    interactions. It is responsible for authenticating with ReviewBoard
    servers, and creating requests (such as new reviews, diffs, etc. ).
    It uses an RBInterface to make its REST (POST, GET, DELETE, etc. ) calls,
    and also for storing cookies
    """

    COOKIE_NAME = '.cookie.txt'
    API_ROOT = 'api/'
    LOGIN_PATH = 'json/accounts/login/'
    REVIEWS_PATH = 'review-requests/'

    root = None
    current = None
    interface = None
    repo = None
    cookie = None
    util = None
    user = None
    url = None

    def __init__(self, url=None, interface=None, \
        cookie=None, repo=None, util=RBUtilities.RBUtilities()):
        """
            Initiates a new ServerManager Object

            Parameters:
                url: The root url of the rb server
                interface: the interface used to communicate with the server
                cookie: the cookie file (if None, cookie is made in cwd)
                util: A collection of utility functions
        """

        if util is None:
            util = RBUtilities.RBUtilities()
            util.raise_warning("missingRequiredParameter", "ServerManager \
                requires an object of type RBUtilities in order to function. \
                Loading default RBUtilites.")
        elif not isinstance(util, RBUtilities.RBUtilities):
            util = RBUtilities.RBUtilities()
            util.raise_warning("TypeMismatch", "ServerManager requires \
                RBUtilities (or a child thereof) in order to function. \
                Loading default RBUtilities instead.")

        if not url:
            util.raise_error("missingRequiredParameter", \
                "No server URL supplied")

        #is this how we need to do the cookie and interface?  for example,
        #if the interface already has a cookie, won't this overwrite it and
        #thus invalidate it?
        if not cookie:
            cwd = os.getcwd()
            cookie = os.path.join(cwd, self.COOKIE_NAME)

        if not interface:
            interface = ServerInterface.ServerInterface(cookie)

        if not repo:
            repo = util.get_repository(url)

        self.url = url
        self.interface = interface
        self.cookie = cookie
        self.repo = repo
        self.util = util

        try:
            self.root = Resource.Resource(interface.get( \
                self.url + self.API_ROOT))
            if not self.root.is_ok():
                util.die("There was an error connecting to the ReviewBoard \
                    server.  Please check the url and try again.")
        except ServerInterface.APIError, e:
            print e
        except urllib2.HTTPError, e:
            interface.process_error(e.code, e.read())

        self.current = self.root

    def login(self, rb_user=None, rb_password=None, force=False):
        """
        Logs into a ReviewBoard server

        Parameters:
            force, whether or not to force entering of credentials
                (i.e. don't use cookie). Defaults: False
            rb_user, The username. If None, the user will be prompted
                Defaults: None
            rb_password, The password. If None, the user will be prompted
                Defaults: None

        Returns: True/False whether login was successful
        """

        logged_in = False

        if force or not self.interface.has_valid_cookie():
            self.util.output( \
                "==>Connecting to Review Board at: " + self.root.url())

            if not rb_password or not rb_user:

                if rb_user:
                    self.util.output("Username: " + rb_user)
                else:
                    rb_user = self.util.input("Username: ")

                if not rb_password:
                    rb_password = self.util.input("Password: ", True)

            body = {'username': rb_user, 'password': rb_password}

            try:
                resp = Resource.Resource(self.interface.post( \
                    self.url + self.API_ROOT + self.LOGIN_PATH, body) \
                )

                if resp.is_ok():
                    logged_in = True

            except ServerInterface.APIError, e:
                print e
            except urllib2.HTTPError, e:
                self.interface.process_error(e.code, e.read())

        else:
            #valid cookie already established (and force=false).  Do nothing
            logged_in = True

        self.user = rb_user

        if logged_in:
            self.util.output('login successful')
        else:
            self.util.raise_warning('LOGIN_FAILURE', \
                'Failed to login to the ReviewBoard server')

        return logged_in

    def create_review_request(self, rep_id=None):
        """
        Attempts to create a ReviewRequest object.  If successfull,
        self.current is set to this new review request.

        Parameters:
            repo_id: The name of the server's repository (this will later be
                supplied by the Repository Class

        Returns: True/False whether creation was successful
        """
        body = {}
        body['submit_as'] = self.user
        body['repository'] = repo_id

        try:
            self.current = Resource.ReviewRequest(self.interface.post( \
                self.root.url() + self.REVIEWS_PATH, body) \
            )

            if not self.current.is_ok():
                self.util.raise_error("HTTPError", \
                    "Failed to get a response from the server")
            else:
                return True

        except ServerInterface.APIError, e:
            print e
        except urllib2.HTTPError, e:
            #self.interface.process_error(e.code, e.read())
            print e

        return False

    def select_review_request(self, review_num):
        """
        Attempts to set the current resource to be the review request indicated
        by the specified review_num.  The review must already exist.

        Parameters:
            review_num: the id of the review request to be selected

        Returns: True/False whether the selection was successful
        """
        try:
            self.current = Resource.ReviewRequest( \
                self.interface.get(self.root.url() + self.REVIEWS_PATH + \
                review_num + '/') \
            )
        except ServerInterface.APIError, e:
            print e
        except urllib2.HTTPError, e:
            print e

        return self.current.is_ok()

    def update_draft_review_request(self, changes):
        """
        Trys to update the current review request with the specified changes.
        self.current must be ethier a ReviewRequest or DraftReviewRequest type
        Resource.  Only changes that can effect a DraftReviewRequest will be
        made.

        Parameters:
            changes: a dictionary of changes to be made ex: {'public':'true'}

        Returns: True/False whether update was successful
        """
        if not isinstance(self.current, Resource.ReviewRequest) and \
            not isinstance(self.current, Resource.DraftReviewRequest):
                return False

        draft_url = None
        rsp = None

        try:
            if isinstance(self.current, Resource.ReviewRequest):
                draft_url = self.current.draft_url()
            else:
                draft_url = self.current.url()

            rsp = self.interface.put(draft_url, changes)
            self.current = Resource.DraftReviewRequest(rsp)
        except urllib2.HTTPError, e:
            if e.code == 303:
                #HTTP redirect error - the update was successful
                #perform an HTTP get on the draft's parent
                if isinstance(self.current, Resource.ReviewRequest):
                    rsp = self.interface.get(self.current.url())
                else:
                    rsp = self.interface.get(self.current.parent_url())

                self.current = Resource.ReviewRequest(rsp)
            else:
                print e
                self.util.raise_error("HTTPError", "Failed on update")

        return self.current.is_ok()

        """
        #stuff to get working later
        if 1 == 2:
            if not resp:
                self.util.raise_error("HTTPError", \
                    "Failed to get a response from the server during put")

            print "about to make draft"
            review_request = Resource.DraftReviewRequest(resp)
            print "draft made"

            if not review_request or not review_request.is_ok():
                self.util.raise_error( "ObjectCreationError",  \
                    "Failed to make an update review request object")

            return review_request
        """

    def update_review_request(self, changes):
        """
        Trys to update the current review request with the specified changes.
        self.current must be ethier a ReviewRequest or DraftReviewRequest type
        Resource.  Only changes that can effect a ReviewRequest will be
        made.

        Parameters:
            changes: a dictionary of changes to be made
                ex. {'status':'submitted'}

        Returns: True/False whether update was successful
        """
        if not isinstance(self.current, Resource.ReviewRequest) and \
            not isinstance(self.current, Resource.DraftReviewRequest):
                return False

        review_request_url = None
        rsp = None
        try:
            if isinstance(self.current, Resource.ReviewRequest):
                review_request_url = self.current.url()
            else:
                review_request_url = self.current.parent_url()

            rsp = self.interface.put(review_request_url, changes)
            self.current = Resource.ReviewRequest(rsp)
        except urllib2.HTTPError, e:
            print e
            self.util.raise_error("HTTPError", "Failed on update")

        return self.current.is_ok()

    def publish_review_request(self):
        """
        Attempts to publish the current review request.

        Returns: True/False whether the draft is published or not
        """
        return self.update_draft_review_request({'public': 'true'})

    def close_review_request(self):
        """
        Attempts to close the current review request.

        Returns: True/False whether the draft is published or not
        """
        return self.update_review_request({'status': 'submitted'})

    def delete_review_request(self):
        """
        Deletes the currently selected review request, if you have the right
        permissions

        Returns: True/False whether delete was successful
        """
        try:
            self.current = Resource.Resource(self.interface.delete( \
                self.current.url()) \
            )
        except urllib2.HTTPError, e:
            print e
            self.util.raise_error("HTTPError", "Failed on delete: " + e.code())
