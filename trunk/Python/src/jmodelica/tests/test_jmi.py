""" Test module for testing the jmi module
"""

import os

import ctypes as ct
import numpy as N
import nose
import matplotlib.pyplot as plt
import nose.tools as ntools

#from jmodelica.tests import load_example_standard_model
from jmodelica.tests import testattr

import jmodelica.jmi as jmi
from jmodelica.compiler import OptimicaCompiler
from jmodelica.compiler import ModelicaCompiler
import jmodelica.xmlparser as xp
import jmodelica.io
from jmodelica.initialization.ipopt import NLPInitialization
from jmodelica.initialization.ipopt import InitializationOptimizer
from jmodelica.optimization import ipopt
from jmodelica.simulation.sundials import SundialsODESimulator

int = N.int32
N.int = N.int32

# set paths
jm_home = os.environ.get('JMODELICA_HOME')
path_to_examples = os.path.join(jm_home, "Python", "jmodelica", "examples")
path_to_tests = os.path.join(jm_home, "Python", "jmodelica", "tests")
# get a compiler
oc = OptimicaCompiler()

# compile VDP
model_vdp = os.path.join("files", "VDP.mo")
fpath_vdp = os.path.join(path_to_examples, model_vdp)
cpath_vdp = "VDP_pack.VDP_Opt"
fname_vdp = cpath_vdp.replace('.','_',1)
oc.set_boolean_option('state_start_values_fixed',True)
oc.compile_model(fpath_vdp, cpath_vdp, target='ipopt')

# constants used in TestJMIModel
eval_alg = jmi.JMI_DER_CPPAD
sparsity = jmi.JMI_DER_SPARSE
indep_vars = jmi.JMI_DER_ALL

# compile CSTR with alias variables elimination
model_cstr = os.path.join("files", "CSTR.mo")
fpath_cstr = os.path.join(path_to_examples, model_cstr)
cpath_cstr = "CSTR.CSTR_Opt"
fname_cstr = cpath_cstr.replace('.','_',1)      
oc.set_boolean_option('eliminate_alias_variables', True)
oc.compile_model(fpath_cstr, cpath_cstr, target='ipopt')




