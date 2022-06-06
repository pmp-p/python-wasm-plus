# ----------------------------------------------------------------------------
# pymunk
# Copyright (c) 2007-2012 Victor Blomqvist
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ----------------------------------------------------------------------------

"""
pymunk is a easy-to-use pythonic 2d physics library that can be used whenever
you need 2d rigid body physics from Python.

Homepage: http://www.pymunk.org

This is the main containing module of pymunk. It contains among other things
the very central Space, Body and Shape classes.

When you import this module it will automatically load the chipmunk library
file. As long as you haven't turned off the debug mode a print will show
exactly which Chipmunk library file it loaded. For example::

    >>> import pymunk
    Loading chipmunk for Windows (32bit) [C:\code\pymunk\chipmunk.dll]

"""
__version__ = "$Id: __init__.py 541 2013-08-22 17:36:25Z vb@viblo.se $"
__docformat__ = "reStructuredText"

__all__ = ["inf", "version", "chipmunk_version"
        , "Space", "Body", "Shape", "Circle", "Poly", "Segment"
        , "moment_for_circle", "moment_for_poly", "moment_for_segment"
        , "moment_for_box", "reset_shapeid_counter"
        , "SegmentQueryInfo", "Contact", "Arbiter", "BB"]

import ctypes as ct
import weakref
try:
    #Python 2.7+
    from weakref import WeakSet
except ImportError:
    from .weakrefset import WeakSet

from . import _chipmunk as cp
from . import _chipmunk_ffi as cpffi
from . import util as u
from .vec2d import Vec2d

from .constraint import *

version = "4.0.0"
"""The release version of this pymunk installation.
Valid only if pymunk was installed from a source or binary
distribution (i.e. not in a checked-out copy from svn).
"""

chipmunk_version = "%sR%s" % (cp.cpVersionString.value.decode(), '3bdf1b7b3c')
"""The Chipmunk version compatible with this pymunk version.
Other (newer) Chipmunk versions might also work if the new version does not
contain any breaking API changes.

This property does not show a valid value in the compiled documentation, only
when you actually import pymunk and do pymunk.chipmunk_version

The string is in the following format:
<cpVersionString>R<svn or github commit of chipmunk>
where cpVersionString is a version string set by Chipmunk and the svn version
corresponds to the svn version of the chipmunk source files included with
pymunk or the github commit hash. If the Chipmunk version is a release then
the second part will be empty

.. note::
    This is also the version of the Chipmunk source files included in the
    chipmunk_src folder (normally included in the pymunk source distribution).
"""

#inf = float('inf') # works only on python 2.6+
inf = 1e100
"""Infinity that can be passed as mass or inertia to Body.

Useful when you for example want a body that cannot rotate, just set its
moment to inf. Just remember that if two objects with both infinite masses
collides the world might explode. Similary effects can happen with infinite
moment.

.. note::
    In previous versions of pymunk you used inf to create static bodies. This
    has changed and you should instead do it by invoking the body constructor
    without any arguments.
"""

cp.cpEnableSegmentToSegmentCollisions()

