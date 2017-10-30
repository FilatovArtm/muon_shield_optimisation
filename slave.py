#!/usr/bin/env python2
import os
from time import sleep
import copy
import json
import argparse
import shutil
import subprocess
import filelock
import ROOT as r
import config
import shipunit as u
import geomGeant4
from ShipGeoConfig import ConfigRegistry
import shipDet_conf
from analyse import analyse
from disney_common import create_id, ParseParams
from common import generate_geo
from get_geo import get_geo


def generate(
        inputFile,
        paramFile,
        outFile,
        seed=1,
        nEvents=None
):
    """Generate muon background and transport it through the geometry.

    Parameters
    ----------
    inputFile : str
        File with muon ntuple
    paramFile : str
        File with the muon shield parameters
    outFile : str
        File in which `cbmsim` tree is saved
    seed : int
        Determines the seed passed on to the MuonBackGenerator instance
    nEvents : int
        Number of events to be read from inputFile

        If falsy, generate will run over the entire file.

    """
    firstEvent = 0
    dy = 10.
    vessel_design = 5
    shield_design = 8
    mcEngine = 'TGeant4'
    sameSeed = seed
    theSeed = 1

    phiRandom = False  # only relevant for muon background generator
    followMuon = True  # only transport muons for a fast muon only background

    print 'FairShip setup to produce', nEvents, 'events'
    r.gRandom.SetSeed(theSeed)
    ship_geo = ConfigRegistry.loadpy(
        '$FAIRSHIP/geometry/geometry_config.py',
        Yheight=dy,
        tankDesign=vessel_design,
        muShieldDesign=shield_design,
        muShieldGeo=paramFile)

    run = r.FairRunSim()
    run.SetName(mcEngine)  # Transport engine
    run.SetOutputFile(outFile)  # Output file
    # user configuration file default g4Config.C
    run.SetUserConfig('g4Config.C')
    modules = shipDet_conf.configure(run, ship_geo)
    primGen = r.FairPrimaryGenerator()
    primGen.SetTarget(ship_geo.target.z0 + 50 * u.m, 0.)
    MuonBackgen = r.MuonBackGenerator()
    MuonBackgen.Init(inputFile, firstEvent, phiRandom)
    MuonBackgen.SetSmearBeam(3 * u.cm)  # beam size mimicking spiral
    if sameSeed:
        MuonBackgen.SetSameSeed(sameSeed)
    primGen.AddGenerator(MuonBackgen)
    if not nEvents:
        nEvents = MuonBackgen.GetNevents()
    else:
        nEvents = min(nEvents, MuonBackgen.GetNevents())
    print 'Process ', nEvents, ' from input file, with Phi random=', phiRandom
    if followMuon:
        modules['Veto'].SetFastMuon()
    run.SetGenerator(primGen)
    run.SetStoreTraj(r.kFALSE)
    run.Init()
    print 'Initialised run.'
    geomGeant4.setMagnetField()
    print 'Start run of {} events.'.format(nEvents)
    run.Run(nEvents)
    print 'Finished simulation of {} events.'.format(nEvents)


def main():

    tmpl = copy.deepcopy(config.RESULTS_TEMPLATE)

    paramFile = '/shared/params_{}.root'.format(create_id(args.params))
    heavy = '/shared/heavy'
    lockfile = paramFile + '.lock'

    while not os.path.exists(paramFile) and not os.path.exists(heavy):
        lock = filelock.FileLock(lockfile)
        if not lock.is_locked:
            with lock:
                tmp_paramFile = generate_geo(
                    paramFile.replace('.', '.tmp.'),
                    ParseParams(args.params)
                )
                subprocess.call(
                    [
                        'python2',
                        'get_geo.py',
                        '-g', tmp_paramFile,
                        '-o', paramFile.replace('params', 'geoinfo')
                        ])
                shutil.move(
                    '/shield/geo/' + os.path.basename(tmp_paramFile),
                    paramFile.replace(
                        'shared', 'output'
                    ).replace(
                        'params', 'geo'
                    )
                )
                with open(paramFile.replace('params', 'geoinfo'), 'r') as f:
                    length, weight = f.read().strip().split(',')

                tmpl['weight'] = weight
                tmpl['length'] = length
                if weight >= 3e6:
                    open(heavy, 'a').close()
                    with open(args.results, 'w') as f:
                        json.dump(tmpl, f)
                else:
                    shutil.move(tmp_paramFile, paramFile)
        else:
            sleep(60)

    if os.path.exists(heavy):
        return

    outFile = "/output/ship.conical.MuonBack-TGeant4.root"
    try:
        try:
            generate(
                inputFile=args.input,
                paramFile=paramFile,
                outFile=outFile,
                seed=args.seed,
                nEvents=args.nEvents
            )
        except Exception, e:
            raise RuntimeError(
                "Simulation failed with exception: %s",
                e
            )
        try:
            chain = r.TChain('cbmsim')
            chain.Add(outFile)
            xs = analyse(chain, args.hists)
            tmpl['muons'] = len(xs)
            tmpl['muons_w'] = sum(xs)
        except Exception, e:
            raise RuntimeError(
                "Analysis failed with exception: %s",
                e
            )
    except RuntimeError, e:
        tmpl['error'] = e.__repr__()
    finally:
        with open(args.results, 'w') as f:
            json.dump(tmpl, f)
        os.remove(outFile)


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    r.gSystem.Load('libpythia8')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        '--input',
        default='root://eoslhcb.cern.ch/'
        '/eos/ship/data/Mbias/'
        'pythia8_Geant4-withCharm_onlyMuons_4magTarget.root')
    parser.add_argument('--results', default='results.json')
    parser.add_argument('--hists', default='hists.root')
    parser.add_argument('--params', required=True)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('-n', '--nEvents', type=int)
    args = parser.parse_args()
    main()
