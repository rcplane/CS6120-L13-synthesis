# from repo root
reset # clear terminal
for file in examples/*.txt ; do
    echo "$file"
    cat "$file"
    python3 solve.py < "$file"
    echo "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+" #"done with $file"
  done