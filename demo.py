"""
A simple 2-node simulation demonstration the application of GP-CaKe. Of particular interest are the covariance parameters
that define the constraints on the posterior shape of the causal kernels.

References:
    Ambrogioni, L., Hinne, M., van Gerven, M., & Maris, E. (2017). GP CaKe: Effective brain connectivity with causal kernels,
    pp. 1–10. Retrieved from http://arxiv.org/abs/1705.05603

Last updated on July 6th, 2017.
"""

import numpy as np
#import importlib

"""
Simulation and GP-CaKe packages.
"""

import simulator as sim
import gpcake
import utility

from time import time

tics = []

def tic():
    tics.append(time())

def toc():
    if len(tics)==0:
        return None
    else:
        return time() - tics.pop()

#importlib.reload(gpcake)

import argparse




"""
Simulation parameters. Here, we construct a 2-node graph with one connection (with max. strength <connection_strength>).
We create a 4 second time series per node, with a sampling rate of 100 Hz.
"""

p                       = 2
adj_mat                 = np.zeros((p,p))
adj_mat[0,1]            = 1
connection_strength     = 1.0
time_step               = 0.01
time_period             = 4.
time_range              = np.arange(-time_period / 2, time_period / 2, time_step)
n                       = int(time_period / time_step)
simulation_params       = {'network'                : adj_mat,
                           'connection_strength'    : connection_strength,
                           'time_step'              : time_step,
                           'time_period'            : time_period}

"""
Simulation settings. We generate <ntrials_train> trials to train the dynamic parameters on,
and <ntrials_test> to learn the GP posterior.
"""

ntrials_train                                       = 30
ntrials_test                                        = 30
simulation                                          = sim.integroDifferential_simulator()
print('Generating simulation samples')
(training_samples, testing_samples, ground_truth)   = simulation.simulate_network_dynamics(ntrials_train, ntrials_test, simulation_params)

"""
Plot a few samples to see the generated time series.
"""

utility.plot_samples(training_samples[0:3])

"""
Simulation is done. Time to bake some cake!
"""

cake = gpcake.gpcake()
cake.initialize_time_parameters(time_step, time_period)
cake.dynamic_parameters["number_sources"] = p

"""
Select internal dynamics type. Currently implemented are "Relaxation" and "Oscillation".
"""

cake.dynamic_type = "Relaxation"


"""
Optimize the univariate likelihoods for each node for the dynamic parameters using a grid search.
"""

dynamic_parameters_range = {}
dynamic_parameters_range["relaxation_constant"] = {}
dynamic_parameters_range["relaxation_constant"]["step"] = 2
dynamic_parameters_range["relaxation_constant"]["min"] = 20
dynamic_parameters_range["relaxation_constant"]["max"] = 50
dynamic_parameters_range["amplitude"] = {}
dynamic_parameters_range["amplitude"]["step"] = 0.001
dynamic_parameters_range["amplitude"]["min"] = 0.005
dynamic_parameters_range["amplitude"]["max"] = 0.015

print('Learning dynamic parameters')
cake.learn_dynamic_parameters(training_samples, dynamic_parameters_range)

"""
Set the parameters of the causal kernel.
"""

cake.covariance_parameters = {  "time_scale"        : 0.15,     # Temporal smoothing
                                "time_shift"        : 0.05,     # Temporal offset
                                "causal"            : "yes",    # Hilbert transform
                                "spectral_smoothing": np.pi }   # Temporal localization
cake.noise_level = 0.05

"""
Compute the posteriors for each of the p*(p-1) connections.
"""

print('Computing posterior kernels')
connectivity = cake.run_analysis(testing_samples)


"""
Visualize the posterior kernels
"""
utility.plot_connectivity(ground_truth, connectivity, time_range, t0=-0.5)
