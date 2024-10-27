#!/usr/bin/env bash

function trace() {
	echo "$@" >&2
}

function checkout() {
	trace "@proginc ${drive}"
}

drive="$1"

trace "@proginit 1"
trap checkout EXIT SIGINT
hdiutil detach "${drive}" -force
