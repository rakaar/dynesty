#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilities for handling results.

"""

import sys
import numpy as np
import shutil

__all__ = ["Results", "print_fn"]


def print_fn(results,
             niter,
             ncall,
             add_live_it=None,
             dlogz=None,
             stop_val=None,
             nbatch=None,
             logl_min=-np.inf,
             logl_max=np.inf,
             pbar=None):
    """
    The default function used to print out results in real time.

    Parameters
    ----------

    results : tuple
        Collection of variables output from the current state of the sampler.
        Currently includes:
        (1) particle index,
        (2) unit cube position,
        (3) parameter position,
        (4) ln(likelihood),
        (5) ln(volume),
        (6) ln(weight),
        (7) ln(evidence),
        (8) Var[ln(evidence)],
        (9) information,
        (10) number of (current) function calls,
        (11) iteration when the point was originally proposed,
        (12) index of the bounding object originally proposed from,
        (13) index of the bounding object active at a given iteration,
        (14) cumulative efficiency, and
        (15) estimated remaining ln(evidence).

    niter : int
        The current iteration of the sampler.

    ncall : int
        The total number of function calls at the current iteration.

    add_live_it : int, optional
        If the last set of live points are being added explicitly, this
        quantity tracks the sorted index of the current live point being added.

    dlogz : float, optional
        The evidence stopping criterion. If not provided, the provided
        stopping value will be used instead.

    stop_val : float, optional
        The current stopping criterion (for dynamic nested sampling). Used if
        the `dlogz` value is not specified.

    nbatch : int, optional
        The current batch (for dynamic nested sampling).

    logl_min : float, optional
        The minimum log-likelihood used when starting sampling. Default is
        `-np.inf`.

    logl_max : float, optional
        The maximum log-likelihood used when stopping sampling. Default is
        `np.inf`.

    """
    if pbar is None:
        print_fn_fallback(results,
                          niter,
                          ncall,
                          add_live_it=add_live_it,
                          dlogz=dlogz,
                          stop_val=stop_val,
                          nbatch=nbatch,
                          logl_min=logl_min,
                          logl_max=logl_max)
    else:
        print_fn_tqdm(pbar,
                      results,
                      niter,
                      ncall,
                      add_live_it=add_live_it,
                      dlogz=dlogz,
                      stop_val=stop_val,
                      nbatch=nbatch,
                      logl_min=logl_min,
                      logl_max=logl_max)


def get_print_fn_args(results,
                      niter,
                      ncall,
                      add_live_it=None,
                      dlogz=None,
                      stop_val=None,
                      nbatch=None,
                      logl_min=-np.inf,
                      logl_max=np.inf):
    # Extract results at the current iteration.
    loglstar = results.loglstar
    logz = results.logz
    logzvar = results.logzvar
    delta_logz = results.delta_logz
    bounditer = results.bounditer
    nc = results.nc
    eff = results.eff

    # Adjusting outputs for printing.
    if delta_logz > 1e6:
        delta_logz = np.inf
    if logzvar >= 0. and logzvar <= 1e6:
        logzerr = np.sqrt(logzvar)
    else:
        logzerr = np.nan
    if logz <= -1e6:
        logz = -np.inf
    if loglstar <= -1e6:
        loglstar = -np.inf

    # Constructing output.
    long_str = []
    # long_str.append("iter: {:d}".format(niter))
    if add_live_it is not None:
        long_str.append("+{:d}".format(add_live_it))
    short_str = list(long_str)
    if nbatch is not None:
        long_str.append("batch: {:d}".format(nbatch))
    long_str.append("bound: {:d}".format(bounditer))
    long_str.append("nc: {:d}".format(nc))
    long_str.append("ncall: {:d}".format(ncall))
    long_str.append("eff(%): {:6.3f}".format(eff))
    short_str.append(long_str[-1])
    long_str.append("loglstar: {:6.3f} < {:6.3f} < {:6.3f}".format(
        logl_min, loglstar, logl_max))
    short_str.append("logl*: {:6.1f}<{:6.1f}<{:6.1f}".format(
        logl_min, loglstar, logl_max))
    long_str.append("logz: {:6.3f} +/- {:6.3f}".format(logz, logzerr))
    short_str.append("logz: {:6.1f}+/-{:.1f}".format(logz, logzerr))
    mid_str = list(short_str)
    if dlogz is not None:
        long_str.append("dlogz: {:6.3f} > {:6.3f}".format(delta_logz, dlogz))
        mid_str.append("dlogz: {:6.1f}>{:6.1f}".format(delta_logz, dlogz))
    else:
        long_str.append("stop: {:6.3f}".format(stop_val))
        mid_str.append("stop: {:6.3f}".format(stop_val))

    return niter, short_str, mid_str, long_str


def print_fn_tqdm(pbar,
                  results,
                  niter,
                  ncall,
                  add_live_it=None,
                  dlogz=None,
                  stop_val=None,
                  nbatch=None,
                  logl_min=-np.inf,
                  logl_max=np.inf):
    niter, short_str, mid_str, long_str = get_print_fn_args(
        results,
        niter,
        ncall,
        add_live_it=add_live_it,
        dlogz=dlogz,
        stop_val=stop_val,
        nbatch=nbatch,
        logl_min=logl_min,
        logl_max=logl_max)

    pbar.set_postfix_str(" | ".join(long_str), refresh=False)
    pbar.update(niter - pbar.n)


def print_fn_fallback(results,
                      niter,
                      ncall,
                      add_live_it=None,
                      dlogz=None,
                      stop_val=None,
                      nbatch=None,
                      logl_min=-np.inf,
                      logl_max=np.inf):
    niter, short_str, mid_str, long_str = get_print_fn_args(
        results,
        niter,
        ncall,
        add_live_it=add_live_it,
        dlogz=dlogz,
        stop_val=stop_val,
        nbatch=nbatch,
        logl_min=logl_min,
        logl_max=logl_max)

    long_str = ["iter: {:d}".format(niter)] + long_str

    # Printing.
    long_str = ' | '.join(long_str)
    mid_str = ' | '.join(mid_str)
    short_str = '|'.join(short_str)
    if sys.stderr.isatty() and hasattr(shutil, 'get_terminal_size'):
        columns = shutil.get_terminal_size(fallback=(80, 25))[0]
    else:
        columns = 200
    if columns > len(long_str):
        sys.stderr.write("\r" + long_str + ' ' * (columns - len(long_str) - 2))
    elif columns > len(mid_str):
        sys.stderr.write("\r" + mid_str + ' ' * (columns - len(mid_str) - 2))
    else:
        sys.stderr.write("\r" + short_str + ' ' *
                         (columns - len(short_str) - 2))
    sys.stderr.flush()


class Results:
    """Contains the full output of a run along with a set of helper
    functions for summarizing the output."""
    def __init__(self, key_values):
        self._keys = []
        self._initialized = False
        for k, v in key_values:
            self._keys.append(k)
            setattr(self, k, v)
        required_keys = [
            'samples_u', 'samples_id', 'logl', 'logwt', 'logz', 'logzerr',
            'samples'
        ]
        for k in required_keys:
            if k not in self._keys:
                raise ValueError('Key %s must be provided' % k)
        if 'nlive' in self._keys:
            self._dynamic = False
        elif 'samples_n' in self._keys:
            self._dynamic = True
        else:
            raise ValueError(
                'Trying to construct results object without nlive '
                'or batch_nlive information')
        self._initialized = True

    def __setattr__(self, name, value):
        if name[0] != '_' and self._initialized:
            raise RuntimeError("Cannot set attributes directly")
        super().__setattr__(name, value)

    def __getitem__(self, name):
        if name in self._keys:
            return getattr(self, name)
        else:
            raise KeyError(name)

    def __repr__(self):
        m = max(list(map(len, list(self._keys)))) + 1
        return '\n'.join(
            [k.rjust(m) + ': ' + repr(getattr(self, k)) for k in self._keys])

    def items(self):
        return ((k, getattr(self, k)) for k in self._keys)

    def isdynamic(self):
        return self._dynamic

    def summary(self):
        """Return a formatted string giving a quick summary
        of the results."""

        if self._dynamic:
            res = ("niter: {:d}\n"
                   "ncall: {:d}\n"
                   "eff(%): {:6.3f}\n"
                   "logz: {:6.3f} +/- {:6.3f}".format(self.niter,
                                                      sum(self.ncall),
                                                      self.eff, self.logz[-1],
                                                      self.logzerr[-1]))
        else:
            res = ("nlive: {:d}\n"
                   "niter: {:d}\n"
                   "ncall: {:d}\n"
                   "eff(%): {:6.3f}\n"
                   "logz: {:6.3f} +/- {:6.3f}".format(self.nlive, self.niter,
                                                      sum(self.ncall),
                                                      self.eff, self.logz[-1],
                                                      self.logzerr[-1]))

        print('Summary\n=======\n' + res)


def results_substitute(results, kw_dict):
    new_list = []
    for k, w in results.items():
        if k not in kw_dict:
            new_list.append((k, w))
        else:
            new_list.append((k, kw_dict[k]))
    return Results(new_list)
