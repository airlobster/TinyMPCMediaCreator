#!/usr/bin/env bash

set -e

function trace() {
	echo "$@" >&2
}

function error() {
	trace "$@"
	exit 1
}

function enumDirectories() {
	[ -n "${deleteroot}" ] || exclude=(-not -path "$1")
	find "$1" -type d ${exclude[@]} | sort -ru
}

IFS=$'\n'

roots=()
total=0

# collect roots from command-line
while [ -n "$1" ]; do
	case "$1" in
		-d|--dryrun)
			dryrun=1
			;;
		-r|--deleteroot)
			deleteroot=1
			;;
		-*)
			error "Illegal option ($1)"
			;;
		*)
			[ -d "$1" ] || error "\"$1\" is not a valid directory"
			[ -G "$1" ] || error "accessing \"$1\" is not permitted"
			roots+=("$1")
			;;
	esac
	shift
done

[[ ${#roots[@]} == 0 ]] && error "Missing paths"

# count total sub-directories
for root in ${roots[@]}; do
	total=$(( ${total} + $(enumDirectories "${root}" | wc -l) ))
done

# remove
trace "@proginit ${total}"
for root in ${roots[@]}; do
	for sub in $(enumDirectories "${root}"); do
		[ -n "${dryrun}" ] || rm -rf "${sub}" || true
		trace "@proginc \"${sub}\""
	done
done