class TestModel_VDP:
    """Test the high level model class, jmi.Model.
    
    The tests are based on the Van der Pol oscillator.
    
    Also note that this class also is tested in simulation tests.
    """
    def __init__(self):        
        self.vdp = jmi.Model(fname_vdp)
            
    @testattr(stddist = True)                                          
    def test_model_size(self):
        """Test jmi.Model length of x"""
        size = len(self.vdp.x)
        nose.tools.assert_equal(size, 3)

    @testattr(stddist = True)    
    def test_reset(self):
        """Testing resetting the a jmi.Model."""
        random = N.array([12, 31, 42])
        self.vdp.x = random
        self.vdp.reset()
        maxdiff = max(N.abs(random - self.vdp.x))
        assert maxdiff > 0.001

    @testattr(stddist = True)    
    def test_get_variable_names(self):
        names = self.vdp.get_variable_names()
        ntools.assert_equal(names.get(0),"p1")
        
    @testattr(stddist = True)
    def test_get_derivative_names(self):
        names = self.vdp.get_derivative_names()
        ntools.assert_equal(names.get(4),"der(x2)")
    
    @testattr(stddist = True)
    def test_get_differentiated_variable_names(self):
        names = self.vdp.get_differentiated_variable_names()
        ntools.assert_equal(names.get(8),"cost")
    
    @testattr(stddist = True)
    def test_get_input_names(self):
        names = self.vdp.get_input_names()
        ntools.assert_equal(names.get(9),"u")
    
    @testattr(stddist = True)
    def test_get_algebraic_variable_names(self):
        # TODO improve test 
        # there are no algebraic variables in the vdp model
        names = self.vdp.get_algebraic_variable_names()
        ntools.assert_equal(len(names),0)
    
    @testattr(stddist = True)
    def test_get_p_opt_names(self):
        # TODO improve test 
        # there are no popt variables in the model
        names = self.vdp.get_p_opt_names()
        ntools.assert_equal(len(names),0)
     
    @testattr(stddist = True)   
    def test_get_sizes(self):
        sizes = [0, 0, 3, 0, 3, 3, 1, 0, 1, 0, 0, 18]
        ntools.assert_equal(self.vdp.get_sizes(),sizes)
    
    @testattr(stddist = True)    
    def test_get_offsets(self):
        offsets = [0, 0, 0, 3, 3, 6, 9, 10, 10, 11, 14, 17, 18, 18, 18]
        ntools.assert_equal(self.vdp.get_offsets(),offsets)
    
    @testattr(stddist = True)
    def test_get_n_tp(self):
        ntools.assert_equal(self.vdp.get_n_tp(),1)
        
    @testattr(stddist = True)    
    def test_states_get_set(self):
        """Test jmi.Model.set_x(...) and jmi.Model.get_x()."""
        new_states = [1.74, 3.38, 12.45]
        reset = [0, 0, 0]
        self.vdp.x = reset
        states = self.vdp.x
        N.testing.assert_array_almost_equal(reset, states)
        self.vdp.x = new_states
        states = self.vdp.x
        N.testing.assert_array_almost_equal(new_states, states)

    @testattr(stddist = True)    
    def test_states_p_get_set(self):
        """Test jmi.Model.set_x_p(...) and jmi.Model.get_x_p()."""
        new_states = N.ones(3)
        timepoint=0
        self.vdp.set_x_p(new_states, 0)
        N.testing.assert_array_almost_equal(self.vdp.get_x_p(0),new_states)
        
    @testattr(stddist = True)    
    def test_pd_get_set(self):
        """Test jmi.Model.set_pd(...) and jmi.Model.get_pd()."""
        # pd is empty
        pd_new = N.ones(1)
        self.vdp.set_pd(pd_new)
        N.testing.assert_array_almost_equal(self.vdp.get_pd(),N.zeros(0))

    @testattr(stddist = True)    
    def test_cd_get_set(self):
        """Test jmi.Model.set_cd(...) and jmi.Model.get_cd()."""
        # cd is empty
        cd_new = N.ones(1)
        self.vdp.set_cd(cd_new)
        N.testing.assert_array_almost_equal(self.vdp.get_cd(),N.zeros(0))

    @testattr(stddist = True)    
    def test_ci_get_set(self):
        """Test jmi.Model.set_ci(...) and jmi.Model.get_ci()."""
        # cd is empty
        ci_new = N.ones(1)
        self.vdp.set_ci(ci_new)
        N.testing.assert_array_almost_equal(self.vdp.get_ci(),N.zeros(0))
    
    @testattr(stddist = True)   
    def test_diffs(self):
        """Test jmi.Model.set_dx(...) and jmi.Model.get_dx()."""
        reset = [0, 0, 0]
        diffs = self.vdp.dx
        diffs[:] = reset
        diffs2 = self.vdp.dx
        N.testing.assert_array_almost_equal(reset, diffs2)
        
        new_diffs = [1.54, 3.88, 45.87]
        diffs[:] = new_diffs
        N.testing.assert_array_almost_equal(new_diffs, diffs2)

    @testattr(stddist = True)    
    def test_diffs_p_get_set(self):
        """Test jmi.Model.set_dx_p(...) and jmi.Model.get_dx_p()."""
        new_diffs = N.ones(3)
        timepoint=0
        self.vdp.set_dx_p(new_diffs, 0)
        N.testing.assert_array_almost_equal(self.vdp.get_dx_p(0),new_diffs)
            
    @testattr(stddist = True)    
    def test_inputs(self):
        """Test jmi.Model.set_u(...) and jmi.Model.get_u()."""
        new_inputs = [1.54]
        reset = [0]
        self.vdp.u = reset
        inputs = self.vdp.u
        N.testing.assert_array_almost_equal(reset, inputs)
        self.vdp.u = new_inputs
        inputs = self.vdp.u
        N.testing.assert_array_almost_equal(new_inputs, inputs)

    @testattr(stddist = True)    
    def test_inputs_p_get_set(self):
        """Test jmi.Model.set_u_p(...) and jmi.Model.get_u_p()."""
        new_inputs = N.ones(1)
        timepoint=0
        self.vdp.set_u_p(new_inputs, 0)
        N.testing.assert_array_almost_equal(self.vdp.get_u_p(0),new_inputs)
        
    @testattr(stddist = True)    
    def test_w_get_set(self):
        """Test jmi.Model.set_w(...) and jmi.Model.get_w()."""
        # w is empty
        w_new = N.ones(1)
        self.vdp.set_w(w_new)
        N.testing.assert_array_almost_equal(self.vdp.get_w(),N.zeros(0))

    @testattr(stddist = True)    
    def test_w_p_get_set(self):
        """Test jmi.Model.set_w_p(...) and jmi.Model.get_w_p()."""
        new_alg = N.ones(1)
        timepoint=0
        self.vdp.set_w_p(new_alg, 0)
        N.testing.assert_array_almost_equal(self.vdp.get_w_p(0),N.zeros(0))
        
    @testattr(stddist = True)    
    def test_z_get_set(self):
        """Test jmi.Model.set_z(...) and jmi.Model.get_z()."""
        z_new = self.vdp.get_z()
        z_new.itemset(0,2)
        self.vdp.set_z(z_new)
        N.testing.assert_array_almost_equal(self.vdp.get_z(),z_new)
    
    @testattr(stddist = True)    
    def test_parameters(self):
        """Test methods jmi.Model.[set|get]_pi(...)."""
        new_params = [1.54, 19.54, 78.12]
        reset = [0] * 3
        self.vdp.pi = reset
        params = self.vdp.pi
        N.testing.assert_array_almost_equal(reset, params)
        self.vdp.pi = new_params
        params = self.vdp.pi
        N.testing.assert_array_almost_equal(new_params, params)
    
    @testattr(stddist = True)    
    def test_time_get_set(self):
        """Test jmi.Model.[set|get]_t(...)."""
        new_time = 0.47
        reset = 0
        self.vdp.t = reset
        t = self.vdp.t
        nose.tools.assert_almost_equal(reset, t)
        self.vdp.t = new_time
        t = self.vdp.t
        nose.tools.assert_almost_equal(new_time, t)
    
    @testattr(stddist = True)   
    def test_evaluation(self):
        """Test jmi.Model.eval_ode_f()."""
        self.vdp.dx = [0, 0, 0]
        self.vdp.eval_ode_f()
        all_zeros = True
        for value in self.vdp.dx:
            if value != 0:
                all_zeros = False
                
        assert not all_zeros
            
    def test_optimization_cost_eval(self):
        """Test evaluation of optimization cost function."""
        simulator = SundialsODESimulator(self.m)
        simulator.run()
        T, ys = simulator.get_solution()
        
        self.vdp.set_x_p(ys[-1], 0)
        self.vdp.set_dx_p(self.vdp.dx, 0)
        cost = self.vdp.opt_eval_J()
        nose.tools.assert_not_equal(cost, 0)
        
    def test_optimization_cost_jacobian(self):
        """Test evaluation of optimization cost function jacobian.
        
        Note:
        This test is model specific for the VDP oscillator.
        """
        simulator = SundialsODESimulator(self.m)
        simulator.run()
        T, ys = simulator.get_solution()
        
        self.vdp.set_x_p(ys[-1], 0)
        self.vdp.set_dx_p(self.vdp.dx, 0)
        jac = self.vdp.opt_eval_jac_J(jmi.JMI_DER_X_P)
        N.testing.assert_almost_equal(jac, [[0, 0, 1]])
    
    @testattr(stddist = True)    
    def test_setget_value(self):
        """ Test set and get a value of a variable or parameter. """
        parameter = 'p1'
        # set_value
        new_value = 2.0
        self.vdp.set_value(parameter, new_value)
        nose.tools.assert_equal(self.vdp.get_value(parameter), new_value)

    @testattr(stddist = True)        
    def test_setget_values(self):
        """ Test set and get a list of variables or parameters."""
        parameters = ['p1', 'p2', 'p3']
        real_values = [0.0, 0.0, 0.0]
        # set_values
        new_values = [1.0, 2.0, 3.0]
        self.vdp.set_values(parameters, new_values)
        for index, val in enumerate(new_values):
            nose.tools.assert_equal(val, self.vdp.get_value(parameters[index]))
            