class Space(object):
    """Spaces are the basic unit of simulation. You add rigid bodies, shapes
    and joints to it and then step them all forward together through time.
    """
    def __init__(self, iterations=10):
        """Create a new instace of the Space

        Its usually best to keep the elastic_iterations setting to 0. Only
        change if you have problem with stacking elastic objects on each other.
        If that is the case, try to raise it. However, a value other than 0
        will affect other parts, most importantly you wont get reliable
        total_impulse readings from the `Arbiter` object in collsion callbacks!

        :Parameters:
            iterations : int
                Number of iterations to use in the impulse solver to solve
                contacts.
        """

        self._space = cp.cpSpaceNew()
        self._space.contents.iterations = iterations

        self._static_body = Body()

        self._handlers = {} # To prevent the gc to collect the callbacks.
        self._default_handler = None

        self._post_step_callbacks = {}
        self._post_callback_keys = {}
        self._post_last_callback_key = 0
        self._removed_shapes = {}

        self._shapes = {}
        self._bodies = set()
        self._constraints = set()

        self._locked = False
        self._add_later = set()
        self._remove_later = set()

    def _get_shapes(self):
        return list(self._shapes.values())
    shapes = property(_get_shapes,
        doc="""A list of all the shapes added to this space (both static and non-static)""")

    def _get_bodies(self):
        return list(self._bodies)
    bodies = property(_get_bodies,
        doc="""A list of the bodies added to this space""")

    def _get_constraints(self):
        return list(self._constraints)
    constraints = property(_get_constraints,
        doc="""A list of the constraints added to this space""")

    def _get_static_body(self):
        """A convenience static body already added to the space"""
        return self._static_body
    static_body = property(_get_static_body, doc=_get_static_body.__doc__)

    def __del__(self):
        try:
            cp.cpSpaceFree(self._space)
        except:
            pass

    def _set_iterations(self, iterations):
        self._space.contents.iterations = iterations
    def _get_iterations(self):
        return self._space.contents.iterations
    iterations = property(_get_iterations, _set_iterations
        , doc="""Number of iterations to use in the impulse solver to solve
        contacts.""")


    def _set_gravity(self, gravity_vec):
        self._space.contents.gravity = gravity_vec
    def _get_gravity(self):
        return self._space.contents.gravity
    gravity = property(_get_gravity, _set_gravity
        , doc="""Default gravity to supply when integrating rigid body motions.""")

    def _set_damping(self, damping):
        self._space.contents.damping = damping
    def _get_damping(self):
        return self._space.contents.damping
    damping = property(_get_damping, _set_damping
        , doc="""Damping rate expressed as the fraction of velocity bodies
        retain each second.

        A value of 0.9 would mean that each body's velocity will drop 10% per
        second. The default value is 1.0, meaning no damping is applied.""")

    def _set_idle_speed_threshold(self, idle_speed_threshold):
        self._space.contents.idleSpeedThreshold = idle_speed_threshold
    def _get_idle_speed_threshold(self):
        return self._space.contents.idleSpeedThreshold
    idle_speed_threshold = property(_get_idle_speed_threshold
        , _set_idle_speed_threshold
        , doc="""Speed threshold for a body to be considered idle.
        The default value of 0 means to let the space guess a good threshold
        based on gravity.""")

    def _set_sleep_time_threshold(self, sleep_time_threshold):
        self._space.contents.sleepTimeThreshold = sleep_time_threshold
    def _get_sleep_time_threshold(self):
        return self._space.contents.sleepTimeThreshold
    sleep_time_threshold = property(_get_sleep_time_threshold
        , _set_sleep_time_threshold
        , doc="""Time a group of bodies must remain idle in order to fall
        asleep.

        Enabling sleeping also implicitly enables the the contact graph. The
        default value of `inf` disables the sleeping algorithm.""")

    def _set_collision_slop(self, collision_slop):
        self._space.contents.collisionSlop = collision_slop
    def _get_collision_slop(self):
        return self._space.contents.collisionSlop
    collision_slop = property(_get_collision_slop
        , _set_collision_slop
        , doc="""Amount of allowed penetration.

        Used to reduce oscillating contacts and keep the collision cache warm.
        Defaults to 0.1. If you have poor simulation quality, increase this
        number as much as possible without allowing visible amounts of
        overlap.""")

    def _set_collision_bias(self, collision_bias):
        self._space.contents.collisionBias = collision_bias
    def _get_collision_bias(self):
        return self._space.contents.collisionBias
    collision_bias = property(_get_collision_bias
        , _set_collision_bias
        , doc="""Determines how fast overlapping shapes are pushed apart.

        Expressed as a fraction of the error remaining after each second.
        Defaults to pow(1.0 - 0.1, 60.0) meaning that pymunk fixes 10% of
        overlap each frame at 60Hz.""")

    def _set_collision_persistence(self, collision_persistence):
        self._space.contents.collisionPersistence = collision_persistence
    def _get_collision_persistence(self):
        return self._space.contents.collisionPersistence
    collision_persistence = property(_get_collision_persistence
        , _set_collision_persistence
        , doc="""Number of frames that contact information should persist.

        Defaults to 3. There is probably never a reason to change this value.
        """)

    def _set_enable_contact_graph(self, enable_contact_graph):
        self._space.contents.enableContactGraph = enable_contact_graph
    def _get_enable_contact_graph(self):
        return self._space.contents.enableContactGraph
    enable_contact_graph = property(_get_enable_contact_graph
        , _set_enable_contact_graph
        , doc="""Rebuild the contact graph during each step.

        Must be enabled to use the get_arbiter() function on Body
        Disabled by default for a small performance boost. Enabled implicitly
        when the sleeping feature is enabled.
        """)

    def add(self, *objs):
        """Add one or many shapes, bodies or joints to the space

        Unlike Chipmunk and earlier versions of pymunk its now allowed to add
        objects even from a callback during the simulation step. However, the
        add will not be performed until the end of the step.
        """

        if self._locked:
            self._add_later.add(objs)
            return

        for o in objs:
            if isinstance(o, Body):
                self._add_body(o)
            elif isinstance(o, Shape):
                self._add_shape(o)
            elif isinstance(o, Constraint):
                self._add_constraint(o)
            else:
                for oo in o:
                    self.add(oo)

    def remove(self, *objs):
        """Remove one or many shapes, bodies or constraints from the space

        Unlike Chipmunk and earlier versions of pymunk its now allowed to
        remove objects even from a callback during the simulation step.
        However, the removal will not be performed until the end of the step.

        .. Note::
            When removing objects from the space, make sure you remove any
            other objects that reference it. For instance, when you remove a
            body, remove the joints and shapes attached to it.
        """

        if self._locked:
            self._remove_later.add(objs)
            return

        for o in objs:
            if isinstance(o, Body):
                self._remove_body(o)
            elif isinstance(o, Shape):
                self._remove_shape(o)
            elif isinstance(o, Constraint):
                self._remove_constraint(o)
            else:
                for oo in o:
                    self.remove(oo)

    def _add_shape(self, shape):
        """Adds a shape to the space"""
        assert shape._hashid_private not in self._shapes, "shape already added to space"
        self._shapes[shape._hashid_private] = shape
        cp.cpSpaceAddShape(self._space, shape._shape)
    def _add_body(self, body):
        """Adds a body to the space"""
        assert body not in self._bodies, "body already added to space"
        body._space = weakref.proxy(self)
        self._bodies.add(body)
        cp.cpSpaceAddBody(self._space, body._body)
    def _add_constraint(self, constraint):
        """Adds a constraint to the space"""
        assert constraint not in self._constraints, "constraint already added to space"
        self._constraints.add(constraint)
        cp.cpSpaceAddConstraint(self._space, constraint._constraint)

    def _remove_shape(self, shape):
        """Removes a shape from the space"""
        self._removed_shapes[shape._hashid_private] = shape
        del self._shapes[shape._hashid_private]
        cp.cpSpaceRemoveShape(self._space, shape._shape)
    def _remove_body(self, body):
        """Removes a body from the space"""
        body._space = None
        self._bodies.remove(body)
        cp.cpSpaceRemoveBody(self._space, body._body)
    def _remove_constraint(self, constraint):
        """Removes a constraint from the space"""
        self._constraints.remove(constraint)
        cp.cpSpaceRemoveConstraint(self._space, constraint._constraint)

    def reindex_static(self):
        """Update the collision detection info for the static shapes in the
        space. You only need to call this if you move one of the static shapes.
        """
        cp.cpSpaceReindexStatic(self._space)

    def reindex_shape(self, shape):
        """Update the collision detection data for a specific shape in the
        space.
        """
        cp.cpSpaceReindexShape(self._space, shape._shape)

    def step(self, dt):
        """Update the space for the given time step. Using a fixed time step is
        highly recommended. Doing so will increase the efficiency of the
        contact persistence, requiring an order of magnitude fewer iterations
        to resolve the collisions in the usual case."""

        self._locked = True
        cp.cpSpaceStep(self._space, dt)
        self._removed_shapes = {}
        self._post_step_callbacks = {}
        self._post_callback_keys = {}
        self._post_last_callback_key = 0
        self._locked = False

        for objs in self._add_later:
            self.add(objs)
        self._add_later.clear()

        for objs in self._remove_later:
            self.remove(objs)
        self._remove_later.clear()

    def add_collision_handler(self, a, b, begin=None, pre_solve=None, post_solve=None, separate=None, *args, **kwargs):
        """Add a collision handler for given collision type pair.

        Whenever a shapes with collision_type a and collision_type b collide,
        these callbacks will be used to process the collision.
        None can be provided for callbacks you do not wish to implement,
        however pymunk will call it's own default versions for these and not
        the default ones you've set up for the Space. If you need to fall back
        on the space's default callbacks, you'll have to provide them
        individually to each handler definition.

        :Parameters:
            a : int
                Collision type of the first shape
            b : int
                Collision type of the second shape
            begin : ``func(space, arbiter, *args, **kwargs) -> bool``
                Collision handler called when two shapes just started touching
                for the first time this step. Return false from the callback
                to make pymunk ignore the collision or true to process it
                normally. Rejecting a collision from a begin() callback
                permanently rejects the collision until separation. Pass
                `None` if you wish to use the pymunk default.
            pre_solve : ``func(space, arbiter, *args, **kwargs) -> bool``
                Collision handler called when two shapes are touching. Return
                false from the callback to make pymunk ignore the collision or
                true to process it normally. Additionally, you may override
                collision values such as `Arbiter.elasticity` and
                `Arbiter.friction` to provide custom friction or elasticity
                values. See `Arbiter` for more info. Pass `None` if you wish
                to use the pymunk default.
            post_solve : ``func(space, arbiter, *args, **kwargs)``
                Collsion handler called when two shapes are touching and their
                collision response has been processed. You can retrieve the
                collision force at this time if you want to use it to
                calculate sound volumes or damage amounts. Pass `None` if you
                wish to use the pymunk default.
            separate : ``func(space, arbiter, *args, **kwargs)``
                Collision handler called when two shapes have just stopped
                touching for the first time this frame. Pass `None` if you
                wish to use the pymunk default.
            args
                Optional parameters passed to the collision handler functions.
            kwargs
                Optional keyword parameters passed on to the collision handler
                functions.

        """

        _functions = self._collision_function_helper(begin, pre_solve, post_solve, separate, *args, **kwargs)

        self._handlers[(a, b)] = _functions
        cp.cpSpaceAddCollisionHandler(self._space, a, b,
            _functions[0], _functions[1], _functions[2], _functions[3], None)

    def set_default_collision_handler(self, begin=None, pre_solve=None, post_solve=None, separate=None, *args, **kwargs):
        """Register a default collision handler to be used when no specific
        collision handler is found. If you do nothing, the space will be given
        a default handler that accepts all collisions in begin() and
        pre_solve() and does nothing for the post_solve() and separate()
        callbacks.

        :Parameters:
            begin : ``func(space, arbiter, *args, **kwargs) -> bool``
                Collision handler called when two shapes just started touching
                for the first time this step. Return False from the callback
                to make pymunk ignore the collision or True to process it
                normally. Rejecting a collision from a begin() callback
                permanently rejects the collision until separation. Pass
                `None` if you wish to use the pymunk default.
            pre_solve : ``func(space, arbiter, *args, **kwargs) -> bool``
                Collision handler called when two shapes are touching. Return
                False from the callback to make pymunk ignore the collision or
                True to process it normally. Additionally, you may override
                collision values such as Arbiter.elasticity and
                Arbiter.friction to provide custom friction or elasticity
                values. See Arbiter for more info. Pass `None` if you wish to
                use the pymunk default.
            post_solve : ``func(space, arbiter, *args, **kwargs)``
                Collsion handler called when two shapes are touching and their
                collision response has been processed. You can retrieve the
                collision force at this time if you want to use it to
                calculate sound volumes or damage amounts. Pass `None` if you
                wish to use the pymunk default.
            separate : ``func(space, arbiter, *args, **kwargs)``
                Collision handler called when two shapes have just stopped
                touching for the first time this frame. Pass `None` if you wish
                to use the pymunk default.
            args
                Optional parameters passed to the collision handler functions.
            kwargs
                Optional keyword parameters passed on to the collision handler
                functions.
        """

        _functions = self._collision_function_helper(
            begin, pre_solve, post_solve, separate, *args, **kwargs
            )
        self._default_handler = _functions
        cp.cpSpaceSetDefaultCollisionHandler(self._space,
            _functions[0], _functions[1], _functions[2], _functions[3], None)

    def _collision_function_helper(self, begin, pre_solve, post_solve, separate, *args, **kwargs):

        functions = [(begin, cp.cpCollisionBeginFunc)
                    , (pre_solve, cp.cpCollisionPreSolveFunc)
                    , (post_solve, cp.cpCollisionPostSolveFunc)
                    , (separate, cp.cpCollisionSeparateFunc)]

        _functions = []

        for func, func_type in functions:
            if func is None:
                _f = ct.cast(ct.POINTER(ct.c_int)(), func_type)
            else:
                _f = self._get_cf1(func, func_type, *args, **kwargs)
            _functions.append(_f)
        return _functions

    def remove_collision_handler(self, a, b):
        """Remove a collision handler for a given collision type pair.

        :Parameters:
            a : int
                Collision type of the first shape
            b : int
                Collision type of the second shape
        """
        if (a, b) in self._handlers:
            del self._handlers[(a, b)]
        cp.cpSpaceRemoveCollisionHandler(self._space, a, b)


    def _get_cf1(self, func, function_type, *args, **kwargs):
        def cf(_arbiter, _space, _data):
            arbiter = Arbiter(_arbiter, self)
            return func(self, arbiter, *args, **kwargs)
        return function_type(cf)


    def add_post_step_callback(self, callback_function, obj, *args, **kwargs):
        """Add a function to be called last in the next simulation step.

        Post step callbacks are registered as a function and an object used as
        a key. You can only register one post step callback per object.

        This function was more useful with earlier versions of pymunk where
        you weren't allowed to use the add and remove methods on the space
        during a simulation step. But this function is still available for
        other uses and to keep backwards compatibility.

        .. Note::
            If you remove a shape from the callback it will trigger the
            collision handler for the 'separate' event if it the shape was
            touching when removed.

        :Parameters:
            callback_function : ``func(obj, *args, **kwargs)``
                The callback function.
            obj : Any object
                This object is used as a key, you can only have one callback
                for a single object. It is passed on to the callback function.
            args
                Optional parameters passed to the callback function.
            kwargs
                Optional keyword parameters passed on to the callback function.

        :Return:
            True if key was not previously added, False otherwise
        """

        if obj in self._post_callback_keys:
            return False

        def cf(_space, key, data):
            callback_function(obj, *args, **kwargs)

        f = cp.cpPostStepFunc(cf)

        self._post_last_callback_key += 1
        self._post_callback_keys[obj] = self._post_last_callback_key
        self._post_step_callbacks[obj] = f

        key = self._post_callback_keys[obj]
        return bool(cp.cpSpaceAddPostStepCallback(self._space, f, key, None))

    def point_query(self, point, layers = -1, group = 0):
        """Query space at point filtering out matches with the given layers
        and group. Return a list of found shapes.

        If you don't want to filter out any matches, use -1 for the layers
        and 0 as the group.

        :Parameters:
            point : (x,y) or `Vec2d`
                Define where to check for collision in the space.
            layers : int
                Only pick shapes matching the bit mask. i.e.
                (layers & shape.layers) != 0
            group : int
                Only pick shapes not in this group.

        """
        self.__query_hits = []
        def cf(_shape, data):
            shape = self._get_shape(_shape)
            self.__query_hits.append(shape)
        f = cp.cpSpacePointQueryFunc(cf)
        cp.cpSpacePointQuery(self._space, point, layers, group, f, None)

        return self.__query_hits

    def point_query_first(self, point, layers = -1, group = 0):
        """Query space at point and return the first shape found matching the
        given layers and group. Returns None if no shape was found.

        :Parameters:
            point : (x,y) or `Vec2d`
                Define where to check for collision in the space.
            layers : int
                Only pick shapes matching the bit mask. i.e.
                (layers & shape.layers) != 0
            group : int
                Only pick shapes not in this group.
        """
        _shape = cp.cpSpacePointQueryFirst(self._space, point, layers, group)
        return self._get_shape(_shape)

    def _get_shape(self, _shape):
        if not bool(_shape):
            return None
        hashid_private = _shape.contents.hashid_private
        #return self._shapes[hashid_private]
        if hashid_private in self._shapes:
            shape = self._shapes[hashid_private]
        elif hashid_private in self._removed_shapes:
            shape = self._removed_shapes[hashid_private]
        return shape

    def nearest_point_query(self, point, max_distance, layers = -1, group = 0):
        """Query space at point filtering out matches with the given layers
        and group. Return a list of all shapes within max_distance of the point.

        If you don't want to filter out any matches, use -1 for the layers
        and 0 as the group.

        :Parameters:
            point : (x,y) or `Vec2d`
                Define where to check for collision in the space.
            max_distance : int
                Maximumm distance of shape from point
            layers : int
                Only pick shapes matching the bit mask. i.e.
                (layers & shape.layers) != 0
            group : int
                Only pick shapes not in this group.

        :Return:
            [dict(shape=`Shape`, distance = distance, point = Vec2d)]
        """
        self.__query_hits = []
        def cf(_shape, distance, point, data):
            shape = self._get_shape(_shape)
            self.__query_hits.append(dict(shape=shape, distance=distance, point=Vec2d(point)))
        f = cp.cpSpaceNearestPointQueryFunc(cf)
        cp.cpSpaceNearestPointQuery(self._space, point, max_distance, layers, group, f, None)

        return self.__query_hits

    def nearest_point_query_nearest(self, point, max_distance, layers = -1, group = 0):
        """Query space at point filtering out matches with the given layers
        and group. Return nearest of all shapes within max_distance of the
        point.

        If you don't want to filter out any matches, use -1 for the layers
        and 0 as the group.

        :Parameters:
            point : (x,y) or `Vec2d`
                Define where to check for collision in the space.
            max_distance : int
                Maximumm distance of shape from point
            layers : int
                Only pick shapes matching the bit mask. i.e.
                (layers & shape.layers) != 0
            group : int
                Only pick shapes not in this group.

        :Return:
            dict(shape=`Shape`, distance = distance, point = Vec2d)
        """
        info = cp.cpNearestPointQueryInfo()
        info_p = ct.POINTER(cp.cpNearestPointQueryInfo)(info)
        _shape = cp.cpSpaceNearestPointQueryNearest(self._space, point, max_distance, layers, group, info_p)
        shape = self._get_shape(_shape)
        if shape != None:
            return dict(shape=shape, point=info.p, distance=info.d)
        return None



    def segment_query(self, start, end, layers = -1, group = 0):
        """Query space along the line segment from start to end filtering out
        matches with the given layers and group.

        Segment queries are like ray casting, but because pymunk uses a
        spatial hash to process collisions, it cannot process infinitely
        long queries like a ray. In practice this is still very fast and you
        don't need to worry too much about the performance as long as you
        aren't using very long segments for your queries.

        :Return:
            [`SegmentQueryInfo`] - One SegmentQueryInfo object for each hit.
        """

        self.__query_hits = []
        def cf(_shape, t, n, data):
            shape = self._get_shape(_shape)
            info = SegmentQueryInfo(shape, start, end, t, n)
            self.__query_hits.append(info)

        f = cp.cpSpaceSegmentQueryFunc(cf)
        cp.cpSpaceSegmentQuery(self._space, start, end, layers, group, f, None)

        return self.__query_hits

    def segment_query_first(self, start, end, layers = -1, group = 0):
        """Query space along the line segment from start to end filtering out
        matches with the given layers and group. Only the first shape
        encountered is returned and the search is short circuited.
        Returns None if no shape was found.
        """
        info = cp.cpSegmentQueryInfo()
        info_p = ct.POINTER(cp.cpSegmentQueryInfo)(info)
        _shape = cp.cpSpaceSegmentQueryFirst(self._space, start, end, layers, group, info_p)
        shape = self._get_shape(_shape)
        if shape != None:
            return SegmentQueryInfo(shape, start, end, info.t, info.n)
        return None

    def bb_query(self, bb, layers = -1, group = 0):
        """Perform a fast rectangle query on the space.

        Only the shape's bounding boxes are checked for overlap, not their
        full shape. Returns a list of shapes.
        """

        self.__query_hits = []
        def cf(_shape, data):

            shape = self._get_shape(_shape)
            self.__query_hits.append(shape)
        f = cp.cpSpaceBBQueryFunc(cf)
        cp.cpSpaceBBQuery(self._space, bb._bb, layers, group, f, None)
        return self.__query_hits


    def shape_query(self, shape):
        """Query a space for any shapes overlapping the given shape

        Returns a list of shapes.
        """

        self.__query_hits = []
        def cf(_shape, points, data):

            shape = self._get_shape(_shape)
            self.__query_hits.append(shape)
        f = cp.cpSpaceShapeQueryFunc(cf)
        cp.cpSpaceShapeQuery(self._space, shape._shape, f, None)
        return self.__query_hits

