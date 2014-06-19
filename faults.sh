grep -n -R -E "(#0\s|Assertion|runtime\serror:)" bucket/* | sort -t: -n -k2 | uniq -f3