####### This test was commented out in r1153?
# #    @testattr(stddist = True)
# #    def test_writeload_parameters_from_XML(self):
# #        original_values = self.vdp.get_pi()
# #        new_values = N.ones(3)
# #        self.vdp.set_pi(new_values)
# #
# #        # new values are set
# #        N.testing.assert_array_equal(self.vdp.get_pi(),new_values)
# #        
# #        #load original values, pi are now = old values
# #        self.vdp.load_parameters_from_XML()
# #        N.testing.assert_array_equal(self.vdp.get_pi(),original_values)
# #        
# #        # set new values and write to xml
# #        self.vdp.set_pi(new_values)
# #        self.vdp.write_parameters_to_XML()
# #        
# #        #load values, pi are now = new values
# #        self.vdp.load_parameters_from_XML()
# #        N.testing.assert_array_equal(self.vdp.get_pi(),new_values)

##### This test was added in r1153 but results in seg fault on Mac
##### Commented out in r1154.
#     @testattr(stddist = True)
#     def test_writeload_params_from_XML(self):
#         original_values = self.vdp.get_pi()
#         new_values = N.ones(3)
#         self.vdp.set_pi(new_values)

#         # new values are set
#         N.testing.assert_array_equal(self.vdp.get_pi(),new_values)
        
#         #load original values, pi are now = old values
#         self.vdp.load_parameters_from_XML()
#         N.testing.assert_array_equal(self.vdp.get_pi(),original_values)
        
#         # set new values and write to xml
#         self.vdp.set_pi(new_values)
#         self.vdp.write_parameters_to_XML("test_jmi.xml")
        
#         #load values, pi are now = new values
#         self.vdp.load_parameters_from_XML("test_jmi.xml")
#         N.testing.assert_array_equal(self.vdp.get_pi(),new_values)
        
#         #load original values, pi are now = old values
#         self.vdp.load_parameters_from_XML()
#         N.testing.assert_array_equal(self.vdp.get_pi(),original_values)        
            
    @testattr(stddist = True)        
    def test_get_name(self):
        ntools.assert_equal(self.vdp.get_name(),"VDP_pack_VDP_Opt")
    
    @testattr(stddist = True)    
    def test_opt_interval_starttime_free(self):
        ntools.assert_equal(self.vdp.opt_interval_starttime_free(),False)
    
    @testattr(stddist = True)    
    def test_opt_interval_starttime_fixed(self):
        ntools.assert_equal(self.vdp.opt_interval_starttime_fixed(),True)
    
    @testattr(stddist = True)        
    def test_opt_interval_finaltime_free(self):
        ntools.assert_equal(self.vdp.opt_interval_finaltime_free(),False)
    
    @testattr(stddist = True)    
    def test_opt_interval_finaltime_fixed(self):
        ntools.assert_equal(self.vdp.opt_interval_finaltime_fixed(),True)
    
    @testattr(stddist = True)   
    def test_opt_interval_get_start_time(self):
        ntools.assert_equal(self.vdp.opt_interval_get_start_time(),0.0)
    
    @testattr(stddist = True)   
    def test_opt_interval_get_final_time(self):
        ntools.assert_equal(self.vdp.opt_interval_get_final_time(),20.0)
        
