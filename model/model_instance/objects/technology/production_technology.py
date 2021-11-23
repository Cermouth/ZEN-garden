"""===========================================================================================================================================================================
Title:        ENERGY-CARBON OPTIMIZATION PLATFORM
Created:      October-2021
Authors:      Alissa Ganter (aganter@ethz.ch)
Organization: Laboratory of Risk and Reliability Engineering, ETH Zurich

Description:  Class defining the parameters, variables and constraints of the production technologies.
              The class takes the abstract optimization model as an input, and adds parameters, variables and
              constraints of the production technologies.
==========================================================================================================================================================================="""

import logging
import pyomo.environ as pe
from model.model_instance.objects.technology.technology import Technology

class ProductionTechnology(Technology):

    def __init__(self, object):
        """init generic technology object"""

        logging.info('initialize object of a production technology')
        super().__init__(object, 'Production')

        # Sets and subsets
        subsets = {}
        if self.analysis['technologyApproximation'] == 'PWA':
            self.subsets['setSupportPointsPWA'] = 'Set of support points for piecewise affine linearization'
        subsets = {**subsets, **self.getTechSubsets()}
        self.addSubsets(subsets)

        # Parameters
        params = {}
        if self.analysis['technologyApproximation'] == 'linear':
            params['converEfficiency'] = 'Parameter which specifies the linear conversion efficiency of a technology. Dimensions: setProductionTechnologies, setInputCarriers, setOutputCarriers'
        elif self.analysis['technologyApproximation'] == 'PWA':
            params['converEfficiency'] = 'Parameter which specifies the linear conversion efficiency of a technology. Dimensions: setProductionTechnologies, setInputCarriers, setOutputCarriers, setSupportPointsPWA'
        params = {**params, **self.getTechParams()}
        self.addParams(params)

        # DECISION VARIABLES
        vars = {'inputProductionTechnologies':  'Input stream of a carrier into production technology. \
                                                 Dimensions: setInputCarriers, setProductionTechnologies, setNodes, setTimeSteps. Domain: NonNegativeReals',
                'outputProductionTechnologies':'Output stream of a carrier into production technology. \
                                                 Dimensions: setOutputCarriers, setProductionTechnologies, setNodes, setTimeSteps. Domain: NonNegativeReals'}
        vars = {**vars, **self.getTechVars()}
        self.addVars(vars)
        #TODO implement conditioning for e.g. hydrogen
        #'converEnergy': 'energy involved in conversion of carrier. Dimensions: setCarriers, setNodes, setTimeSteps. Domain: NonNegativeReals'

        # CONSTRAINTS
        constr = {
            'constraintProductionTechnologiesPerformance': 'Conversion efficiency of production technology. Dimensions: setProductionTechnologies, setInputCarriers, setOutputCarriers, setNodes, setTimeSteps'}
        constr = {**constr, **self.getTechConstr()}
        self.addConstr(constr)

        logging.info('added production technology sets, parameters, decision variables and constraints')

    # Constraints
    @staticmethod
    def constraintProductionTechnologiesPerformanceRule(model, tech, carrierIn, carrierOut, node, time):
        """conversion efficiency of production technology. Dimensions: setProductionTechnologiesnologies, setInputCarriers, setNodes, setTimeSteps"""
    
        if model.converEfficiency[tech, carrierIn, carrierOut]>0:
            return (model.converEfficiency[tech, carrierIn, carrierOut] * model.inputProductionTechnologies[carrierIn, tech, node, time]
                    <= model.outputProductionTechnologies[carrierOut, tech, node, time])
        else:
            return(model.inputProductionTechnologies[carrierIn, tech, node, time] == 0)

    # pre-defined in Technology class
    @staticmethod
    def constraintProductionTechnologiesSizeRule(model, tech, node, time):
        """min and max size of production technology. Dimensions: setProductionTechnologiesnologies, setNodes, setTimeSteps"""
    
        return (model.minCapacityProduction[tech] * model.installProductionTechnologies[tech, node, time],
                model.sizeProductionTechnologies[tech, node, time],
                model.maxCapacityProduction[tech] * model.installProductionTechnologies[tech, node, time])

    @staticmethod
    def constraintMinLoadProductionTechnologies1Rule(model, carrier, tech, node, time):
        """min amount of carrier transported with transport technology between two nodes. Dimensions: setCarrier, setTransportTechnologies, setNodes, setAlias, setTimeSteps"""
        #return (model.flowLimit[tech, node, aliasNode, time] * model.minSizeProductionTech[tech], # lb
        #        model.carrierFlowAux[carrier, Tech, node, aliasNode, time],                       # expr
        #        model.flowLimit[tech, node, aliasNode, time] * model.maxSizeProductionTech[tech]) # ub
        return (model.sizeProductionTechnologies[tech, node, time] >= 0)

    @staticmethod
    def constraintMinLoadProductionTechnologies2Rule(model, carrier, tech, node, time):
        """min amount of carrier transported with transport technology between two nodes. Dimensions: setCarrier, setTransportTechnologies, setNodes, setAlias, setTimeSteps"""
        #return (model.carrierFlow - model.maxSizeTransportTech[tech] * (1 - model.flowLimit[tech, node, aliasNode, time]), # lb
        #        model.carrierFlowAux[carrier, tech, node, aliasNode, time],                                                # expr
        #        model.carrierFlow[carrier, tech, node, aliasNode, time])                                                   # ub
        return (model.sizeProductionTechnologies[tech, node, time] >= 0)

    @staticmethod
    def constraintMaxLoadProductionTechnologiesRule(model, carrierIn, carrierOut, tech, node, time):
        """min amount of carrier transported with transport technology between two nodes. Dimensions: setCarrier, setTransportTechnologies, setNodes, setAlias, setTimeSteps"""
        if model.converEfficiency[tech, carrierIn, carrierOut] > 0:
            return (model.outputProductionTechnologies[carrierOut, tech, node, time] <= model.sizeProductionTechnologies[tech, node, time])
        else:
            return (model.outputProductionTechnologies[carrierOut, tech, node, time] == 0)

    @staticmethod
    def constraintAvailabilityProductionTechnologiesRule(model, tech, node, time):
        """limited availability of production technology. Dimensions: setProductionTechnologiesnologies, setNodes, setTimeSteps"""
        return (model.availabilityProductionTechnologies[tech, node, time] <= model.installProductionTechnologies[tech, node, time])