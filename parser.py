#!/usr/bin/python3

import sys
import re
from datetime import datetime

log_file = sys.argv[1]
try:
    min_period = sys.argv[2]
except IndexError:
    pass

pattern = re.compile(r'.*Periodic low priority record')
date_pattern = re.compile(r'\d{4}\.\d{2}\.\d{2}\s\d{2}:\d{2}:\d{2}')
time_format = '[%Y.%m.%d %H:%M:%S]'

with open(log_file, 'r') as f:
    log = f.read()

matches = pattern.finditer(log)

minuend = None
subtrahend = None
diffs = []
for m in matches:
    time_str = m.group().split('-')[0]
    time = datetime.strptime(time_str, time_format)
    if not subtrahend:
        subtrahend = time
    else:
        minuend = time
        diff = (minuend - subtrahend).total_seconds()
        subtrahend = minuend
        diffs.append(diff)

s_sq = (sum([i**2 for i in diffs]) - ((sum(diffs)**2)/len(diffs)))/(len(diffs)-1)
s = s_sq**0.5
diffs.sort()
diffs_len = len(diffs)
R = diffs[-1] - diffs[0]
x_ = sum(diffs)/diffs_len
Q1 = 0.25*(diffs_len+1)
Q3 = 0.75*(diffs_len+1)

print(f"MEAN: {x_:.2f}")
print(f"S^2: {s_sq:.2f}\nS: {s:.2f}")
print(f"R: {R}")
print(f"Q1: {diffs[int(Q1)]}; Q3: {diffs[int(Q3)]}")
