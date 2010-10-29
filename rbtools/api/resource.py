import serverinterface
import urllib2

try:
    from json import loads as json_loads
except ImportError:
    from simplejson import loads as json_loads


class ResourceError(Exception):
    INVALID_KEY = 1

    def __init__(self, code, msg, *args, **kwargs):
        Exception(self, *args, **kwargs)
        self.code = code
        self.msg = msg

    def __str__(self):
        code_str = "Resource Error %d: " % self.code
        code_str += self.msg
        return code_str


class ResourceBase(object):
    """
    Base class from which other Resource objects should inherit.
    """
    def __init__(self, server_interface):
        self.url = None
        self.server_interface = server_interface
        self.resource_type = 'resource_base'
        self.resource_string = None
        self.data = {}


    def __str__(self):
        return self.resource_string

    def is_ok(self):
        """
        Returns true if the resource was provided from the server without
        error.  If the request to the server wasn't successfull for any
        reason, false is returned.
        """
        return self.get_field('stat') == 'ok'

    def get_keys(self):
        """
        Returns a list of the keys which comprise to this resource.
        """
        return self.data.keys()

    def get_fields(self):
        """
        Returns a list of the values contained within this resource.
        """
        return self.data.values()

    def get_field(self, key_list):
        """
        Attempts to retrieve the field mapped by the key_list.
        If there is no value found under the specified key_list an INVALID_KEY
        error is raised.

        Parameters:
            key_list - the key(s) which map to a value to be obtained.
                       key_list can be a single (non-list) key, or any list
                       of keys to a set of nested dicts, in order of retrieval.

        Returns:
            The field mapped to by the key_list.
        """
        if isinstance(key_list, list):
            field = self.data.get(key_list[0])

            if field:
                for key in key_list[1:]:
                    field = field.get(key)

                    if field == None:
                        break
        else:
            field = self.data.get(key_list)

        if field == None:
            raise ResourceError(ResourceError.INVALID_KEY, '%s is not a valid '
                'key for this resource.' % key_list)
        else:
            return field

    def get_links(self):
        """
        Returns the links available to this resource.  This is equivilant to
        calling get_field('links').

        .. note::
            This method MUST be overridden for subclasses whose 'links' are
            not stored directly in the root of the resource.
        """
        try:
            return self.get_field('links')
        except ResourceError, e:
            raise ResourceError(ResourceError.INVALID_KEY, e.msg + \
                '  This is likely because you must use the resource object '
                'specific to this resource.')

    def get_link(self, link_name):
        try:
            link_list = self.get_links()
            return link_list[link_name]['href']
        except KeyError, e:
            raise ResourceError(ResourceError.INVALID_KEY, 'The resource could'
                ' not retrieve the link %s' % link_name)

class Resource(ResourceBase):
    """
    An object which specifically deals with resources.
    """
    def __init__(self, server_interface, create_url, resource_type):
        ResourceBase.__init__(self, server_interface)
        self.create_url = create_url
        self.resource_type = resource_type

    def save(self):
        self.resource_string = self.server_interface.post(self.create_url,
                                                          self.data)
        self.data = json_loads(self.resource_string)

        if not self.is_ok():
            raise ResourceError(ResourceError.REQUEST_FAILED, 'The resource '
                'requested could not be retrieved - from save.')

    def set_field(self, field, value):
        self.data[field] = value

    def get_links(self):
        """
        Overriden specifically for a ReviewRequest.
        """
        return self.get_field([resource_type, 'links'])

class ResourceList(ResourceBase):
    """
    An object which specifically deals with lists of resources.
    """
    def __init__(self, server_interface, url):
        ResourceBase.__init__(self, server_interface)
        self.url = url
        self.resource_type = 'resource_list'
        self.child_resource_type = None
        self._index = -1

        self._load()

    def _load(self):
        if not self.server_interface.is_logged_in():
            raise ResourceError(ResourceError.LOGIN_REQUIRED, 'The server '
                'interface must be logged in.')

        try:
            self.resource_string = self.server_interface.get(self.url)
            self.data = json_loads(self.resource_string)
        except serverinterface.APIError, e:
            print e
        except urllib2.HTTPError, e:
            print e

        if not self.is_ok():
            raise ResourceError(ResourceError.REQUEST_FAILED, 'The resource '
                'requested could not be retrieved.')

        for elem in self.data:
            if elem not in ['stat', 'links', 'total_results']:
                self.child_resource_type = elem

        if self.child_resource_type is None:
            print "error getting the type of child resource"

    def create(self):
        return Resource(self.server_interface, self.get_link('create'), self.child_resource_type)    

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        self._index += 1
        if self._index == self.__len__():
            self._index = -1
            raise StopIteration
        else:
            return self.data[self.child_resource_type][self._index]

    def __len__(self):
        return len(self.data[self.child_resource_type])

    def __contains__(self, key):
        contains = False

        for n in self:
            if n == key:
                contains = True
                break

        return contains

    def __getitem__(self, position):
        return self.data[self.child_resource_type][position]    
