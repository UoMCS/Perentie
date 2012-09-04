#!/bin/bash

# Generates a website from the pages in the $INPUT and project documentation
# ($DOC) directory and puts the output in $OUTPUT. See the README for an
# overview of how to create pages.

INCLUDE="include"
TEMPLATE="template"
WORKING="tmp"
ROOT=".."

INPUT="pages"
DOC="$ROOT/doc"
OUTPUT="out"

MENU_FILE="menu.txt"
RST_TEMPLATE="template/rst2htm.template"

function find_replace {
	# Find occurrences of \$\{$1\} in the text and replace with $2.
	sed -re "s\\[$][{]$1[}]\\$2\\g"
}

function get_var {
	# Find the last occurrence of <!-- $1:value --> in the file $2
	sed -nre "s/.*<!-- $1:(.+) -->.*/\1/p" < "$2" \
		| tail -1
}

function make_nav {
	# Output the site nav bar with $1 highlighted
	cat "$MENU_FILE" | while read name; do
		read url;
		([ "$name" == "$1" ] && cat "$TEMPLATE/nav_item_active.htm" \
		                     || cat "$TEMPLATE/nav_item.htm") \
			| find_replace "NAME" "$name" \
			| find_replace "URL" "$url"
	done
}

function change_ext {
	# change $1's extension to $2
	echo "$1" | sed -re "s/([^.]*)([.].*)?/\1.$2/g"
}

# Delete the old output
[ -d $OUTPUT ] && rm -rf $OUTPUT
[ -d $WORKING ] && rm -rf $WORKING
mkdir -p "$OUTPUT"
mkdir -p "$WORKING"

# Generate the download file & put it in the output
./generate_download.sh
DOWNLOAD_SIZE="$(ls -lh perentie.zip | cut -f5 -d " ")"
mv perentie.zip "$OUTPUT/"

# Copy the HTML files
cp "$INPUT/"*.htm "$DOC/"*.htm "$WORKING/"

# Compile rst files and the project documentation
for file in $INPUT/*.rst $DOC/*.rst; do
	[ ! -f "$file" ] && continue
	
	rst2html -q --stylesheet="" --initial-header-level=1 \
	         --no-doc-title \
	         --template="$RST_TEMPLATE" "$file" \
		> "$WORKING/$(change_ext "$(basename "$file")" "htm")"
done

# Stick headers/footers/menus on
for file in $WORKING/*.htm; do
	# Page titles (with and without trailing dash)
	TITLE="$(get_var "TITLE" "$file")"
	TITLE_="$([ -n "$TITLE" ] && echo "$TITLE - " || echo "$TITLE")"
	
	cat "$TEMPLATE/head1.htm" \
	    <( make_nav "$(get_var "MENU_ITEM" "$file")" ) \
	    "$TEMPLATE/head2.htm" \
	    "$file" \
	    "$TEMPLATE/tail.htm" \
		| find_replace "VERSION" "$(tail -1 $ROOT/VERSION)" \
		| find_replace "TITLE" "$TITLE" \
		| find_replace "TITLE_" "$TITLE_" \
		| find_replace "DOWNLOAD_SIZE" "$DOWNLOAD_SIZE" \
		> "$OUTPUT/`basename "$file"`"

done

# Copy in the stock items
cp -r $INCLUDE/* $OUTPUT

# Remove the tmp directory
rm -rf "$WORKING"
