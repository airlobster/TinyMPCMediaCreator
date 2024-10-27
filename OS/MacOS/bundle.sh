#!/usr/bin/env bash

set -e

function trace() {
	echo -e "$@" >&2
}

function error() {
	trace "$@"
	exit 1
}

function cleanup() {
	rm -rf build dist .eggs /tmp/_*.dmg
	find . -name .DS_Store | xargs rm -f
}

function get_bootstrap_prop() {
	[ -n "$1" ] || error "Missing property name"
	python <<EOF
import json
with open('bootstrap.json') as f:
	print(json.load(f)['$1'])
EOF
}

outdir="."

while [ -n "$1" ]; do
	case "$1" in
		-o|--outdir)
			shift
			outdir="$1"
			;;
		-f|--showinfinder)
			showinfinder=1
			;;
		-i|--install)
			install=1
			;;
		-I|--install-cleanup)
			install=1
			post_install_cleanup=1
			;;
		-c|--cleanup)
			cleanup=1
			;;
		*)
			error "Illegal option ($1)"
			;;
	esac
	shift
done

# search for base directory
markerfile="bootstrap.json"
while [ ! -f "${markerfile}" ]; do
	cd ..
done
[ -f "./${markerfile}" ] || error "${markerfile} not found"

# input validation
[ -n "$VIRTUAL_ENV" ] || error "no active virtual-env"
[ -d "${outdir}" ] || error "${outdir} not found"

version=$(get_bootstrap_prop version)
[ -n "${version}" ] || error "application version could not be resolved"

name=$(get_bootstrap_prop appname)
[ -n "${name}" ] || error "application name could not be resolved"

bundle_version=${version//\./_}
finaldmg="${outdir}/${name}.${bundle_version}.dmg"

# preparation clean up
cleanup
rm -f "${finaldmg}"
[ -n "${cleanup}" ] && trap cleanup EXIT
# bundle
python setup.py py2app
# create a soft-link to the /Applications folder so the user can drag the app to it
ln -s /Applications dist
# make dmg
# hdiutil create /tmp/_${name}.dmg -ov -volname ${name} -fs HFS+ -srcfolder dist/${name}.app/
hdiutil create /tmp/_${name}.dmg -ov -volname ${name} -fs HFS+ -srcfolder dist/
hdiutil convert /tmp/_${name}.dmg -format UDZO -o "${finaldmg}"

if [ -n "${showinfinder}" ]; then
	open -R "${finaldmg}"
fi

if [ -n "${install}" ]; then
	# mount dmg
	hdiutil attach "${finaldmg}"
	# copy app to /Applications
	sudo cp -R "/Volumes/${name}/${name}.app" "/Applications/."
	if [ -n "${post_install_cleanup}" ]; then
		# unmount dmg
		hdiutil detach "/Volumes/${name}"
	fi
	# open -R "/Applications/${name}.app"
	trace "${name} installed in /Applications/${name}.app"
fi

