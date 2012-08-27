Website Generator
=================

This directory contains a generator for the perentie website. In short, run::

	$ ./generate_site.sh

and then upload the content of the 'out' directory to the web. Documentation is
generated from the contents of the project doc directory. See 'Adding Pages' for
details.

You can safely ignore warnings about missing files/directories.

Requirements
------------

You must have rst2html installed to build the website.


Adding pages
------------

To add a page to the site, create the page body in a html or reStructuredText
file (.rst) in the project doc directory or in the www/pages (to prevent
polution of the documentation) directory. The nav bar and boilerplate HTML will
be added around this content.

Page title
``````````
To specify the page title, place a comment formatted like so:

HTML::

	<!-- TITLE:Page title -->

reStructuredText::

	.. TITLE:Page title

Note: The spacing is significant.

Menu Selection
``````````````
To specify which menu item should appear selected, add a similar comment such as

HTML::

	<!-- MENU_ITEM:Menu item -->

reStructuredText::

	.. MENU_ITEM:Menu item

Where "Menu item" is the menu item text.

Substitutions
`````````````
The following strings will be substituted in the output::

	${VERSION} -- the current version number (from the VERSION file)
	${TITLE}   -- the current page title
	${TITLE_}  -- the current page title with a " - " appended if not empty


Menu
----
The menu is specified in menu.txt. Odd-lines contain menu text and even-lines
contain the corresponding URL the menu item should navigate to.

Including Files
---------------
Any static resources (such as images) will be copied unmodified from the
'include' directory into the website root.

Template
--------

The site is built on "Twitter Bootstrap". A the site is formed by concatenating
head1.htm, the site menu (generated from nav_item.htm and nav_item_active.htm),
head2.htm, the page body and tail.htm. These templates can be found in the
template directory.