class Body(object):
    """A rigid body

    * Use forces to modify the rigid bodies if possible. This is likely to be
      the most stable.
    * Modifying a body's velocity shouldn't necessarily be avoided, but
      applying large changes can cause strange results in the simulation.
      Experiment freely, but be warned.
    * Don't modify a body's position every step unless you really know what
      you are doing. Otherwise you're likely to get the position/velocity badly
      out of sync.
    """
    def __init__(self, mass=None, moment=None):
        """Create a new Body

        To create a static body, pass in None for mass and moment.
        """
        if mass == None and moment == None:
            self._body = cp.cpBodyNewStatic()
        else:
            self._body = cp.cpBodyNew(mass, moment)
        self._bodycontents = self._body.contents
        self._position_callback = None # To prevent the gc to collect the callbacks.
        self._velocity_callback = None # To prevent the gc to collect the callbacks.

        self._space = None # Weak ref to the space holding this body (if any)

        self._constraints = WeakSet() # weak refs to any constraints attached
        self._shapes = WeakSet() # weak refs to any shapes attached

    def __del__(self):
        try:
            cp.cpBodyFree(self._body)
        except:
            pass

    def _set_mass(self, mass):
        cp.cpBodySetMass(self._body, mass)
    def _get_mass(self):
        return self._bodycontents.m
    mass = property(_get_mass, _set_mass)

    def _set_moment(self, moment):
        cp.cpBodySetMoment(self._body, moment)
    def _get_moment(self):
        return self._bodycontents.i
    moment = property(_get_moment, _set_moment)

    def _set_angle(self, angle):
        cp.cpBodySetAngle(self._body, angle)
    def _get_angle(self):
        return self._bodycontents.a
    angle = property(_get_angle, _set_angle,
        doc="""The rotation of the body.

        .. Note::
            If you get small/no changes to the angle when for example a
            ball is "rolling" down a slope it might be because the Circle shape
            attached to the body or the slope shape does not have any friction
            set.""")

    def _get_rotation_vector(self):
        return self._bodycontents.rot
    rotation_vector = property(_get_rotation_vector)

    def _set_torque(self, t):
        self._bodycontents.t = t
    def _get_torque(self):
        return self._bodycontents.t
    torque = property(_get_torque, _set_torque)

    def _set_position(self, pos):
        self._bodycontents.p = pos
    def _get_position(self):
        return self._bodycontents.p
    position = property(_get_position, _set_position)

    def _set_velocity(self, vel):
        self._bodycontents.v = vel
    def _get_velocity(self):
        return self._bodycontents.v
    velocity = property(_get_velocity, _set_velocity)

    def _set_velocity_limit(self, vel):
        self._bodycontents.v_limit = vel
    def _get_velocity_limit(self):
        return self._bodycontents.v_limit
    velocity_limit = property(_get_velocity_limit, _set_velocity_limit)

    def _set_angular_velocity(self, w):
        self._bodycontents.w = w
    def _get_angular_velocity(self):
        return self._bodycontents.w
    angular_velocity = property(_get_angular_velocity, _set_angular_velocity)

    def _set_angular_velocity_limit(self, w):
        self._bodycontents.w_limit = w
    def _get_angular_velocity_limit(self):
        return self._bodycontents.w_limit
    angular_velocity_limit = property(_get_angular_velocity_limit, _set_angular_velocity_limit)


    def _set_force(self, f):
        self._bodycontents.f = f
    def _get_force(self):
        return self._bodycontents.f
    force = property(_get_force, _set_force)

    def _set_velocity_func(self, func):
        """The velocity callback function. The velocity callback function
        is called each time step, and can be used to set a body's velocity.

            ``func(body, gravity, damping, dt) -> None``

            Callback Parameters
                body : `Body`
                    Body that should have its velocity calculated
                gravity : `Vec2d`
                    The gravity vector
                damping : float
                    The damping
                dt : float
                    Delta time since last step.
        """

        def _impl(_, gravity, damping, dt):
            return func(self, gravity, damping, dt)

        self._velocity_callback = cp.cpBodyVelocityFunc(_impl)
        self._bodycontents.velocity_func = self._velocity_callback
    velocity_func = property(fset=_set_velocity_func,
        doc=_set_velocity_func.__doc__)

    def _set_position_func(self, func):
        """The position callback function. The position callback function
        is called each time step and can be used to update the body's position.

            ``func(body, dt) -> None``

            Callback Parameters
                body : `Body`
                    Body that should have its velocity calculated
                dt : float
                    Delta time since last step.
        """

        def _impl(_, dt):
            func(self, dt)
            return 0
        self._position_callback = cp.cpBodyPositionFunc(_impl)
        self._bodycontents.position_func = self._position_callback
    position_func = property(fset=_set_position_func,
        doc=_set_position_func.__doc__)

    def _get_kinetic_energy(self):
        #todo: use ffi method
        #return cp._cpBodyKineticEnergy(self._body)

        vsq = self.velocity.dot(self.velocity)
        wsq = self.angular_velocity * self.angular_velocity
        return (vsq*self.mass if vsq else 0.) + (wsq*self.moment if wsq else 0.)

    kinetic_energy = property(_get_kinetic_energy,
        doc="""Get the kinetic energy of a body.""")


    @staticmethod
    def update_velocity(body, gravity, damping, dt):
        """Default rigid body velocity integration function.

        Updates the velocity of the body using Euler integration.
        """
        cp.cpBodyUpdateVelocity(body._body, gravity, damping, dt)

    @staticmethod
    def update_position(body, dt):
        """Default rigid body position integration function.

        Updates the position of the body using Euler integration. Unlike the
        velocity function, it's unlikely you'll want to override this
        function. If you do, make sure you understand it's source code
        (in Chipmunk) as it's an important part of the collision/joint
        correction process.
        """
        cp.cpBodyUpdatePosition(body._body, dt)

    def apply_impulse(self, j, r=(0, 0)):
        """Apply the impulse j to body at a relative offset (important!) r
        from the center of gravity. Both r and j are in world coordinates.

        :Parameters:
            j : (x,y) or `Vec2d`
                Impulse to be applied
            r : (x,y) or `Vec2d`
                Offset the impulse with this vector
        """
        cp.cpBodyApplyImpulse(self._body, j, r)

    def reset_forces(self):
        """Zero both the forces and torques accumulated on body"""
        cp.cpBodyResetForces(self._body)

    def apply_force(self, f, r=(0, 0)):
        """Apply (accumulate) the force f on body at a relative offset
        (important!) r from the center of gravity.

        Both r and f are in world coordinates.

        :Parameters:
            f : (x,y) or `Vec2d`
                Force in world coordinates
            r : (x,y) or `Vec2d`
                Offset in world coordinates
        """
        cp.cpBodyApplyForce(self._body, f, r)

    def activate(self):
        """Wake up a sleeping or idle body."""
        cp.cpBodyActivate(self._body)

    def sleep(self):
        """Force a body to fall asleep immediately."""
        cp.cpBodySleep(self._body)

    def sleep_with_group(self, body):
        """Force a body to fall asleep immediately along with other bodies in a group.
        """
        cp.cpBodySleepWithGroup(self._body, body._body)

    def _is_sleeping(self):
        return cpffi.cpBodyIsSleeping(self._body)
    is_sleeping = property(_is_sleeping,
        doc="""Returns true if the body is sleeping.""")

    def _is_rogue(self):
        return cpffi.cpBodyIsRogue(self._body)
    is_rogue = property(_is_rogue,
        doc="""Returns true if the body has not been added to a space.""")

    def _is_static(self):
        return cpffi.cpBodyIsStatic(self._body)
    is_static = property(_is_static,
        doc="""Returns true if the body is a static body""")

    def each_arbiter(self, func, *args, **kwargs):
        """Run func on each of the arbiters on this body.

            ``func(arbiter, *args, **kwargs) -> None``

            Callback Parameters
                arbiter : `Arbiter`
                    The Arbiter
                args
                    Optional parameters passed to the callback function.
                kwargs
                    Optional keyword parameters passed on to the callback function.

        .. warning::

            Do not hold on to the Arbiter after the callback!
        """

        def impl(body, _arbiter, _):
            arbiter = Arbiter(_arbiter, self._space)
            func(arbiter, *args, **kwargs)
            return 0
        f = cp.cpBodyArbiterIteratorFunc(impl)
        cp.cpBodyEachArbiter(self._body, f, None)

    def _get_constraints(self):
        return set(self._constraints)

    constraints = property(_get_constraints,
        doc="""Get the constraints this body is attached to.""")

    def _get_shapes(self):
        return set(self._shapes)

    shapes = property(_get_shapes,
        doc="""Get the shapes attached to this body.""")

    def local_to_world(self, v):
        """Convert body local coordinates to world space coordinates

        :Parameters:
            v : (x,y) or `Vec2d`
                Vector in body local coordinates
        """
        return cpffi.cpBodyLocal2World(self._body, v)

    def world_to_local(self, v):
        """Convert world space coordinates to body local coordinates

        :Parameters:
            v : (x,y) or `Vec2d`
                Vector in world space coordinates
        """
        return cpffi.cpBodyWorld2Local(self._body, v)



