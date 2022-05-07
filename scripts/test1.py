#import tempfile
#with tempfile.TemporaryDirectory() as tmpdirname:
#    print('created temporary directory', tmpdirname)

import re

lines = """
      21000 -- (-156.867) (-186.222) (-151.640) [-148.184] -- 0:00:03
      22000 -- (-172.182) (-166.280) [-152.891] (-150.863) -- 0:00:03
      23000 -- (-161.007) (-158.153) (-150.284) [-151.297] -- 0:00:06
"""

for line in lines.split("\n"):
    progress_match = re.match("^\s+(\d+).*(\d+:\d+:\d+)$",line)
    #progress_match = re.match("(\d+) \s+--.+--\s+(\d+:\d+\d+)",line)
    if progress_match:
        print(progress_match.group(1))
        print(progress_match.group(2))
    else:
        print("not found", line)