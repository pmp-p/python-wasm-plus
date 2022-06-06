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

"""This submodule contains helper functions to help with quick prototyping 
using pymunk together with pyglet.

Intended to help with debugging and prototyping, not for actual production use
in a full application. The methods contained in this module is opinionated 
about your coordinate system and not very optimized (they use batched 
drawing, but there is probably room for optimizations still). 
"""

__version__ = "$Id$"
__docformat__ = "reStructuredText"

__all__ = ["draw"]


import math

import pyglet

import pymunk
from pymunk.vec2d import Vec2d

def draw(*objs, **kwargs):
    """Draw one or many pymunk objects. It is perfectly fine to pass in a 
    whole Space object.
    
    Objects that can be handled are:
        * pymunk.Space
        * pymunk.Segment
        * pymunk.Circle
        * pymunk.Poly
    
    If a Space is passed in all shapes in that space will be drawn. 
    Unrecognized objects will be ignored (for example if you pass in a 
    constraint).
    
    Typical usage::
    
    >>> pymunk.pyglet_util.draw(my_space)
    
    You can control the color of a Shape by setting shape.color to the color 
    you want it drawn in.
    
    >>> my_shape.color = (255, 0, 0) # will draw my_shape in red
    
    If you do not want a shape to be drawn, set shape.ignore_draw to True.
    
    >>> my_shape.ignore_draw = True
    
    (However, if you want to ignore most shapes its probably more performant 
    to only pass in those shapes that you want to be drawn to the draw method)
    
    You can optionally pass in a batch to use. Just remember that you need to 
    call draw yourself.
    
    >>> pymunk.pyglet_util.draw(my_shape, batch = my_batch)
    >>> my_batch.draw()
    
    See pyglet_util.demo.py for a full example
    
    :Param:
            objs : One or many objects to draw.
                Can be either a single object or a list like container with 
                objects.
            kwargs : You can optionally pass in a pyglet.graphics.Batch
                If a batch is given all drawing will use this batch to draw 
                on. If no batch is given a a new batch will be used for the
                drawing. Remember that if you pass in your own batch you need 
                to call draw on it yourself.
    
    """
    new_batch = False
    
    if "batch" not in kwargs:
        new_batch = True
        batch = pyglet.graphics.Batch()
    else:
        batch = kwargs["batch"]
        
    for o in objs:
        if isinstance(o, pymunk.Space):
            _draw_space(o, batch)
        elif isinstance(o, pymunk.Shape):
            _draw_shape(o, batch)
        elif isinstance(o, pymunk.Constraint):
            _draw_constraint(o, batch)
        elif hasattr(o, '__iter__'):
            for oo in o:
                draw(oo, **kwargs)
    
    if new_batch:
        batch.draw()

def _draw_space(space, batch = None):
    for s in space.shapes:
        if not (hasattr(s, "ignore_draw") and s.ignore_draw):
            _draw_shape(s, batch)
            
            
def _draw_shape(shape, batch = None):
    if isinstance(shape, pymunk.Circle):
        _draw_circle(shape, batch)
    elif isinstance(shape, pymunk.Segment):
        _draw_segment(shape, batch)
    elif isinstance(shape, pymunk.Poly):
        _draw_poly(shape, batch)
    
def _draw_circle(circle, batch = None):
    circle_center = circle.body.position + circle.offset.rotated(circle.body.angle)
    
    r = 0
    if hasattr(circle, "color"):
        color = circle.color  
    elif circle.body.is_static:
        color = (200, 200, 200)
        r = 1
    else:
        color = (255, 0, 0)
        
    #http://slabode.exofire.net/circle_draw.shtml
    num_segments = int(4 * math.sqrt(circle.radius))
    theta = 2 * math.pi / num_segments
    c = math.cos(theta)
    s = math.sin(theta)
    
    x = circle.radius # we start at angle 0
    y = 0
    
    ps = []
    
    for i in range(num_segments):
        ps += [Vec2d(circle_center.x + x, circle_center.y + y)]
        t = x
        x = c * x - s * y
        y = s * t + c * y
               
    
    if circle.body.is_static:
        mode = pyglet.gl.GL_LINES
        ps = [p for p in ps+ps[:1] for _ in (0, 1)]
    else:
        mode = pyglet.gl.GL_TRIANGLE_STRIP
        ps2 = [ps[0]]
        for i in range(1, len(ps)+1/2):
            ps2.append(ps[i])
            ps2.append(ps[-i])
        ps = ps2
    vs = []
    for p in [ps[0]] + ps + [ps[-1]]:
            vs += [p.x, p.y]
        
    c = circle_center + Vec2d(circle.radius, 0).rotated(circle.body.angle)
    cvs = [circle_center.x, circle_center.y, c.x, c.y]
        
    bg = pyglet.graphics.OrderedGroup(0)
    fg = pyglet.graphics.OrderedGroup(1)
        
    l = len(vs)/2
    if batch == None:
        pyglet.graphics.draw(l, mode,
                            ('v2f', vs),
                            ('c3B', color*l))
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                            ('v2f', cvs),
                            ('c3B', (0,0,255)*2))
    else:
        batch.add(len(vs)/2, mode, bg,
                 ('v2f', vs),
                 ('c3B', color*l))
        batch.add(2, pyglet.gl.GL_LINES, fg,
                 ('v2f', cvs),
                 ('c3B', (0,0,255)*2))
    return

def _draw_poly(poly, batch = None):
    ps = poly.get_vertices()
    
    if hasattr(poly, "color"):
        color = poly.color  
    elif poly.body.is_static:
        color = (200, 200, 200)
    else:
        color = (0, 255, 0)
        
    if poly.body.is_static:
        mode = pyglet.gl.GL_LINES
        ps = [p for p in ps+ps[:1] for _ in (0, 1)]
    else:
        mode = pyglet.gl.GL_TRIANGLE_STRIP
        ps = [ps[1],ps[2], ps[0]] + ps[3:]
        
    vs = []
    for p in [ps[0]] + ps + [ps[-1]]:
            vs += [p.x, p.y]
        
    l = len(vs)/2
    if batch == None:
        pyglet.graphics.draw(l, mode,
                            ('v2f', vs),
                            ('c3B', color*l))
    else:
        batch.add(l, mode, None,
                 ('v2f', vs),
                 ('c3B', color*l))

def _draw_segment(segment, batch = None):
    body = segment.body
    pv1 = body.position + segment.a.rotated(body.angle)
    pv2 = body.position + segment.b.rotated(body.angle)
    
    d = pv2 - pv1
    a = -math.atan2(d.x, d.y)
    dx = segment.radius * math.cos(a)
    dy = segment.radius * math.sin(a)
    
    p1 = pv1 + Vec2d(dx,dy)
    p2 = pv1 - Vec2d(dx,dy)
    p3 = pv2 + Vec2d(dx,dy)
    p4 = pv2 - Vec2d(dx,dy)
           
    vs = [i for xy in [p1,p2,p3]+[p2,p3,p4] for i in xy]
    
    if hasattr(segment, "color"):
        color = segment.color  
    elif segment.body.is_static:
        color = (200, 200, 200)
    else:
        color = (0, 0, 255)
        
    l = len(vs)/2
    if batch == None:
        pyglet.graphics.draw(l, pyglet.gl.GL_TRIANGLES,
                            ('v2f', vs),
                            ('c3B', color * l))
    else:
        batch.add(l,pyglet.gl.GL_TRIANGLES, None,
                 ('v2f', vs),
                 ('c3B', color * l))
