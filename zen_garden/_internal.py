"""===========================================================================================================================================================================
Title:        ZEN-GARDEN
Created:      October-2021
Authors:      Alissa Ganter (aganter@ethz.ch)
              Davide Tonelli (davidetonelli@outlook.com)
              Jacob Mannhardt (jmannhardt@ethz.ch)
Organization: Laboratory of Reliability and Risk Engineering, ETH Zurich

Description:  Compilation  of the optimization problem.
==========================================================================================================================================================================="""
import copy
import os
import sys
import logging
import importlib.util
import pkg_resources
from   .preprocess.prepare             import Prepare
from   .model.optimization_setup       import OptimizationSetup
from   .postprocess.results            import Postprocess


def compile(config, dataset_path=None):
    """
    This function runs the compile.py script that was used in ZEN-Garden prior to the package build, it is executed
    in the __main__.py script
    :param config: A config instance used for the run
    :param dataset_path: If not None, used to overwrite the config.analysis["dataset"]
    """
    # SETUP LOGGER
    log_format = '%(asctime)s %(filename)s: %(message)s'
    log_path = os.path.join('outputs', 'logs')
    os.makedirs(log_path, exist_ok=True)
    logging.basicConfig(filename=os.path.join(log_path, 'valueChain.log'), level=logging.INFO,
                        format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
    logging.captureWarnings(True)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)

    # print the version
    version = pkg_resources.require("zen_garden")[0].version
    logging.info(f"Running ZEN-Garden version: {version}")

    # prevent double printing
    logging.propagate = False

    # overwrite the path if necessary
    if dataset_path is not None:
        logging.info(f"Overwriting dataset to: {dataset_path}")
        config.analysis["dataset"] = dataset_path
    # get the abs path to avoid working dir stuff
    config.analysis["dataset"] = os.path.abspath(config.analysis['dataset'])

    ### System - load system configurations
    system_path = os.path.join(config.analysis['dataset'], "system.py")
    if not os.path.exists(system_path):
        raise FileNotFoundError(f"system.py not found in dataset: {config.analysis['dataset']}")
    spec    = importlib.util.spec_from_file_location("module", system_path)
    module  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    system  = module.system
    config.system.update(system)

    ### overwrite default system and scenario dictionaries
    if config.system["conductScenarioAnalysis"]:
        scenarios_path = os.path.abspath(os.path.join(config.analysis['dataset'], "scenarios.py"))
        if not os.path.exists(scenarios_path):
            raise FileNotFoundError(f"scenarios.py not found in dataset: {config.analysis['dataset']}")
        spec        = importlib.util.spec_from_file_location("module", scenarios_path)
        module      = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scenarios   = module.scenarios
        config.scenarios.update(scenarios)

    # create a dictionary with the paths to access the model inputs and check if input data exists
    prepare = Prepare(config)
    # check if all data inputs exist and remove non-existent
    prepare.checkExistingInputData()

    # FORMULATE THE OPTIMIZATION PROBLEM
    # add the elements and read input data
    optimizationSetup           = OptimizationSetup(config.analysis, prepare)
    # get rolling horizon years
    stepsOptimizationHorizon    = optimizationSetup.getOptimizationHorizon()

    # update input data
    optimizationSetupList = []
    for scenario, elements in config.scenarios.items():
        optimizationSetup.restoreBaseConfiguration(scenario, elements)  # per default scenario="" is used as base configuration. Use setBaseConfiguration(scenario, elements) if you want to change that
        optimizationSetup.overwriteParams(scenario, elements)
        # iterate through horizon steps
        for stepHorizon in stepsOptimizationHorizon:
            if len(stepsOptimizationHorizon) == 1:
                logging.info("\n--- Conduct optimization for perfect foresight --- \n")
            else:
                logging.info(f"\n--- Conduct optimization for rolling horizon step {stepHorizon} of {max(stepsOptimizationHorizon)}--- \n")
            # overwrite time indices
            optimizationSetup.overwriteTimeIndices(stepHorizon)
            # create optimization problem
            optimizationSetup.constructOptimizationProblem()
            # SOLVE THE OPTIMIZATION PROBLEM
            optimizationSetup.solve(config.solver)
            # add newly builtCapacity of first year to existing capacity
            optimizationSetup.addNewlyBuiltCapacity(stepHorizon)
            # add cumulative carbon emissions to previous carbon emissions
            optimizationSetup.addCarbonEmissionsCumulative(stepHorizon)
            # EVALUATE RESULTS
            modelName = os.path.basename(config.analysis["dataset"])
            if len(stepsOptimizationHorizon) > 1:
                modelName += f"_MF{stepHorizon}"
            if config.system["conductScenarioAnalysis"]:
                modelName += f"_{scenario}"
            evaluation = Postprocess(optimizationSetup, modelName=modelName)


    #adaption LK
    #        optimizationSetupCopy = copy.deepcopy(optimizationSetup)
    #        optimizationSetupList.append(optimizationSetupCopy)
    #if len(optimizationSetupList) == 1:
    #    optimizationSetupList = optimizationSetupList[0]
    #return optimizationSetupList
    return optimizationSetup
    """
    #adaption_2
    import pandas as pd
    #import csv file containing selected variable values of test model collection
    testVariables = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + '\\test_variables_readable.csv', header=0, index_col=None)

    def compareVariables(testModel):
        # dictionary to store variable names, indices, values and test values of variables which don't match the test values
        failedVariables = {}
        #iterate through dataframe rows
        for dataRow in testVariables.values:
            #skip row if data doesn't correspond to selected test model
            if dataRow[0] != testModel:
                continue
            #get variable attribute of optimizationSetup object by using string of the variable's name (e.g. optimizationSetup.model.importCarrierFLow)
            variableAttribute = getattr(optimizationSetup.model,dataRow[1])
            #iterate through indices of current variable
            for variableIndex in variableAttribute.extract_values():
                #ensure equality of dataRow index and variable index
                if str(variableIndex) == dataRow[2]:
                    #check if variable value at current index differs from zero such that relative error can be computed
                    if variableAttribute.extract_values()[variableIndex] != 0:
                        #check if relative error exceeds limit of 10^-3, i.e. value differs from test value
                        if abs(variableAttribute.extract_values()[variableIndex] - dataRow[3]) / variableAttribute.extract_values()[variableIndex] > 10**(-3):
                            if dataRow[1] in failedVariables:
                                failedVariables[dataRow[1]][dataRow[2]] = {'computedValue' : variableAttribute.extract_values()[variableIndex]}
                            else:
                                failedVariables[dataRow[1]] = {dataRow[2] : {'computedValue' : variableAttribute.extract_values()[variableIndex]} }#variableAttribute.extract_values()[variableIndex]
                            failedVariables[dataRow[1]][dataRow[2]]['testValue'] = dataRow[3]
                    else:
                        #check if absolute error exceeds specified limit
                        if abs(variableAttribute.extract_values()[variableIndex] - dataRow[3]) > 10**(-3):
                            if dataRow[1] in failedVariables:
                                failedVariables[dataRow[1]][dataRow[2]] = {'computedValue' : variableAttribute.extract_values()[variableIndex]}
                            else:
                                failedVariables[dataRow[1]] = {dataRow[2] : {'computedValue' : variableAttribute.extract_values()[variableIndex]} }#variableAttribute.extract_values()[variableIndex]
                            failedVariables[dataRow[1]][dataRow[2]]['testValue'] = dataRow[3]
        assertionString = str()
        for failedVar in failedVariables:
            assertionString += f"\n{failedVar}{failedVariables[failedVar]}"

        assert len(failedVariables) == 0, f"The variables {assertionString} \ndon't match their test values"

    compareVariables('test_6a')

    """