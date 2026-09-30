sqlite3 ~/shdb 'create table c(_);create table _(_ unique,c);'
HISTFILE=
sqlite3 ~/shdb 'select _ from _ order by c'>/tmp/_
history -r /tmp/_
shdb=(`history 1`)
trap "history -d0-$shdb;history|sed -Ez 's/ +[0-9]+ +([^\n]+)\n/\1\o036/g'|sqlite3 ~/shdb '.import --ascii /dev/stdin c' 'insert into _ select trim(_),1 from c where true on conflict do update set c=c+1;delete from c'" exit
