import os
import glob
import subprocess

parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara')
evaluator_file_address = os.path.join(parent_dir, 'evaluator/evaluator.py')

def getLastFile(pathtofolder):
    list_of_files = glob.glob(pathtofolder+'/*') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

if __name__ == '__main__':
    split = input('which split? ')
    predictions_dir = os.path.join(parent_dir, 'data', split, 'lexis-predictions')
    last_file_name = getLastFile(predictions_dir)
    answers_file = os.path.join(parent_dir, 'data', split, 'answers.tsv')
    subprocess.run(['python', evaluator_file_address, '-p', last_file_name, '-a', answers_file])