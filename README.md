Copy `settings_example.py` to `settings.py` and fill that bad boy in!


Sends the observations and true outcomes from the two csvs in this repo 
uniformely distributed over a time range.

To run the full simulator, you need to run two scripts:

```
# If today is January 20th 2018 and you want it to run through the 25th ending
# exactly at January 26th at 01h01 you would execute the following:

# start the simulator that sends observations uniformely distributed over time
python run-simulation.py --enddate 26-01-2018 "observation"

# start the simulator that sends the true outcomes uniformely distributed
# until the 24th because you want them to end early
python run-simulation.py --enddate 24-01-2018 "true-outcome"
```
