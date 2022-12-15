"""===========================================================================================================================================================================
Title:          ZEN-GARDEN
Created:        October-2021
Authors:        Alissa Ganter (aganter@ethz.ch)
                Jacob Mannhardt (jmannhardt@ethz.ch)
Organization:   Laboratory of Reliability and Risk Engineering, ETH Zurich

Description:    Class defining the parameters, variables and constraints that hold for all transport technologies.
                The class takes the abstract optimization model as an input, and returns the parameters, variables and
                constraints that hold for the transport technologies.
==========================================================================================================================================================================="""
import logging
import warnings
import pyomo.environ as pe
import numpy as np
from .technology import Technology
from ..energy_system import EnergySystem
from ..component import Parameter,Variable,Constraint

class TransportTechnology(Technology):
    # set label
    label           = "setTransportTechnologies"
    locationType    = "setEdges"
    # empty list of elements
    list_of_elements = []
    # dict of reversed edges
    dictReversedEdges = {}

    def __init__(self, tech):
        """init transport technology object
        :param tech: name of added technology"""

        logging.info(f'Initialize transport technology {tech}')
        super().__init__(tech)
        # store input data
        self.store_input_data()
        # add TransportTechnology to list
        TransportTechnology.add_element(self)

    def store_input_data(self):
        """ retrieves and stores input data for element as attributes. Each Child class overwrites method to store different attributes """   
        # get attributes from class <Technology>
        super().store_input_data()
        # set attributes for parameters of child class <TransportTechnology>
        self.distance                       = self.datainput.extract_input_data("distanceEuclidean",index_sets=["setEdges"])
        self.lossFlow                       = self.datainput.extract_attribute("lossFlow")["value"]
        # get capex of transport technology
        self.getCapexTransport()
        # annualize capex
        self.convertToAnnualizedCapex()
        # calculate capex of existing capacity
        self.capexExistingCapacity          = self.calculateCapexOfExistingCapacities()
        # check that existing capacities are equal in both directions if technology is bidirectional
        if self.name in EnergySystem.get_system()["setBidirectionalTransportTechnologies"]:
            self.checkIfBidirectional()

    def getCapexTransport(self):
        """get capex of transport technology"""
        set_time_steps_yearly = EnergySystem.get_energy_system().set_time_steps_yearly
        # check if there are separate capex for capacity and distance
        if EnergySystem.system['DoubleCapexTransport']:
            # both capex terms must be specified
            self.capexSpecific    = self.datainput.extract_input_data("capexSpecific",index_sets=["setEdges", "set_time_steps"],time_steps=set_time_steps_yearly)
            self.capexPerDistance = self.datainput.extract_input_data("capexPerDistance",index_sets=["setEdges", "set_time_steps"],time_steps=set_time_steps_yearly)
        else:  # Here only capexSpecific is used, and capexPerDistance is set to Zero.
            if self.datainput.exists_attribute("capexPerDistance"):
                self.capexPerDistance   = self.datainput.extract_input_data("capexPerDistance",index_sets=["setEdges","set_time_steps"],time_steps= set_time_steps_yearly)
                self.capexSpecific      = self.capexPerDistance * self.distance
                self.fixedOpexSpecific  = self.fixedOpexSpecific * self.distance
            elif self.datainput.exists_attribute("capexSpecific"):
                self.capexSpecific  = self.datainput.extract_input_data("capexSpecific",index_sets=["setEdges","set_time_steps"],time_steps= set_time_steps_yearly)
            else:
                raise AttributeError(f"The transport technology {self.name} has neither capexPerDistance nor capexSpecific attribute.")
            self.capexPerDistance   = self.capexSpecific * 0.0

    def convertToAnnualizedCapex(self):
        """ this method converts the total capex to annualized capex """
        fractionalAnnuity       = self.calculateFractionalAnnuity()
        system                  = EnergySystem.get_system()
        _fraction_year         = system["unaggregatedTimeStepsPerYear"] / system["totalHoursPerYear"]
        # annualize capex
        self.capexSpecific      = self.capexSpecific * fractionalAnnuity + self.fixedOpexSpecific * _fraction_year
        self.capexPerDistance   = self.capexPerDistance * fractionalAnnuity

    def calculateCapexOfSingleCapacity(self,capacity,index):
        """ this method calculates the annualized capex of a single existing capacity. """
        #TODO check existing capex of transport techs -> Hannes
        if np.isnan(self.capexSpecific[index[0]].iloc[0]):
            return 0
        else:
            return self.capexSpecific[index[0]].iloc[0] * capacity

    def checkIfBidirectional(self):
        """ checks that the existing capacities in both directions of bidirectional capacities are equal """
        energy_system = EnergySystem.get_energy_system()
        for edge in energy_system.setEdges:
            _reversed_edge = EnergySystem.calculate_reversed_edge(edge)
            TransportTechnology.setReversedEdge(edge=edge, _reversed_edge=_reversed_edge)
            _existingCapacityEdge = self.existingCapacity[edge]
            _existingCapacityReversedEdge = self.existingCapacity[_reversed_edge]
            assert (_existingCapacityEdge == _existingCapacityReversedEdge).all(), \
                f"The existing capacities of the bidirectional transport technology {self.name} are not equal on the edge pair {edge} and {_reversed_edge} ({_existingCapacityEdge.to_dict()} and {_existingCapacityReversedEdge.to_dict()})"

    ### --- getter/setter classmethods
    @classmethod
    def setReversedEdge(cls,edge,_reversed_edge):
        """ maps the reversed edge to an edge """
        cls.dictReversedEdges[edge] = _reversed_edge

    @classmethod
    def getReversedEdge(cls, edge):
        """ get the reversed edge corresponding to an edge """
        return cls.dictReversedEdges[edge]

    ### --- classmethods to construct sets, parameters, variables, and constraints, that correspond to TransportTechnology --- ###
    @classmethod
    def construct_sets(cls):
        """ constructs the pe.Sets of the class <TransportTechnology> """
        pass

    @classmethod
    def construct_params(cls):
        """ constructs the pe.Params of the class <TransportTechnology> """
        model = EnergySystem.get_pyomo_model()
        
        # distance between nodes
        Parameter.add_parameter(
            name="distance",
            data= EnergySystem.initialize_component(cls,"distance",index_names=["setTransportTechnologies","setEdges"]),
            doc = 'distance between two nodes for transport technologies')
        # capital cost per unit
        Parameter.add_parameter(
            name="capexSpecificTransport",
            data= EnergySystem.initialize_component(cls,"capexSpecific",index_names=["setTransportTechnologies","setEdges","set_time_steps_yearly"]),
            doc = 'capex per unit for transport technologies')
        # capital cost per distance
        Parameter.add_parameter(
            name="capexPerDistance",
            data=EnergySystem.initialize_component(cls, 'capexPerDistance', index_names=['setTransportTechnologies', "setEdges", "set_time_steps_yearly"]),
            doc='capex per distance for transport technologies')
        # carrier losses
        Parameter.add_parameter(
            name="lossFlow",
            data= EnergySystem.initialize_component(cls,"lossFlow",index_names=["setTransportTechnologies"]),
            doc = 'carrier losses due to transport with transport technologies')

    @classmethod
    def construct_vars(cls):
        """ constructs the pe.Vars of the class <TransportTechnology> """
        def carrierFlowBounds(model,tech ,edge,time):
            """ return bounds of carrierFlow for bigM expression 
            :param model: pe.ConcreteModel
            :param tech: tech index
            :param edge: edge index
            :param time: time index
            :return bounds: bounds of carrierFlow"""
            # convert operationTimeStep to timeStepYear: operationTimeStep -> base_time_step -> timeStepYear
            timeStepYear = EnergySystem.convert_time_step_operation2invest(tech,time)
            bounds = model.capacity[tech,"power",edge,timeStepYear].bounds
            return(bounds)

        model = EnergySystem.get_pyomo_model()
        # flow of carrier on edge
        Variable.add_variable(
            model,
            name="carrierFlow",
            index_sets= cls.create_custom_set(["setTransportTechnologies","setEdges","setTimeStepsOperation"]),
            domain = pe.NonNegativeReals,
            bounds = carrierFlowBounds,
            doc = 'carrier flow through transport technology on edge i and time t'
        )
        # loss of carrier on edge
        Variable.add_variable(
            model,
            name="carrierLoss",
            index_sets= cls.create_custom_set(["setTransportTechnologies","setEdges","setTimeStepsOperation"]),
            domain = pe.NonNegativeReals,
            doc = 'carrier flow through transport technology on edge i and time t'
        )
        
    @classmethod
    def construct_constraints(cls):
        """ constructs the pe.Constraints of the class <TransportTechnology> """
        model   = EnergySystem.get_pyomo_model()
        system  = EnergySystem.get_system()
        # Carrier Flow Losses 
        Constraint.add_constraint(
            model,
            name="constraintTransportTechnologyLossesFlow",
            index_sets= cls.create_custom_set(["setTransportTechnologies","setEdges","setTimeStepsOperation"]),
            rule = constraintTransportTechnologyLossesFlowRule,
            doc = 'Carrier loss due to transport with through transport technology'
        ) 
        # capex of transport technologies
        Constraint.add_constraint(
            model,
            name="constraintCapexTransportTechnology",
            index_sets= cls.create_custom_set(["setTransportTechnologies","setEdges","set_time_steps_yearly"]),
            rule = constraintCapexTransportTechnologyRule,
            doc = 'Capital expenditures for installing transport technology'
        )
        # bidirectional transport technologies: capacity on edge must be equal in both directions
        Constraint.add_constraint(
            model,
            name="constraintBidirectionalTransportTechnology",
            index_sets= cls.create_custom_set(["setTransportTechnologies", "setEdges", "set_time_steps_yearly"]),
            rule=constraintBidirectionalTransportTechnologyRule,
            doc='Forces that transport technology capacity must be equal in both directions'
        )

    # defines disjuncts if technology on/off
    @classmethod
    def disjunctOnTechnologyRule(cls,disjunct, tech,capacity_type, edge, time):
        """definition of disjunct constraints if technology is on"""
        model = disjunct.model()
        # get parameter object
        params = Parameter.get_component_object()
        # get invest time step
        timeStepYear = EnergySystem.convert_time_step_operation2invest(tech,time)
        # disjunct constraints min load
        disjunct.constraintMinLoad = pe.Constraint(
            expr=model.carrierFlow[tech, edge, time] >= params.minLoad[tech,capacity_type,edge,time] * model.capacity[tech,capacity_type,edge, timeStepYear]
        )

    @classmethod
    def disjunctOffTechnologyRule(cls,disjunct, tech,capacity_type, edge, time):
        """definition of disjunct constraints if technology is off"""
        model = disjunct.model()
        disjunct.constraintNoLoad = pe.Constraint(
            expr=model.carrierFlow[tech, edge, time] == 0
        )

