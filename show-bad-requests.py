from pprint import pprint
import pandas as pd
import json

df = pd.concat([
    pd.read_csv('test_will_give_outcomes.csv'),
    pd.read_csv('test_no_give_outcomes.csv')
]).set_index('id')

with open('state.json') as fh:
    state = json.load(fh)

for app_name, responses in state.items():
    bads = list(filter(lambda x: x[1] == -1, responses))
    print('========================================================')
    print(app_name)
    for obs_id, _ in bads[0:10]:
        pprint(df.loc[obs_id].to_dict())
    print('\n\n\n\n')
