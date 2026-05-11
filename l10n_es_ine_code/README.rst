.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========
INE codes
=========

This module assigns Spanish INE municipality codes to ``res.city`` records and
exposes them on contacts through the selected city.

It is designed to work together with ``base_address_extend`` and
``base_location_geonames_import`` so that INE codes are linked to existing
``res.city`` / ``res.city.zip`` data, avoiding duplicated city records.

Overview
========

The module extends ``res.city`` with the following INE fields:

* INE state code
* INE province code
* INE municipality code
* INE control digit
* INE full code

The INE full code is computed as ``CPRO + CMUN``.

The matching process uses the following strategy:

1. Postal-code-based matching using the INE postal code / municipality mapping.
2. Reuse of already assigned INE codes on existing cities.
3. Fallback matching by normalized city name and province, only when the match is unambiguous.

This approach makes it possible to reuse cities imported from GeoNames and link
them to official INE municipality codes.

Usage
=====

1. Import Spanish cities and postal codes with ``base_location_geonames_import``.
2. Install this module to populate INE codes on existing ``res.city`` records.
3. Open any contact using ``city_id`` and check the INE municipality code shown
   in the address section.
4. When updated INE data is available, run the manual update wizard to simulate
   or apply the reassignment.

Notes
=====

* Some GeoNames cities may remain without INE code if they do not exist in the
  INE municipality datasets.
* Automatic updates never need to run on every module upgrade.
* A manual update wizard is provided so yearly INE dataset refreshes can be
  applied explicitly and safely.
* Locked cities are not modified by automatic reassignment.

Technical details
=================

This module does not create a separate INE city model.

Instead, it stores INE data directly on ``res.city`` and exposes the computed
INE full code on ``res.partner`` through the related ``city_id`` field.

This avoids duplicate city catalogs and keeps compatibility with the address
models provided by ``base_address_extend``.

Credits
=======

Authors
-------

* Moval Agroingeniería S.L.
* Odoo Community Association (OCA)

Contributors
------------

* Samuel Fernández Verdú <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>
* Guillermo Amante <gamante@moval.es>
* Your Name <your@email.com>

Maintainers
-----------

This module is maintained by the Odoo Community Association (OCA).

.. image:: https://odoo-community.org/logo.png
   :target: https://odoo-community.org
   :alt: Odoo Community Association