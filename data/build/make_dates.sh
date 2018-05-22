#!/bin/bash

start=$(date -d '2018-03-01' +%s)
end=$(date -d '2018-12-31' +%s)




now=$start
while [ $now -le $end ]; do
	echo $now | xargs -iz date -d @z +%Y-%m-%d
	now=$(echo $now+86400 | bc)	
done