class Shape(object):
    """Base class for all the shapes.

    You usually dont want to create instances of this class directly but use
    one of the specialized shapes instead.
    """
    def __init__(self, shape=None):
        self._shape = shape
        self._shapecontents = self._shape.contents
        self._body = shape.body
        self.data = None

    def __del__(self):
        try:
            cp.cpShapeFree(self._shape)
        except:
            pass

    def _get_hashid_private(self):
        return self._shapecontents.hashid_private
    _hashid_private = property(_get_hashid_private)

    def _get_sensor(self):
        return bool(self._shapecontents.sensor)
    def _set_sensor(self, is_sensor):
        self._shapecontents.sensor = is_sensor
    sensor = property(_get_sensor, _set_sensor,
        doc="""A boolean value if this shape is a sensor or not. Sensors only
        call collision callbacks, and never generate real collisions.""")

    def _get_collision_type(self):
        return self._shapecontents.collision_type
    def _set_collision_type(self, t):
        self._shapecontents.collision_type = t
    collision_type = property(_get_collision_type, _set_collision_type,
        doc="""User defined collision type for the shape. See
        add_collisionpair_func function for more information on when to use
        this property""")

    def _get_group(self):
        return self._shapecontents.group
    def _set_group(self, group):
        self._shapecontents.group = group
    group = property(_get_group, _set_group,
        doc="""Shapes in the same non-zero group do not generate collisions.
        Useful when creating an object out of many shapes that you don't want
        to self collide. Defaults to 0""")

    def _get_layers(self):
        return self._shapecontents.layers
    def _set_layers(self, layers):
        self._shapecontents.layers = layers
    layers = property(_get_layers, _set_layers,
        doc="""Shapes only collide if they are in the same bit-planes.
        i.e. (a.layers & b.layers) != 0. By default, a shape occupies all
        32 bit-planes, i.e. layers == -1""")

    def _get_elasticity(self):
        return self._shapecontents.e
    def _set_elasticity(self, e):
        self._shapecontents.e = e
    elasticity = property(_get_elasticity, _set_elasticity,
        doc="""Elasticity of the shape. A value of 0.0 gives no bounce,
        while a value of 1.0 will give a 'perfect' bounce. However due to
        inaccuracies in the simulation using 1.0 or greater is not
        recommended.""")

    def _get_friction(self):
        return self._shapecontents.u
    def _set_friction(self, u):
        self._shapecontents.u = u
    friction = property(_get_friction, _set_friction,
        doc="""Friction coefficient. pymunk uses the Coulomb friction model, a
        value of 0.0 is frictionless.

        A value over 1.0 is perfectly fine.

        Some real world example values from wikipedia (Remember that
        it is what looks good that is important, not the exact value).

        ==============  ======  ========
        Material        Other   Friction
        ==============  ======  ========
        Aluminium       Steel   0.61
        Copper          Steel   0.53
        Brass           Steel   0.51
        Cast iron       Copper  1.05
        Cast iron       Zinc    0.85
        Concrete (wet)  Rubber  0.30
        Concrete (dry)  Rubber  1.0
        Concrete        Wood    0.62
        Copper          Glass   0.68
        Glass           Glass   0.94
        Metal           Wood    0.5
        Polyethene      Steel   0.2
        Steel           Steel   0.80
        Steel           Teflon  0.04
        Teflon (PTFE)   Teflon  0.04
        Wood            Wood    0.4
        ==============  ======  ========
        """)

    def _get_surface_velocity(self):
        return self._shapecontents.surface_v
    def _set_surface_velocity(self, surface_v):
        self._shapecontents.surface_v = surface_v
    surface_velocity = property(_get_surface_velocity, _set_surface_velocity,
        doc="""The surface velocity of the object. Useful for creating
        conveyor belts or players that move around. This value is only used
        when calculating friction, not resolving the collision.""")

    def _get_body(self):
        return self._body
    def _set_body(self, body):
        if self._body != None:
            self._body._shapes.remove(self)
        if body != None:
            body._shapes.add(self)
            self._shapecontents.body = body._body
        else:
            self._shapecontents.body = None

        self._body = body

    body = property(_get_body, _set_body,
        doc="""The body this shape is attached to. Can be set to None to
        indicate that this shape doesnt belong to a body.""")

    def update(self, position, rotation_vector):
        """Update, cache and return the bounding box of a shape with an
        explicit transformation.

        Useful if you have a shape without a body and want to use it for
        querying.
        """
        return BB(cp.cpShapeUpdate(self._shape, position, rotation_vector))

    def cache_bb(self):
        """Update and returns the bouding box of this shape"""
        return BB(cp.cpShapeCacheBB(self._shape))

    def _get_bb(self):
        return BB(cpffi.cpShapeGetBB(self._shape))

    bb = property(_get_bb, doc="""The bounding box of the shape.
    Only guaranteed to be valid after Shape.cache_bb() or Space.step() is
    called. Moving a body that a shape is connected to does not update it's
    bounding box. For shapes used for queries that aren't attached to bodies,
    you can also use Shape.update().
    """)

    def point_query(self, p):
        """Check if the given point lies within the shape."""
        return bool(cp.cpShapePointQuery(self._shape, p))

    def segment_query(self, start, end):
        """Check if the line segment from start to end intersects the shape.

        Return either SegmentQueryInfo object or None
        """
        info = cp.cpSegmentQueryInfo()
        info_p = ct.POINTER(cp.cpSegmentQueryInfo)(info)
        r = cp.cpShapeSegmentQuery(self._shape, start, end, info_p)
        if bool(r):
            return SegmentQueryInfo(self, start, end, info.t, info.n)
        else:
            return None



