# =====================================================================================================================
#                                   ENERGY-CARBON OPTIMIZATION PLATFORM
# =====================================================================================================================

#                                Institute of Energy and Process Engineering
#                               Labratory of Risk and Reliability Engineering
#                                         ETH Zurich, September 2021

# ======================================================================================================================
#                                    PREPARATION: DEFINE PATHS AND REARRANGE DATA
# ======================================================================================================================

import os
import pandas as pd
import model.preprocess.functions.paths_data as Paths
import model.preprocess.functions.initialise as Init
import model.preprocess.functions.read_data as Read

class Prepare:
    
    def __init__(self, analysis, system):
        """
        This class creates the dictionary containing all the input data
        organised per set according to the model formulation
        :param analysis: dictionary defining the analysis framework
        :return: dictionary containing all the input data
        """
        
        # instantiate analysis object
        self.analysis = analysis
        
        # create a dictionary with the paths to access the model inputs
        self.createPaths()
        
        # initialise a dictionary with the keys of the data to be read
        self.initDict() 
        
        # read data and store in the initialised dictionary
        self.readData()

    def createPaths(self):
        """
        This method creates a dictionary with the paths of the data split
        by carriers, networks, tecnhologies
        :param analysis: dictionary defining the analysis framework
        :return: dictionary all the paths for reading data
        """
        
        # create paths of the data folders according to the input sets
        Paths.data(self)
        # create paths of the input carriers' folders
        Paths.carriers(self)    
        # create paths of netwoks' folders        
        Paths.networks(self)
        # create paths of technologies' folders   
        Paths.technologies(self)
        
    def initDict(self):
        """
        This method initialises a dictionary containing all the input data
        split by carriers, networks, tecnhologies
        :return: dictionary initialised with keys
        """        
        
        self.input = dict()
        
        # initialise the keys with the input carriers' name
        Init.carriers(self)
        # initialise the keys with the networks' name      
        Init.networks(self)
        # initialise the keys with the technologies' name           
        Init.technologies(self)
        # initialise the key of nodes
        Init.nodes(self)
        # initialise the key of times
        Init.times(self)  
        # initialise the key of scenarios
        Init.scenarios(self)             
        
    def readData(self):
        """
        This method fills in the dictionary with all the input data
        split by carriers, networks, tecnhologies
        :return: dictionary containing all the input data 
        """                
        
        # fill the initialised dictionary by reading the input carriers' data        
        Read.carriers(self)     
        # fill the initialised dictionary by reading the netwroks' data        
        Read.networks(self)
        # fill the initialised dictionary by reading the technologies' data          
        Read.technologies(self)
        # fill the initialised dictionary by reading the nodes' data         
        Read.nodes(self)
        # fill the initialised dictionary by reading the times' data           
        Read.times(self)    
        # fill the initialised dictionary by reading the scenarios' data       
        Read.scenarios(self) 
        
    def checkData(self):
        # TODO: define a routine to check the consistency of the data w.r.t.
        # the nodes, times and scenarios
        pass
        