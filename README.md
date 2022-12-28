# Lexis
Symbolic Entity State Tracking

The first version of Lexis was described in [this article](https://aclanthology.org/2021.law-1.13/). This is an expansion of Lexis based on the error analysis performed in the paper.

For the complete experiments and the description of the approach, refer to Chapter 4 of my dissertation (link to be provided later in 2023). We showed that Lexis is generalizable and explainable. Also, we achieve a new SOTA on the Recipes dataset.

## ProPara dataset

To run Lexis on the ProPara dataset and generate the predictions file in the correct format, run the generateOutput.py file. It will ask you to input the split (test, dev, or train). 

To evaluate on the ProPara dataset, run the evaluator_for_lexis_propara.py file. 

## Recipes Dataset

1. preprocess using the recipes_data_preprocessing.py file
2. run recipes_evaluate.ipynb