class Circle(Shape):
    """A circle shape defined by a radius

    This is the fastest and simplest collision shape
    """
    def __init__(self, body, radius, offset = (0, 0)):
        """body is the body attach the circle to, offset is the offset from the
        body's center of gravity in body local coordinates.

        It is legal to send in None as body argument to indicate that this
        shape is not attached to a body.
        """
        self._body = body
        body_body = None if body is None else body._body
        if body != None:
            body._shapes.add(self)

        self._shape = cp.cpCircleShapeNew(body_body, radius, offset)
        self._shapecontents = self._shape.contents
        self._cs = ct.cast(self._shape, ct.POINTER(cp.cpCircleShape))


    def unsafe_set_radius(self, r):
        """Unsafe set the radius of the circle.

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        cp.cpCircleShapeSetRadius(self._shape, r)

    def _get_radius(self):
        return cp.cpCircleShapeGetRadius(self._shape)
    radius = property(_get_radius, doc="""The Radius of the circle""")

    def unsafe_set_offset(self, o):
        """Unsafe set the offset of the circle.

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        cp.cpCircleShapeSetOffset(self._shape, o)

    def _get_offset (self):
        return cp.cpCircleShapeGetOffset(self._shape)
    offset = property(_get_offset, doc="""Offset. (body space coordinates)""")


