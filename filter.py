#!/usr/bin/env python2
import argparse
from array import array
import numpy as np
import rootpy.ROOT as r
from rootpy.plotting import Hist2D
from rootpy.tree import Ntuple


maxpt = 6.5
maxp = 360.


def cap_bins(intuple, binmax=100):
    outtuple = intuple.CloneTree(0)
    h_all = Hist2D(100, 0, maxp, 100, 0, maxpt, name='all')
    h = Hist2D(100, 0, maxp, 100, 0, maxpt, name='cap')
    for muon in intuple:
        px = muon.opx
        py = muon.opy
        pz = muon.opz
        p = np.sqrt(px**2 + py**2 + pz**2)
        pt = np.sqrt(px**2 + py**2)
        assert p < maxp
        assert pt < maxpt
        b = int(p / maxp * 100) + 1, int(pt / maxpt * 100) + 1
        h_all.Fill(p, pt)
        if h[b].value < binmax:
            h.Fill(p, pt)
            a = array('f', [y for x in muon.values() for y in x])
            outtuple.Fill(a)
    return outtuple, h, h_all


def fill_up_bins(intuple, h, binmin=10):
    h_added_random = Hist2D(100, 0, maxp, 100, 0, maxpt, name='added_random')
    h_added_mirror = Hist2D(100, 0, maxp, 100, 0, maxpt, name='added_mirror')
    for muon in intuple:
        px = muon.opx
        py = muon.opy
        pz = muon.opz
        p = np.sqrt(px**2 + py**2 + pz**2)
        pt = np.sqrt(px**2 + py**2)
        b = int(p / maxp * 100) + 1, int(pt / maxpt * 100) + 1
        a = array('f', [y for x in muon.values() for y in x])
        if h[b].value < binmin:
            n = int(binmin / h[b].value)
            for _ in range(n):
                phi = r.gRandom.Uniform(0., 2.) * r.TMath.Pi()
                px = pt * r.TMath.Cos(phi)
                py = pt * r.TMath.Sin(phi)
                a[1] = px
                a[2] = py
                a[7] = px
                a[8] = py
                h_added_random.Fill(p, pt)
                intuple.Fill(a)
        a[1] = +pt
        a[2] = 0
        a[7] = +pt
        a[8] = 0
        intuple.Fill(a)
        h_added_mirror.Fill(p, pt)
        a[1] = -pt
        a[2] = 0
        a[7] = +pt
        a[8] = 0
        intuple.Fill(a)
        h_added_mirror.Fill(p, pt)
    return intuple, h_added_random, h_added_mirror


def add_problematic(intuple, n=2000):
    # TODO why aren't these saved?
    h_added_problematic = Hist2D(
        100, 0, maxp, 100, 0, maxpt, name='added_problematic')
    pt = 2.5
    for _ in range(n):
        p = r.gRandom.Uniform(150., maxp)
        pz = np.sqrt(p**2 - pt**2)
        phi = r.gRandom.Uniform(0., 2.) * r.TMath.Pi()
        px = pt * r.TMath.Cos(phi)
        py = pt * r.TMath.Sin(phi)
        intuple.Fill(
            array('f', [
                13., px, py, pz, 0, 0, -49.79, px, py, pz, 0, 0, -49.79, 0, 0,
                1, 0
            ]))
        intuple.Fill(
            array('f', [
                13., +pt, 0, pz, 0, 0, -49.79, +pt, 0, pz, 0, 0, -49.79, 0, 0,
                1, 0
            ]))
        intuple.Fill(
            array('f', [
                13., -pt, 0, pz, 0, 0, -49.79, -pt, 0, pz, 0, 0, -49.79, 0, 0,
                1, 0
            ]))
        h_added_problematic.Fill(p, pt)
        h_added_problematic.Fill(p, pt)
        h_added_problematic.Fill(p, pt)
    return intuple, h_added_problematic


def add_seed(intuple):
    outtuple = Ntuple(
        ('id', 'px', 'py', 'pz', 'x', 'y', 'z', 'opx', 'opy', 'opz', 'ox',
         'oy', 'oz', 'pythiaid', 'parentid', 'w', 'ecut', 'seed'),
        name='pythia8-Geant4')
    for i, muon in enumerate(intuple):
        a = array('f', [y for x in muon.values() for y in x])
        a.append(float(i))
        outtuple.fill(a)
    return outtuple


def main():
    f = r.TFile.Open(args.input, 'read')
    intuple = f.Get('pythia8-Geant4')
    print intuple.GetEntries()
    out = r.TFile.Open(args.output, 'recreate')
    outtuple, h, h_all = cap_bins(intuple)
    h.Write()
    h_all.Write()
    outtuple.Write()
    print outtuple.GetEntries()
    del outtuple
    intuple = out.Get('pythia8-Geant4')
    intuple, h_added_random, h_added_mirror = fill_up_bins(intuple, h)
    intuple.Write()
    print intuple.GetEntries()
    del intuple
    intuple = out.Get('pythia8-Geant4')
    # intuple, h_added_problematic = add_problematic(intuple)
    intuple.Write()
    print intuple.GetEntries()
    h_final = Hist2D(100, 0, maxp, 100, 0, maxpt, name='final')
    for muon in intuple:
        px = muon.opx
        py = muon.opy
        pz = muon.opz
        p = np.sqrt(px**2 + py**2 + pz**2)
        pt = np.sqrt(px**2 + py**2)
        h_final.Fill(p, pt)
    del intuple
    # h_added_problematic.Write()
    h_added_random.Write()
    h_added_mirror.Write()
    h_final.Write()
    intuple = out.Get('pythia8-Geant4')
    intuple = add_seed(intuple)
    intuple.Write()


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        '--input',
        default='root://eoslhcb.cern.ch/'
        '/eos/ship/data/Mbias/'
        'pythia8_Geant4-withCharm_onlyMuons_4magTarget.root')
    parser.add_argument('-o', '--output', default='filtered.root')
    args = parser.parse_args()
    main()
