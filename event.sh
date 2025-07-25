#!/bin/bash

TO="crackers.mb67@gmail.com"

SUBJECT="$1 $2"
shift 2
BODY="$*"

USER="${PAM_USER:-$(whoami)}"
FULL_MESSAGE="$BODY — Utilisateur : $USER"

echo "$FULL_MESSAGE" | mail -s "$SUBJECT" "$TO"
