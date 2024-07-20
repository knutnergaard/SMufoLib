# pylint: disable=C0114
from __future__ import annotations
from typing import NamedTuple
from collections.abc import Iterator
import itertools

from fontParts.fontshell import RComponent
from fontParts.fontshell import RContour
from smufolib.objects.glyph import Glyph
from smufolib.objects.layer import Layer
from smufolib.objects.font import Font
from smufolib import error, stdUtils

TYPES = ('line', 'curve', 'qcurve')

# pylint: disable=C0103


class Point(NamedTuple):
    """Named tuple for point values.

    :param type: The :attr:`~fontParts.base.BasePoint.type` of the point.
    :param position: The :class:`~Position` of the point.
    :param contourIndex: The :attr:`~fontParts.base.BaseContour.index` of
        the point's parent contour.

    """
    type: str
    position: Position
    contourIndex: int


class Position(NamedTuple):
    """Named tuple for position values.

    :param x: The horizontal position of the point.
    :param y: The vertical position of the point.

    """
    x: int | float
    y: int | float


def getPoints(obj: Glyph | tuple[Glyph, ...] | Layer | Font,
              types: str | tuple[str, ...] = TYPES
              ) -> Iterator[Point]:
    """Get points from font-related object.

    This function simply concatinates the results
    of :func:`getContourPoints` and :func:`getCompositePoints` and
    returns the result as an :obj:`itertools.chain` object.

    :param obj: The object from which to get the points. This can be a
        single :class:`.Glyph`, a :class:`tuple` of glyph objects or any
        parent object (:class:`.Layer` or :class:`.Font`).
    :param types: The :attr:`fontParts.base.BasePoint.type` to include.
        Defaults to ``('line', 'curve', 'qcurve')``.
    :raises TypeError: If `obj` is not an accepted type.
    :raises ValueError: If `obj` items is not an accepted type.

    """
    error.validateType(obj, (tuple, Glyph, Layer, Font), 'obj')
    if isinstance(obj, tuple):
        error.validateType(obj[0], Glyph, 'obj', items=True)

    return itertools.chain(getContourPoints(obj, types),
                           getCompositePoints(obj, types))


def getContourPoints(obj: RContour | tuple[RContour, ...]
                     | Glyph | Layer | Font,
                     types: str | tuple[str, ...] = TYPES
                     ) -> Iterator[Point]:
    """Get contour points from a font-related object.

    :param obj: The object from which to get the points. This can be a
        single contour object, a :class:`tuple` of contours or any parent
        object (:class:`.Glyph`, :class:`.Layer` or :class:`.Font`).
    :param types: The :attr:`fontParts.base.BasePoint.type` to include.
        Defaults to ``('line', 'curve', 'qcurve')``.
    :raises TypeError: If `obj` is not an accepted type.

    """
    error.validateType(obj, (tuple, RContour, Glyph, Layer, Font), 'obj')
    if isinstance(obj, tuple):
        for component in obj:
            error.validateType(component, RContour, 'obj', items=True)
    if isinstance(obj, RContour):
        obj = (obj,)

    rawPoints = stdUtils.flatten(obj)

    return (Point(p.type, Position(*p.position), p.contour.index)
            for p in rawPoints if p.type in types or p.type == types)


def getCompositePoints(obj: RComponent | tuple[RComponent, ...]
                       | Glyph | Layer | Font,
                       types: str | tuple[str, ...] = TYPES
                       ) -> Iterator[Point]:
    """Get composite points from font-related object.

    The component's offset position is taken into account.

    :param obj: The object from which to get the points. This can be a
        single component object, a :class:`tuple` of components or any
        parent object (:class:`.Glyph`, :class:`.Layer`
        or :class:`.Font`).
    :param types: The :attr:`fontParts.base.BasePoint.type` to include.
        Defaults to ``('line', 'curve', 'qcurve')``.
    :raises TypeError: If `obj` is not an accepted type.

    """
    components = _getComponents(obj)

    def pointGenerator():
        for component in components:
            baseGlyph = component.font[component.baseGlyph]
            rawPoints = stdUtils.flatten(baseGlyph.contours)
            offset, index = component.offset, component.index
            for point in rawPoints:
                if point.type in types or point.type == types:
                    newPosition = stdUtils.addTuples(
                        point.position, offset)
                    yield Point(point.type, Position(*newPosition), index)

    return pointGenerator()


def _getComponents(obj: RComponent
                   | tuple[RComponent, ...] | Glyph | Layer | Font
                   ) -> tuple[RComponent, ...] | Iterator[RComponent]:
    # Get components from font-related object.
    if isinstance(obj, tuple):
        for component in obj:
            error.validateType(component, RComponent, 'obj', items=True)
        return obj
    if isinstance(obj, RComponent):
        return (obj,)
    if isinstance(obj, Glyph):
        return obj.components
    if isinstance(obj, (Layer, Font)):
        return stdUtils.flatten(g.components for g in obj)
    raise TypeError(
        error.generateTypeError(
            obj, (RComponent, tuple, Glyph, Layer, Font), 'obj'
        )
    )
