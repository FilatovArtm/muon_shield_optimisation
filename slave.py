#!/usr/bin/env python2
import argparse
import tempfile
import ROOT as r
import shipunit as u
import geomGeant4
from ShipGeoConfig import ConfigRegistry
import shipDet_conf
from analyse import analyse


def generate(inputFile, geoFile, nEvents, outFile, lofi=False):
    """Generate muon background and transport it through the geometry.

    Parameters
    ----------
    inputFile : str
        File with muon ntuple
    geoFile : str
        File with the muon shield parameters (not with the geometry config!)
    nEvents : int
        Number of events to read from inputFile
    outFile : str
        File in which `cbmsim` tree is saved
    lofi : bool, optional
        Determine fidelity. If True all non-essential Geant4
        processes will be deactivated

    """
    firstEvent = 0
    dy = 10.
    vessel_design = 5
    shield_design = 8
    mcEngine = 'TGeant4'
    sameSeed = 1
    theSeed = 1

    # provisionally for making studies of various muon background sources
    inactivateMuonProcesses = lofi
    phiRandom = False  # only relevant for muon background generator
    followMuon = True  # only transport muons for a fast muon only background

    print 'FairShip setup to produce', nEvents, 'events'
    r.gRandom.SetSeed(theSeed)
    ship_geo = ConfigRegistry.loadpy(
        '$FAIRSHIP/geometry/geometry_config.py',
        Yheight=dy,
        tankDesign=vessel_design,
        muShieldDesign=shield_design,
        muShieldGeo=geoFile)

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
    nEvents = min(nEvents, MuonBackgen.GetNevents())
    print 'Process ', nEvents, ' from input file, with Phi random=', phiRandom
    if followMuon:
        modules['Veto'].SetFastMuon()
    run.SetGenerator(primGen)
    run.SetStoreTraj(r.kFALSE)
    run.Init()
    geomGeant4.setMagnetField()
    if inactivateMuonProcesses:
        mygMC = r.TGeant4.GetMC()
        mygMC.ProcessGeantCommand('/process/inactivate muPairProd')
        mygMC.ProcessGeantCommand('/process/inactivate muBrems')
        mygMC.ProcessGeantCommand('/process/inactivate muIoni')
        mygMC.ProcessGeantCommand('/process/inactivate msc')
        mygMC.ProcessGeantCommand('/process/inactivate Decay')
        mygMC.ProcessGeantCommand('/process/inactivate CoulombScat')
        mygMC.ProcessGeantCommand('/process/inactivate muonNuclear')
        mygMC.ProcessGeantCommand('/process/inactivate StepLimiter')
        mygMC.ProcessGeantCommand('/process/inactivate specialCutForMuon')
    run.Run(nEvents)
    print 'Macro finished succesfully.'


def main():
    id_ = args.jobid
    n = args.nEvents if args.nEvents else 100000
    # TODO read total number from muon file directly OR
    # TODO always pass from steering process?

    with tempfile.NamedTemporaryFile() as t:
        outFile = t.name
        generate(args.input, args.geofile, n, outFile, args.lofi)
        chain = r.TChain('cbmsim')
        chain.Add(outFile)
        xs = analyse(chain, args.results)
        res = r.TFile.Open(args.results, 'update')
        res.WriteObject(xs, 'results')
        res.Close()
    print 'Slave: Worker process {} done.'.format(id_)


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
    parser.add_argument('--results', default='test.root')
    parser.add_argument('--geofile', required=True)
    parser.add_argument('--jobid', type=int, required=True)
    parser.add_argument('-n', '--nEvents', type=int, default=None)
    parser.add_argument('--lofi', action='store_true')
    args = parser.parse_args()
    main()