### --- functions with constraint rules --- ###
def constraintTransportTechnologyLossesFlowRule(model, tech, edge, time):
    """compute the flow losses for a carrier through a transport technology"""
    # get parameter object
    params = Parameter.get_component_object()
    if np.isinf(params.distance[tech,edge]):
        return model.carrierLoss[tech, edge, time] == 0
    else:
        return(model.carrierLoss[tech, edge, time] ==
               params.distance[tech,edge] * params.lossFlow[tech] * model.carrierFlow[tech, edge, time])

def constraintCapexTransportTechnologyRule(model, tech, edge, time):
    """ definition of the capital expenditures for the transport technology"""
    # get parameter object
    params = Parameter.get_component_object()
    if np.isinf(params.distance[tech, edge]):
        return model.built_capacity[tech,"power",edge, time] == 0
    else:
        return (model.capex[tech,"power",edge, time] ==
                model.built_capacity[tech,"power",edge, time] * params.capexSpecificTransport[tech,edge, time] +
                model.installTechnology[tech,"power", edge, time] * params.distance[tech, edge] * params.capexPerDistance[tech, edge, time])

def constraintBidirectionalTransportTechnologyRule(model, tech, edge, time):
    """ Forces that transport technology capacity must be equal in both direction"""
    system = EnergySystem.get_system()
    if tech in system["setBidirectionalTransportTechnologies"]:
        _reversed_edge = TransportTechnology.getReversedEdge(edge)
        return (model.built_capacity[tech,"power",edge, time] ==
                model.built_capacity[tech,"power",_reversed_edge, time])
    else:
        return pe.Constraint.Skip
