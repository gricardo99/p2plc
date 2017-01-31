#!/bin/bash

lcversion="v1"
apiKey=$(awk '/api.lendingclub.com/ {f=NR} f&&f+2==NR {print $2}' ~/.netrc)
investorID=$(awk '/api.lendingclub.com/ {f=NR} f&&f+1==NR {print $2}' ~/.netrc)
cmd="curl -i -H \"Authorization: $apiKey\" -H \"Content-Type: application/json\" -X GET https://api.lendingclub.com/api/investor/$lcversion/accounts/$investorID/summary"

echo "running:"
echo $cmd;
eval $cmd
