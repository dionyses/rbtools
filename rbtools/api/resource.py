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
    def __init__(self, server_interface, url, resource_type):
        ResourceBase.__init__(self, server_interface)
        self.url = url
        self.resource_type = resource_type

    def save(self):
        if not self.server_interface.is_logged_in():
            raise ResourceError(ResourceError.LOGIN_REQUIRED, 'The server '
                'interface must be logged in.')

        self.resource_string = self.server_interface.post(self.url,
                                                          self.data)
        self.data = json_loads(self.resource_string)

        if not self.is_ok():
            raise ResourceError(ResourceError.REQUEST_FAILED, 'The resource '
                'requested could not be retrieved - from save.')

    def load(self):
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
        self.child_resource_url = None
        self.field_id = None
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
            if elem not in ['stat', 'links', 'total_results', 'uri_templates']:
                self.child_resource_type = elem

        if self.child_resource_type is None:
            print "error getting the type of child resource"
        else:
            try:
                self.child_resource_url = self.get_field(['uri_templates',
                                                       self.child_resource_type,
                                                       'href'])
            except ResourceError, e:
                print e
                print "pretending..."
                self.child_resource_url = self.get_field(['links', 'self',
                                                          'href'])
                self.child_resource_url += '{some_id_field}/'
                print self.child_resource_url

    def create(self):
        if self.child_resource_type is None:
            #there is no child resource type so 'create' is meaningless
            raise ResourceError(ResourceError.NO_CHILD_RESOURCE, 'The '
                'request cannot be made because this resource list has '
                'no child type.')
        else:
            return Resource(self.server_interface, self.get_link('create'),
                            self.child_resource_type)    

    def get(self, field_id):
        split_url = r_section_erase(self.child_resource_url, '{', '}')

        if split_url is None:
            raise ResourceError(ResourceError.INVALIDE_CHILD_RESOURCE_URL,
                "couldn't parse the {id} section from the child resource url")

        return Resource(self.server_interface, split_url[0] + '%d' % field_id +
                        split_url[1], self.child_resource_type)
        

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
            if self.child_resource_type is None:
                #there is no child resource type so iterating is meaningless
                raise ResourceError(ResourceError.NO_CHILD_RESOURCE, 'The '
                    'request cannot be made because this resource list has '
                    'no child type.')
            else:
                return self.data[self.child_resource_type][self._index]

    def __len__(self):
        if self.child_resource_type is None:
            #there is no child resource type so iterating is meaningless
            raise ResourceError(ResourceError.NO_CHILD_RESOURCE, 'The '
                'request cannot be made because this resource list has '
                'no child type.')
        else: 
           return len(self.data[self.child_resource_type])

    def __contains__(self, key):
        contains = False

        for n in self:
            if n == key:
                contains = True
                break

        return contains

    def __getitem__(self, position):
        if self.child_resource_type is None:
            #there is no child resource type so indexing is meaningless
            raise ResourceError(ResourceError.NO_CHILD_RESOURCE, 'The '
                'request cannot be made because this resource list has '
                'no child type.')
        else: 
            return self.data[self.child_resource_type][position]


def r_section_erase(string, left_marker, right_marker):
    left_pos = string.rfind(left_marker)
    right_pos = string.rfind(right_marker)

    #if the left or right marker cannot be found
    if left_pos == -1 or right_pos == -1:
        return None
    #if the markers are found but positioned incorrectly
    elif left_pos > right_pos:
        return None
    #if the left marker extends past the right marker
    elif left_pos + len(left_marker) > right_pos + len(right_marker):
        return None

    out = [string[0:left_pos], string[right_pos+len(right_marker):]]
    return out