class Segment(Shape):
    """A line segment shape between two points

    This shape can be attached to moving bodies, but don't currently generate
    collisions with other line segments. Can be beveled in order to give it a
    thickness.

    It is legal to send in None as body argument to indicate that this
    shape is not attached to a body.
    """
    def __init__(self, body, a, b, radius):
        """Create a Segment

        :Parameters:
            body : `Body`
                The body to attach the segment to
            a : (x,y) or `Vec2d`
                The first endpoint of the segment
            b : (x,y) or `Vec2d`
                The second endpoint of the segment
            radius : float
                The thickness of the segment
        """
        self._body = body
        body_body = None if body is None else body._body
        if body != None:
            body._shapes.add(self)
        self._shape = cp.cpSegmentShapeNew(body_body, a, b, radius)
        self._shapecontents = self._shape.contents

    def unsafe_set_a(self, a):
        """Set the first of the two endpoints for this segment

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.a = a
    def _get_a(self):
        return ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.a
    a = property(_get_a,
        doc="""The first of the two endpoints for this segment""")

    def unsafe_set_b(self, b):
        """Set the second of the two endpoints for this segment

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.b = b
    def _get_b(self):
        return ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.b
    b = property(_get_b,
        doc="""The second of the two endpoints for this segment""")

    def unsafe_set_radius(self, r):
        """Set the radius of the segment

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.r = r
    def _get_radius(self):
        return ct.cast(self._shape, ct.POINTER(cp.cpSegmentShape)).contents.r
    radius = property(_get_radius,
        doc="""The radius/thickness of the segment""")


class Poly(Shape):
    """A convex polygon shape

    Slowest, but most flexible collision shape.

    It is legal to send in None as body argument to indicate that this
    shape is not attached to a body.
    """
    def __init__(self, body, vertices, offset=(0, 0), radius=0):
        """Create a polygon

            body : `Body`
                The body to attach the poly to
            vertices : [(x,y)] or [`Vec2d`]
                Define a convex hull of the polygon with a counterclockwise
                winding.
            offset : (x,y) or `Vec2d`
                The offset from the body's center of gravity in body local
                coordinates.
            radius : int
                Set the radius of the poly shape.
        """

        self._body = body
        self.offset = offset
        self._set_verts(vertices)

        body_body = None if body is None else body._body
        if body != None:
            body._shapes.add(self)
        self._shape = cp.cpPolyShapeNew2(body_body, len(vertices), self.verts, offset, radius)
        self._shapecontents = self._shape.contents

    def unsafe_set_radius(self, radius):
        """Unsafe set the radius of the poly.

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        cp.cpPolyShapeSetRadius(self._shape, radius)

    def _get_radius(self):
        return cp.cpPolyShapeGetRadius(self._shape)
    radius = property(_get_radius,
        doc="""The radius of the poly shape. Extends the poly in all
        directions with the given radius""")

    def _set_verts(self, vertices):
        auto_order_vertices = True
        self.verts = (Vec2d * len(vertices))
        self.verts = self.verts(Vec2d(0, 0))

        i_vs = enumerate(vertices)
        if auto_order_vertices and not u.is_clockwise(vertices):
            i_vs = zip(range(len(vertices)-1, -1, -1), vertices)

        for (i, vertex) in i_vs:
            self.verts[i].x = vertex[0]
            self.verts[i].y = vertex[1]

    @staticmethod
    def create_box(body, size=(10,10), offset=(0,0), radius=0):
        """Convenience function to create a box centered around the body position.

        The size is given as as (w,h) tuple.
        """
        x,y = size[0]*.5,size[1]*.5
        vs = [(-x,-y),(-x,y),(x,y),(x,-y)]

        return Poly(body, vs, offset, radius)


    def get_vertices(self):
        """Get the vertices in world coordinates for the polygon

        :return: [`Vec2d`] in world coords
        """
        #shape = ct.cast(self._shape, ct.POINTER(cp.cpPolyShape))
        #num = shape.contents.numVerts
        #verts = shape.contents.verts
        points = []
        rv = self._body.rotation_vector
        bp = self._body.position
        vs = self.verts
        o = self.offset
        for i in range(len(vs)):
            p = (vs[i]+o).cpvrotate(rv)+bp
            points.append(Vec2d(p))

        return points

    def unsafe_set_vertices(self, vertices, offset=(0, 0)):
        """Unsafe set the vertices of the poly.

        .. note::
            This change is only picked up as a change to the position
            of the shape's surface, but not it's velocity. Changing it will
            not result in realistic physical behavior. Only use if you know
            what you are doing!
        """
        self._set_verts(vertices)
        cp.cpPolyShapeSetVerts(self._shape, len(vertices), self.verts, offset)