class TestModel_CSTR:
    """Test the high level model class, jmi.Model with alias variables 
        enabled.
    
    The tests are based on the CSTR example file.

    """
    
    def __init__(self):
        """Load the test model."""
        # Load the dynamic library and XML data
        self.cstr = jmi.Model(fname_cstr)

    @testattr(stddist = True)
    def test_get_variable_description(self):
        ntools.assert_equal(self.cstr.get_variable_description("cstr.F0"),"Inflow")
        
    @testattr(stddist = True)
    def test_get_variable_descriptions(self):
        descriptions = self.cstr.get_variable_descriptions()
        ntools.assert_equal(descriptions.get(2),"Outflow")

    @testattr(stddist = True)
    def test_is_negated_alias(self):
        ntools.assert_equal(self.cstr.is_negated_alias("cstr.Tc"),False)
    
    @testattr(stddist = True)
    def test_get_aliases(self):
        (aliases,isalias) = self.cstr.get_aliases("u")
        ntools.assert_equal(aliases[0],"cstr.Tc")
        ntools.assert_equal(isalias[0],False)
            
    @testattr(stddist = True)
    def test_setget_alias_value(self):
       """ Test set and get the value of a alias variable. """ 
       alias_variable = 'cstr.Tc'
       aliased_variable = 'u'
       u = self.cstr.get_value(aliased_variable)
       tc = self.cstr.get_value(alias_variable)
       nose.tools.assert_equal(u, tc)
       new_value = 345.0
       self.cstr.set_value(alias_variable, new_value)
       nose.tools.assert_equal(self.cstr.get_value(aliased_variable), new_value)
       

