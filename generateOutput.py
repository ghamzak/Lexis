import pandas as pd
from semparse_infer_test import create_states_for_split
from util import dataPrepare
import os
import time

def writeToTSV(split):
    start_time = time.time()
    x = create_states_for_split(split)  
    print(f'[INFO] Creating states for split time: {time.time() - start_time}s')
    split_dummy = dataPrepare(split).dummy_ordered   
    pids, sids, tes, cos_types, s1s, s2s = [], [], [], [], [], []   
    outdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara/data/', split, 'lexis-predictions')     
    i = len(os.listdir(outdir))
    outfile = split+'-lexis-prediction-'+str(i)+'.tsv'
    out_file = os.path.join(outdir, outfile)   
    # out_file = './lexis_output/' + split + '/' + split + '-dummy-predictions-' + str(i) + '.tsv'

    for i in range(split_dummy.shape[0]):
        pid, sid, ent = split_dummy[0].iloc[i], split_dummy[1].iloc[i], split_dummy[2].iloc[i]
        step_state = x[pid][ent][sid]
        cos, l1, l2 = step_state['cos_type'], step_state['s1'], step_state['s2']
        pids += [str(pid)] 
        sids += [str(sid)]
        tes += [ent]
        cos_types += [cos]
        s1s += [l1]
        s2s += [l2]
            
    split_df = pd.DataFrame({'pid': pids, 'sid': sids, 'target_entity': tes, 'cos_type': cos_types, 's1': s1s, 's2': s2s})
    split_df.to_csv(out_file, sep='\t', header=False, index=False)
    

if __name__ == '__main__':
    split = input('which split? ')
    writeToTSV(split)