class SegmentQueryInfo(object):
    """Segment queries return more information than just a simple yes or no,
    they also return where a shape was hit and it's surface normal at the hit
    point. This object hold that information.
    """
    def __init__(self, shape, start, end, t, n):
        """You shouldn't need to initialize SegmentQueryInfo objects on your
        own.
        """
        self._shape = shape
        self._t = t
        self._n = n
        self._start = start
        self._end = end

    def __repr__(self):
        return "SegmentQueryInfo(%s, %s, %s, %s, %s)" % (self.shape, self._start, self._end, self.t, self.n)

    shape = property(lambda self: self._shape
        , doc = """Shape that was hit""")

    t = property(lambda self: self._t
        , doc = """Distance along query segment, will always be in the range [0, 1]""")

    n = property(lambda self: self._n
        , doc = """Normal of hit surface""")

    def get_hit_point(self):
        """Return the hit point in world coordinates where the segment first
        intersected with the shape
        """
        #todo: use ffi function
        return Vec2d(self._start).interpolate_to(self._end, self.t)

    def get_hit_distance(self):
        """Return the absolute distance where the segment first hit the shape
        """
        #todo: use ffi function
        return Vec2d(self._start).get_distance(self._end) * self.t


def moment_for_circle(mass, inner_radius, outer_radius, offset=(0, 0)):
    """Calculate the moment of inertia for a circle"""
    return cp.cpMomentForCircle(mass, inner_radius, outer_radius, offset)

def moment_for_segment(mass, a, b):
    """Calculate the moment of inertia for a segment"""
    return cp.cpMomentForSegment(mass, a, b)

def moment_for_poly(mass, vertices,  offset=(0, 0)):
    """Calculate the moment of inertia for a polygon"""
    verts = (Vec2d * len(vertices))
    verts = verts(Vec2d(0, 0))
    for (i, vertex) in enumerate(vertices):
        verts[i].x = vertex[0]
        verts[i].y = vertex[1]
    return cp.cpMomentForPoly(mass, len(verts), verts, offset)

def moment_for_box(mass, width, height):
    """Calculate the momentn of inertia for a box"""
    return cp.cpMomentForBox(mass, width, height)

