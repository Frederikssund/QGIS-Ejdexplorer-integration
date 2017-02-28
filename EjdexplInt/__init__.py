# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EjdexplInt
                                 A QGIS plugin
 Opens Ejdexplorer with data chosen from QGIS
                             -------------------
        begin                : 2017-02-20
        copyright            : (C) 2017 by Bo Victor Thomsen, Municipality of Frederikssund
        email                : bvtho at frederikssund dot dk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load EjdexplInt class from file EjdexplInt.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .ejdexplr_int import EjdexplInt
    return EjdexplInt(iface)
