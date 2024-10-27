#!/usr/bin/env bash

function trace() {
	echo "$@" >&2
}

function error() {
	trace "$@"
	exit 1
}

function stem() {
	[ -n "$1" ] || return
	local a=$(basename "$1")
	echo ${a%.*}
}

function checkout() {
	# remove all workdirs
	while IFS= read -r line; do
		trace "removing ${line}"
		rm -rf "${line}" 2>/dev/null
	done < "${tempdirs}"
	rm -f "${tempdirs}"
	# remove tmp files
	find "${target}" -name ._* -delete 2>/dev/null || true
}

function install_source() {
	[ -f "$1" ] || return
	local source="$1"

	local workdir=$(mktemp -d)
	trace "workdir: ${workdir}"
	# register workdir path to a temporary file
	echo "${workdir}" >> "${tempdirs}"

	# fetch
	trace "fetching ${source}"
	cp "${source}" "${workdir}"/.
	trace "@proginc \"${source}\" (fetch)"

	cd "${workdir}"

	# inflate
	while true; do
		local zips=( $(find . \( -name *.zip -o -name *.xpn \) ) )
		[[ ${#zips[@]} == 0 ]] && break
		for z in ${zips[@]}; do
			trace "inflating ${z}"
			unzip "$z" -d "$(dirname "$z")" >/dev/null
			rm -rf "${z}"
		done
	done
	trace "@proginc \"${source}\" (inflate)"

	# install
	local xml=$(find . -name 'Expansion.xml')
	if [ -f "${xml}" ]; then
		# expansion
		trace "${source} is a true MPC expansion"
		local pkgdir=$(dirname "${xml}")
		trace "package directory is ${pkgdir}"
		mkdir -p "${target}/Expansions"
		trace "installing ${pkgdir} to ${target}/Expansions"
		[ -z "${overwrite}" ] && skip="-n"
		cp -R $skip "${pkgdir}" "${target}/Expansions/." || true
	else
		# sample pack
		trace "${source} is not a true MPC expansion"
		local wavdirs=( $(find . -iname *.wav -exec dirname {} + | sort | uniq ) )
		mkdir -p "${target}/Samples"
		for wd in ${wavdirs[@]}; do
			trace "installing ${wd}"
			[ -z "${overwrite}" ] && skip="-n"
			cp -R $skip "${wd}" "${target}/Samples"/. || true
		done
	fi
	trace "@proginc \"${source}\" (install)"
}

set -e

IFS=$'\n'

usage="make-mpc-media.sh {-w|--overwrite} {-p|--purge} <target path> <source> {...}"
target=
sources=()
tempdirs=/tmp/.mpcmcwd

while [ -n "$1" ]; do
	case "$1" in
		-w|--overwrite)
			overwrite=1
			;;
		-h|--help)
			echo $usage
			exit 0
			;;
		-*)
			error "Illegal option ($1)"
			;;
		*)
			if [ -z "${target}" ]; then
				[ -d "$1" ] || error "target '$1' is invalid"
				target="$1"
			else
				[ -f "$1" ] || error "source '$1' not found"
				unzip -l "$1" 2>/dev/null >/dev/null || error "'$1' is not a zip file"
				sources+=( "$1" )
			fi
			;;
	esac
	shift
done

trace "target: ${target}"
trace "sources: ${sources[@]}"

# validate
[ -n "${target}" ] || error "target path not specified"
[[ ${#sources[@]} > 0 ]] || error "No sources provided"

# prepare media
mkdir -p "${target}/Expansions" "${target}/Samples"

> "${tempdirs}"
trap checkout EXIT SIGINT
trace "@proginit $((${#sources[@]} * 3))"
for s in ${sources[@]}; do
	install_source "$s" &
done
wait

complete=1