def reset_shapeid_counter():
    """Reset the internal shape counter

    pymunk keeps a counter so that every new shape is given a unique hash
    value to be used in the spatial hash. Because this affects the order in
    which the collisions are found and handled, you should reset the shape
    counter every time you populate a space with new shapes. If you don't,
    there might be (very) slight differences in the simulation.
    """
    cp.cpResetShapeIdCounter()


class Contact(object):
    """Contact information"""
    def __init__(self, _contact):
        """Initialize a Contact object from the Chipmunk equivalent struct

        .. note::
            You should never need to create an instance of this class directly.
        """
        self._point = _contact.point
        self._normal = _contact.normal
        self._dist = _contact.dist
        #self._contact = contact

    def __repr__(self):
        return "Contact(p: %s, n: %s, d: %s)" % (self.position, self.normal, self.distance)

    def _get_position(self):
        return self._point
    position = property(_get_position, doc="""Contact position""")

    def _get_normal(self):
        return self._normal
    normal = property(_get_normal, doc="""Contact normal""")

    def _get_distance(self):
        return self._dist
    distance = property(_get_distance, doc="""Penetration distance""")



class Arbiter(object):
    """Arbiters are collision pairs between shapes that are used with the
    collision callbacks.

    .. Warning::
        Because arbiters are handled by the space you should never
        hold onto a reference to an arbiter as you don't know when it will be
        destroyed! Use them within the callback where they are given to you
        and then forget about them or copy out the information you need from
        them.
    """
    def __init__(self, _arbiter, space):
        """Initialize an Arbiter object from the Chipmunk equivalent struct
        and the Space.

        .. note::
            You should never need to create an instance of this class directly.
        """

        self._arbiter = _arbiter
        self._arbitercontents = self._arbiter.contents
        self._space = space
        self._contacts = None # keep a lazy loaded cache of converted contacts

    def _get_contacts(self):
        point_set = cp.cpArbiterGetContactPointSet(self._arbiter)

        if self._contacts is None:
            self._contacts = []
            for i in range(point_set.count):
                self.contacts.append(Contact(point_set.points[i]))
        return self._contacts
    contacts = property(_get_contacts,
        doc="""Information on the contact points between the objects. Return [`Contact`]""")

    def _get_shapes(self):
        shapeA_p = ct.POINTER(cp.cpShape)()
        shapeB_p = ct.POINTER(cp.cpShape)()

        cpffi.cpArbiterGetShapes(self._arbiter, shapeA_p, shapeB_p)

        a, b = self._space._get_shape(shapeA_p), self._space._get_shape(shapeB_p)
        return a, b

    shapes = property(_get_shapes,
        doc="""Get the shapes in the order that they were defined in the
        collision handler associated with this arbiter""")

    def _get_elasticity(self):
        return self._arbiter.contents.e
    def _set_elasticity(self, elasticity):
        self._arbiter.contents.e = elasticity
    elasticity = property(_get_elasticity, _set_elasticity,
        doc="""Elasticity""")

    def _get_friction(self):
        return self._arbiter.contents.u
    def _set_friction(self, friction):
        self._arbiter.contents.u = friction
    friction = property(_get_friction, _set_friction, doc="""Friction""")

    def _get_surface_velocity(self):
        return self._arbiter.contents.surface_vr
    surface_velocity = property(_get_surface_velocity,
        doc="""Used for surface_v calculations, implementation may change""")

    def _get_total_impulse(self):
        return cp.cpArbiterTotalImpulse(self._arbiter)
    total_impulse = property(_get_total_impulse,
        doc="""Returns the impulse that was applied this step to resolve the
        collision.

        This property should only be called from a post-solve, post-step""")

    def _get_total_impulse_with_friction(self):
        return cp.cpArbiterTotalImpulseWithFriction(self._arbiter)
    total_impulse_with_friction = property(_get_total_impulse_with_friction,
        doc="""Returns the impulse with friction that was applied this step to
        resolve the collision.

        This property should only be called from a post-solve, post-step""")

    def _get_total_ke(self):
        return cp.cpArbiterTotalKE(self._arbiter)
    total_ke = property(_get_total_ke,
        doc="""The amount of energy lost in a collision including static, but
        not dynamic friction.

        This property should only be called from a post-solve, post-step""")

    def _get_stamp(self):
        return self._arbiter.contents.stamp
    stamp = property(_get_stamp,
        doc="""Time stamp of the arbiter. (from the space)""")

    def _get_is_first_contact(self):
        return bool(cpffi.cpArbiterIsFirstContact(self._arbiter))
    is_first_contact = property(_get_is_first_contact,
        doc="""Returns true if this is the first step that an arbiter existed.
        You can use this from preSolve and postSolve to know if a collision
        between two shapes is new without needing to flag a boolean in your
        begin callback.""")



class BB(object):
    """Simple bounding box class. Stored as left, bottom, right, top values."""
    def __init__(self, *args):
        """Create a new instance of a bounding box. Can be created with zero
        size with bb = BB() or with four args defining left, bottom, right and
        top: bb = BB(left, bottom, right, top)
        """
        if len(args) == 0:
            self._bb = cp.cpBB()
        elif len(args) == 1:
            self._bb = args[0]
        else:
            self._bb = cpffi.cpBBNew(args[0], args[1], args[2], args[3])

    def __repr__(self):
        return 'BB(%s, %s, %s, %s)' % (self.left, self.bottom, self.right, self.top)

    def __eq__(self, other):
        return self.left == other.left and self.bottom == other.bottom and \
            self.right == other.right and self.top == other.top

    def __ne__(self, other):
        return not self.__eq__(other)

    def intersects(self, other):
        """Returns true if the bounding boxes intersect"""
        return bool(cpffi.cpBBIntersects(self._bb, other._bb))

    def contains(self, other):
        """Returns true if bb completley contains the other bb"""
        return bool(cpffi.cpBBContainsBB(self._bb, other._bb))

    def contains_vect(self, v):
        """Returns true if this bb contains the vector v"""
        return bool(cpffi.cpBBContainsVect(self._bb, v))

    def merge(self, other):
        """Return the minimal bounding box that contains both this bb and the
        other bb
        """
        return BB(cpffi.cpBBMerge(self._bb, other._bb))

    def expand(self, v):
        """Return the minimal bounding box that contans both this bounding box
        and the vector v
        """
        return BB(cpffi.cpBBExpand(self._bb, v))

    left = property(lambda self: self._bb.l)
    bottom = property(lambda self: self._bb.b)
    right = property(lambda self: self._bb.r)
    top = property(lambda self: self._bb.t)

    def clamp_vect(self, v):
        """Returns a copy of the vector v clamped to the bounding box"""
        return cpffi.cpBBClampVect(self._bb, v)

    def wrap_vect(self, v):
        """Returns a copy of v wrapped to the bounding box.
        That is, BB(0,0,10,10).wrap_vect((5,5)) == Vec2d(10,10)
        """
        return cp.cpBBWrapVect(self._bb, v)


#del cp, ct, u