class TestJMIModel_VDP:
    """ Test the JMI Model Interface wrappers.
    (Low-level jmodelica interfaces.)

    The correctness of the methods are not really tested here, only that they can
    be called without crashing and in some cases that return value has at least the
    correct type.
    
    """
    def __init__(self):
        # Load the dynamic library and XML data
        self.vdp = jmi.Model(fname_vdp)                

    @testattr(stddist = True)
    def test_initAD(self):
        """ Test JMIModel.initAD method. """
        self.vdp.jmimodel.initAD()

    @testattr(stddist = True)
    def test_get_sizes(self):
        """ Test JMIModel.get_sizes method. """
        n_ci = ct.c_int()
        n_cd = ct.c_int()
        n_pi = ct.c_int()
        n_pd = ct.c_int()
        n_dx = ct.c_int()
        n_x  = ct.c_int()
        n_u  = ct.c_int()
        n_w  = ct.c_int()
        n_tp = ct.c_int()
        n_sw = ct.c_int()
        n_sw_init = ct.c_int()
        n_z  = ct.c_int()
        self.vdp.jmimodel.get_sizes(n_ci, n_cd, n_pi, n_pd, n_dx, n_x, n_u, n_w, n_tp, n_sw, n_sw_init, n_z)

    @testattr(stddist = True)
    def test_get_offsets(self):
        """ Test JMIModel.get_offsets method. """
        offs_ci = ct.c_int()
        offs_cd = ct.c_int()
        offs_pi = ct.c_int()
        offs_pd = ct.c_int()
        offs_dx = ct.c_int()
        offs_x = ct.c_int()
        offs_u = ct.c_int()
        offs_w = ct.c_int()
        offs_t = ct.c_int()
        offs_dx_p = ct.c_int()
        offs_x_p = ct.c_int()
        offs_u_p = ct.c_int()
        offs_w_p = ct.c_int()
        offs_sw = ct.c_int()
        offs_sw_init = ct.c_int()   
        self.vdp.jmimodel.get_offsets(offs_ci, offs_cd, offs_pi, offs_pd, offs_dx, offs_x, offs_u, 
                          offs_w, offs_t, offs_dx_p, offs_x_p, offs_u_p, offs_w_p, offs_sw, offs_sw_init)
        
    @testattr(stddist = True)
    def test_get_n_tp(self):
        """ Test JMIModel.get_n_tp method. """
        n_tp = ct.c_int()
        self.vdp.jmimodel.get_n_tp(n_tp)    
    
    @testattr(stddist = True)
    def test_getset_tp(self):
        """ Test JMIModel.get_tp and JMIModel.set_tp method. """
        n_tp = ct.c_int()
        self.vdp.jmimodel.get_n_tp(n_tp)
        #set tp
        set_tp = N.zeros(n_tp.value)
        for i in range(n_tp.value):
            set_tp[i]=i+1
        self.vdp.jmimodel.set_tp(set_tp) 
        #get tp
        get_tp = N.zeros(n_tp.value)
        self.vdp.jmimodel.get_tp(get_tp)
        for j in range(n_tp.value):
            if set_tp[j] != get_tp[j]:
                assert False, "value set with set_tp was not the same as returned by get_tp"   
    
    @testattr(stddist = True)
    def test_get_z(self):
        """ Test JMIModel.get_z method. """
        assert isinstance(self.vdp.jmimodel.get_z(), N.ndarray),\
            "JMIModel.get_z did not return numpy.ndarray."
        
    @testattr(stddist = True)
    def test_get_ci(self):
        """ Test JMIModel.get_ci method. """
        assert isinstance(self.vdp.jmimodel.get_ci(), N.ndarray),\
            "JMIModel.get_ci did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_cd(self):
        """ Test JMIModel.get_cd method. """
        assert isinstance(self.vdp.jmimodel.get_cd(), N.ndarray),\
            "JMIModel.get_cd did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_pi(self):
        """ Test JMIModel.get_pi method. """
        assert isinstance(self.vdp.jmimodel.get_pi(), N.ndarray),\
            "JMIModel.get_pi did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_pd(self):
        """ Test JMIModel.get_pd method. """
        assert isinstance(self.vdp.jmimodel.get_pd(), N.ndarray),\
            "JMIModel.get_pd did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_dx(self):
        """ Test JMIModel.get_dx method. """
        assert isinstance(self.vdp.jmimodel.get_dx(), N.ndarray),\
            "JMIModel.get_dx did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_x(self):
        """ Test JMIModel.get_x method. """
        assert isinstance(self.vdp.jmimodel.get_x(), N.ndarray),\
            "JMIModel.get_x did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_u(self):
        """ Test JMIModel.get_u method. """
        assert isinstance(self.vdp.jmimodel.get_u(), N.ndarray),\
            "JMIModel.get_u did not return numpy.ndarray."
    
    @testattr(stddist = True)
    def test_get_w(self):
        """ Test JMIModel.get_w method. """
        assert isinstance(self.vdp.jmimodel.get_w(), N.ndarray),\
            "JMIModel.get_w did not return numpy.ndarray. "
    
    @testattr(stddist = True)
    def test_get_t(self):
        """ Test JMIModel.get_t method. """
        assert isinstance(self.vdp.jmimodel.get_t(), N.ndarray),\
            "JMIModel.get_t did not return numpy.ndarray. "
    
    @testattr(stddist = True)
    def test_get_dx_p(self):
        """ Test JMIModel.get_dx_p method. """
        assert isinstance(self.vdp.jmimodel.get_dx_p(0), N.ndarray), \
            "JMIModel.get_dx_p(i) for i=0 did not return numpy.ndarray. "
    
    @testattr(stddist = True)
    def test_get_x_p(self):
        """ Test JMIModel.get_x_p method. """
        assert isinstance(self.vdp.jmimodel.get_x_p(0), N.ndarray), \
            "JMIModel.get_x_p(i) for i=0 did not return numpy.ndarray. "
    
    @testattr(stddist = True)
    def test_get_u_p(self):
        """ Test JMIModel.get_u_p method. """
        assert isinstance(self.vdp.jmimodel.get_u_p(0), N.ndarray), \
            "JMIModel.get_u_p(i) for i=0 did not return numpy.ndarray. " 
    
    @testattr(stddist = True)
    def test_get_w_p(self):
        """ Test JMIModel.get_w_p method. """
        assert isinstance(self.vdp.jmimodel.get_w_p(0), N.ndarray), \
            "JMIModel.get_w_p(i) for i=0 did not return numpy.ndarray. "
    
    #@testattr(stddist = True)
    #def test_ode_f():
    #    """ Test JMIModel.ode_f method. """
    #    model = jmi.JMIModel(fname, '.')
    #    model.ode_f()
    #    
    #
    #@testattr(stddist = True)
    #def test_ode_df():
    #    """ Test JMIModel.ode_f method. """
    #    model = jmi.JMIModel(fname, '.')
    #
    #
    #@testattr(stddist = True)
    #def test_ode_df_n_nz():
    #    """ Test JMIModel.ode_df_n_nz method. """
    #    model = jmi.JMIModel(fname, '.')
    # 
    #
    #@testattr(stddist = True)
    #def test_ode_df_nz_indices():
    #    """ Test JMIModel.ode_df_nz_indices method. """
    #    model = jmi.JMIModel(fname, '.')
    #
    #
    #@testattr(stddist = True)
    #def test_ode_df_dim():
    #    """ Test JMIModel.ode_df_dim method. """
    #    model = jmi.JMIModel('.')
    
    
    @testattr(stddist = True)
    def test_dae_get_sizes(self):
        """ Test JMIModel.dae_get_sizes method. """
        n_eq_F, n_eq_R = self.vdp.jmimodel.dae_get_sizes()
      
    @testattr(stddist = True)
    def test_dae_F(self):
        """ Test JMIModel.dae_F method. """
        size_F,size_R = self.vdp.jmimodel.dae_get_sizes()
        res = N.zeros(size_F)
        self.vdp.jmimodel.dae_F(res)
    
    @testattr(stddist = True)
    def test_dae_dF(self):
        """ Test JMIModel.dae_dF method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        jac = N.zeros(self.vdp.jmimodel.get_z().size)
        self.vdp.jmimodel.dae_dF(eval_alg,sparsity,indep_vars,mask,jac)
        
    @testattr(stddist = True)
    def test_dae_dF_n_nz(self):
        """ Test JMIModel.dae_dF_n_nz method. """
        self.vdp.jmimodel.dae_dF_n_nz(eval_alg)
    
    @testattr(stddist = True)
    def test_dae_dF_nz_indices(self):
        """ Test JMIModel.dae_dF_nz_indices method. """ 
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        nnz = self.vdp.jmimodel.dae_dF_n_nz(eval_alg)
        row = N.ndarray(nnz, dtype=int)
        col = N.ndarray(nnz, dtype=int)
        self.vdp.jmimodel.dae_dF_nz_indices(eval_alg, indep_vars, mask, row, col)
    
    @testattr(stddist = True)
    def test_dae_dF_dim(self):
        """ Test JMIModel.dae_dF_dim method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        n_cols, n_n_nz = self.vdp.jmimodel.dae_dF_dim(eval_alg, sparsity, indep_vars, mask)
        
    @testattr(stddist = True)
    def test_dae_R(self):
        """ Test JMIModel.dae_R method. """
        size_F, size_R = self.vdp.jmimodel.dae_get_sizes()
        res = N.zeros(size_R)
        self.vdp.jmimodel.dae_R(res)
    
    @testattr(stddist = True)
    def test_init_get_sizes(self):
        """ Test JMIModel.init_get_sizes method. """
        n_eq_f0, n_eq_f1, n_eq_fp, n_eq_r0 = self.vdp.jmimodel.init_get_sizes()
    
    @testattr(stddist = True)
    def test_init_F0(self):
        """ Test JMIModel.init_FO method. """
        n_eq_f0, n_eq_f1, n_eq_fp, n_eq_r0 = self.vdp.jmimodel.init_get_sizes()
        res = N.zeros(n_eq_f0)
        self.vdp.jmimodel.init_F0(res)
    
    @testattr(stddist = True)
    def test_init_dF0(self):
        """ Test JMIModel.init_dF0 method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        jac = N.zeros(self.vdp.jmimodel.get_z().size)
        self.vdp.jmimodel.init_dF0(eval_alg, sparsity, indep_vars, mask, jac)
    
    @testattr(stddist = True)
    def test_init_dF0_n_nz(self):
        """ Test JMIModel.init_dF0_n_nz method. """
        n_nz = self.vdp.jmimodel.init_dF0_n_nz(eval_alg)
    
    @testattr(stddist = True)
    def test_init_dF0_nz_indices(self):
        """ Test JMIModel.init_dF0_nz_indices method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        nnz = self.vdp.jmimodel.init_dF0_n_nz(eval_alg)
        row = N.ndarray(nnz, dtype=int)
        col = N.ndarray(nnz, dtype=int)
        self.vdp.jmimodel.init_dF0_nz_indices(eval_alg, indep_vars, mask, row, col)
    
    @testattr(stddist = True)
    def test_init_dF0_dim(self):
        """ Test JMIModel.init_dF0_dim method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        dF_n_cols, dF_n_nz = self.vdp.jmimodel.init_dF0_dim(eval_alg, sparsity, indep_vars,
                                                mask)
    
    @testattr(stddist = True)
    def test_init_F1(self):
        """ Test JMIModel.init_F1 method. """
        n_eq_f0, n_eq_f1, n_eq_fp, n_eq_r0 = self.vdp.jmimodel.init_get_sizes()
        res = N.zeros(n_eq_f1)
        self.vdp.jmimodel.init_F1(res)
    
    @testattr(stddist = True)
    def test_init_dF1(self):
        """ Test JMIModel.init_dF1 method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        jac = N.zeros(self.vdp.jmimodel.get_z().size)
        self.vdp.jmimodel.init_dF1(eval_alg, sparsity, indep_vars, mask, jac)
    
    @testattr(stddist = True)
    def test_init_dF1_n_nz(self):
        """ Test JMIModel.init_dF1_n_nz method. """
        n_nz = self.vdp.jmimodel.init_dF1_n_nz(eval_alg)
    
    @testattr(stddist = True)
    def test_init_dF1_nz_indices(self):
        """ Test JMIModel.init_dF1_nz_indices method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        nnz = self.vdp.jmimodel.init_dF1_n_nz(eval_alg)
        row = N.ndarray(nnz, dtype=int)
        col = N.ndarray(nnz, dtype=int)
        self.vdp.jmimodel.init_dF1_nz_indices(eval_alg, indep_vars, mask, row, col)
    
    @testattr(stddist = True)
    def test_init_dF1_dim(self):
        """ Test JMIModel.init_dF1_dim method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        dF_n_cols, dF_n_nz = self.vdp.jmimodel.init_dF1_dim(eval_alg, sparsity, indep_vars,
                                                mask) 
    @testattr(stddist = True)
    def test_init_R0(self):
        """ Test JMIModel.init_R0 method. """
        n_eq_f0, n_eq_f1, n_eq_fp, n_eq_r0 = self.vdp.jmimodel.init_get_sizes()
        res = N.zeros(n_eq_r0)
        self.vdp.jmimodel.init_R0(res)
    
    #@testattr(stddist = True)
    #def test_init_Fp():
    #    """ Test JMIModel.init_Fp method. """
    #    model = mc.getjmimodel()
    #    n_eq_f0, n_eq_f1, n_eq_fp = model.init_get_sizes()
    #    res = n.zeros(n_eq_fp)
    #    model.init_Fp(res)
    #    
    #
    #@testattr(stddist = True)
    #def test_init_dFp():
    #    """ Test JMIModel.init_dFp method. """
    #    model = mc.getjmimodel()
    #    n_eq_f0, n_eq_f1, n_eq_fp = model.init_get_sizes()
    #    if n_eq_fp > 0:
    #        mask = n.ones(model.get_z().size, dtype=int)
    #        jac = n.zeros(model.get_z().size)
    #        model.init_dFp(eval_alg, sparsity, indep_vars, mask, jac)
    #    else:
    #        assert False, "Cannot perform test, size of Fp is 0. "
    #    
    #
    #@testattr(stddist = True)
    #def test_init_dFp_n_nz():
    #    """ Test JMIModel.init_dFp_n_nz method. """
    #    model = mc.getjmimodel()
    #    n_eq_f0, n_eq_f1, n_eq_fp = model.init_get_sizes()
    #    if n_eq_fp > 0:
    #        n_nz = model.init_dFp_n_nz(eval_alg)
    #    else:
    #        assert False, "Cannot perform test, size of Fp is 0. "
    #    
    #
    #@testattr(stddist = True)
    #def test_init_dFp_nz_indices():
    #    """ Test JMIModel.init_dFp_nz_indices method. """
    #    model = mc.getjmimodel()
    #    n_eq_f0, n_eq_f1, n_eq_fp = model.init_get_sizes()
    #    if n_eq_fp > 0:
    #        mask = n.ones(model.get_z().size, dtype=int)
    #        nnz = model.init_dFp_n_nz(eval_alg)
    #        row = n.ndarray(nnz, dtype=int)
    #        col = n.ndarray(nnz, dtype=int)
    #        model.init_dFp_nz_indices(eval_alg, indep_vars, mask, row, col)
    #    else:
    #       assert False, "Cannot perform test, size of Fp is 0. " 
    #    
    #
    #@testattr(stddist = True)
    #def test_init_dFp_dim():
    #    """ Test JMIModel.init_dFp_dim method. """
    #    model = mc.getjmimodel()
    #    n_eq_f0, n_eq_f1, n_eq_fp = model.init_get_sizes()
    #    if n_eq_fp > 0:
    #        mask = n.ones(model.get_z().size, dtype=int)
    #        dF_n_cols, dF_n_nz = model.init_dFp_dim(eval_alg, sparsity,
    #                                                 indep_vars, mask) 
    #    else:
    #        assert False, "Cannot perform test, size of Fp is 0. "
    
    
    @testattr(stddist = True)
    def test_opt_getset_optimization_interval(self):
        """Test JMIModel.opt_[set|get]_optimization_interval methods."""
        st_set = ct.c_double(5)
        # 0 = fixed, 1 = free (free NOT YET SUPPORTED)
        stf_set = ct.c_int(0)
        ft_set = ct.c_double(20)
        # 0 = fixed, 1 = free (free NOT YET SUPPORTED)
        ftf_set = ct.c_int(0)
        self.vdp.jmimodel.opt_set_optimization_interval(st_set, stf_set, ft_set, ftf_set)
        st_get, stf_get, ft_get, ftf_get = self.vdp.jmimodel.opt_get_optimization_interval()
        
        nose.tools.assert_equal(st_set.value, st_get)
        nose.tools.assert_equal(stf_set.value, stf_get)
        nose.tools.assert_equal(ft_set.value, ft_get)
        nose.tools.assert_equal(ftf_set.value, ftf_get)
    
    @testattr(stddist = True)
    def test_opt_get_n_p_opt(self):
        """ Test opt_get_n_p_opt method. """
        assert isinstance(self.vdp.jmimodel.opt_get_n_p_opt(), int),\
            "Method does not return int."
    
    @testattr(stddist = True)
    def test_opt_getset_p_opt_indices(self):
        """ Test JMIModel.opt_set_p_opt_indices method. """
        n_pi = self.vdp.jmimodel.get_pi().size
        if n_pi > 0:
            # test set
            set_indices = N.zeros(1, dtype=int)
            set_indices[0]=0
            self.vdp.jmimodel.opt_set_p_opt_indices(1, set_indices)
            #test get
            get_indices = N.ones(1, dtype=int)
            self.vdp.jmimodel.opt_get_p_opt_indices(get_indices)
            nose.tools.assert_equal(self.vdp.jmimodel.opt_get_n_p_opt(), 1)
            nose.tools.assert_equal(set_indices[0], get_indices[0])
        else:
            assert False, "pi vector is empty"    
    
    @testattr(stddist = True)
    def test_opt_get_sizes(self):
        """ Test opt_get_sizes method. """
        n_eq_ceq, n_eq_cineq, n_eq_heq, n_eq_hineq = self.vdp.jmimodel.opt_get_sizes()
    
    @testattr(stddist = True)
    def test_opt_J(self):
        """ Test opt_J method. """
        self.vdp.jmimodel.opt_J()
        
    @testattr(stddist = True)
    def test_opt_dJ(self):
        """ Test opt_dJ method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        jac = N.zeros(self.vdp.jmimodel.get_z().size)
        self.vdp.jmimodel.opt_dJ(eval_alg, sparsity, indep_vars, mask, jac)
    
    @testattr(stddist = True)
    def test_opt_dJ_n_nz(self):
        """ Test opt_dJ_n_nz method. """
        assert isinstance(self.vdp.jmimodel.opt_dJ_n_nz(eval_alg), int),\
            "Method does not return int."
    
    @testattr(stddist = True)
    def test_opt_dJ_nz_indices(self):
        """ Test opt_dJ_nz_indices method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        nnz = self.vdp.jmimodel.opt_dJ_n_nz(eval_alg)
        row = N.ndarray(nnz, dtype=int)
        col = N.ndarray(nnz, dtype=int)
        self.vdp.jmimodel.opt_dJ_nz_indices(eval_alg, indep_vars, mask, row, col)
    
    @testattr(stddist = True)
    def test_opt_dJ_dim(self):
        """ Test opt_dJ_dim method. """
        mask = N.ones(self.vdp.jmimodel.get_z().size, dtype=int)
        dJ_n_cols, dJ_n_nz = self.vdp.jmimodel.init_dF0_dim(eval_alg, sparsity, indep_vars,
                                                mask)        
    
    @testattr(stddist = True)
    def test_Model_dae_get_sizes(self):
        """ Test of the dae_get_sizes in Model
        """   
        res_n_eq_F = 3
        n_eq_F, n_eq_R = self.vdp.jmimodel.dae_get_sizes()
        assert n_eq_F==res_n_eq_F, \
               "test_jmi.py: test_Model_dae_get_sizes: Wrong number of DAE equations." 
    
        res_n_eq_F0 = 6
        res_n_eq_F1 = 7
        res_n_eq_Fp = 0
        res_n_eq_R0 = 0
        n_eq_F0,n_eq_F1,n_eq_Fp,n_eq_R0 = self.vdp.jmimodel.init_get_sizes()
        assert n_eq_F0==res_n_eq_F0 and n_eq_F1==res_n_eq_F1 and n_eq_Fp==res_n_eq_Fp and n_eq_R0==res_n_eq_R0, \
               "test_jmi.py: test_Model_dae_get_sizes: Wrong number of DAE initialization equations." 
    
        res_n_eq_Ceq = 0
        res_n_eq_Cineq = 1
        res_n_eq_Heq = 0
        res_n_eq_Hineq = 0
        
        n_eq_Ceq,n_eq_Cineq,n_eq_Heq,n_eq_Hineq = self.vdp.jmimodel.opt_get_sizes()
    
        assert n_eq_Ceq==res_n_eq_Ceq and n_eq_Cineq==res_n_eq_Cineq and n_eq_Heq==res_n_eq_Heq and n_eq_Hineq==res_n_eq_Hineq,  \
               "test_jmi.py: test_Model_dae_get_sizes: Wrong number of constraints." 
    
    
    @testattr(stddist = True)
    def test_state_start_values_fixed(self):
        """ Test of the compiler option state_start_values_fixed
        """
        """ Test of the dae_get_sizes in Model
        """
        
        model = os.path.join("files", "VDP_pack.mo")
        fpath = os.path.join(path_to_tests, model)
        cpath = "VDP_pack.VDP"
        fname = cpath.replace('.','_',1)
    
        mc = ModelicaCompiler()
        
        mc.set_boolean_option('state_start_values_fixed',False)
    
        mc.compile_model(fpath, cpath)
    
        # Load the dynamic library and XML data
        vdp = jmi.Model(fname)
    
        res_n_eq_F = 2
        n_eq_F, n_eq_R = vdp.jmimodel.dae_get_sizes()
        assert n_eq_F==res_n_eq_F, \
               "test_jmi.py: test_Model_dae_get_sizes: Wrong number of DAE equations." 
    
        res_n_eq_F0 = 2
        res_n_eq_F1 = 5
        res_n_eq_Fp = 0
        res_n_eq_R0 = 0
        n_eq_F0,n_eq_F1,n_eq_Fp, n_eq_R0 = vdp.jmimodel.init_get_sizes()
        assert n_eq_F0==res_n_eq_F0 and n_eq_F1==res_n_eq_F1 and n_eq_Fp==res_n_eq_Fp and n_eq_R0==res_n_eq_R0, \
               "test_jmi.py: test_Model_dae_get_sizes: Wrong number of DAE initialization equations."
               
class TestModelSimulation:
    """Test the JMIModel instance of the Van der Pol oscillator."""
    
    def __init__(self):
        """Test setUp. Load the test model."""
        self.vdp = jmi.Model(fname_vdp)
        
    def test_opt_jac_non_zeros(self):
        """Testing the number of non-zero elements in VDP after simulation.
        
        Note:
        This test is model specific and not generic as most other
        tests in this class.
        """
        simulator = SundialsODESimulator(self.vdp)
        simulator.run()
        
        assert self.vdp.jmimodel._n_z > 0, "Length of z should be greater than zero."
        print 'n_z.value:', self.vdp.jmimodel._n_z.value
        n_cols, n_nz = self.vdp.jmimodel.opt_dJ_dim(jmi.JMI_DER_CPPAD,
                                                    jmi.JMI_DER_SPARSE,
                                                    jmi.JMI_DER_X_P,
                                                    n.ones(self.vdp.jmimodel._n_z.value,
                                                           dtype=int))
        
        print 'n_nz:', n_nz
        
        assert n_cols > 0, "The resulting should at least of one column."
        assert n_nz > 0, "The resulting jacobian should at least have" \
                         " one element (structurally) non-zero."

    
      
