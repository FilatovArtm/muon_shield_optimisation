#!/usr/bin/env python2
import argparse
from array import array
import numpy as np
import rootpy.ROOT as r
from rootpy.plotting import Canvas, Hist2D


def main():
    f = r.TFile.Open(args.input, 'read')
    intuple = f.Get('pythia8-Geant4')
    out = r.TFile.Open(args.output, 'recreate')
    outtuple = intuple.CloneTree(0)
    h = Hist2D(100, 0, 350, 100, 0, 6)
    i = 1
    for muon in intuple:
        px = muon.px
        py = muon.py
        pz = muon.pz
        p = np.sqrt(px**2 + py**2 + pz**2)
        pt = np.sqrt(px**2 + py**2)
        b = int(p / 350. * 100)+1, int(pt / 6. * 100)+1
        before = h[b].value
        if before < 100:
            h.Fill(p, pt)
            a = array('f', [y for x in muon.values() for y in x])
            outtuple.Fill(a)
        i += 1
        if i == 100000:
            break
    outtuple.Write()
    del outtuple
    intuple = out.Get('pythia8-Geant4')
    for muon in intuple:
        px = muon.px
        py = muon.py
        pz = muon.pz
        p = np.sqrt(px**2 + py**2 + pz**2)
        pt = np.sqrt(px**2 + py**2)
        a = array('f', [y for x in muon.values() for y in x])
        a[1] = + pt
        a[2] = 0
        intuple.Fill(a)
        a[1] = - pt
        a[2] = 0
        intuple.Fill(a)
    intuple.Write()
    intuple.create_branches({'seed': 'F'})
    for muon in intuple:
        # print muon.keys()
        a = array('f', [y for x in muon.values() for y in x])
        muon.seed = hash(sum(a))
        intuple.Fill()
    intuple.Write()
    c = Canvas()
    r.gStyle.SetOptStat(11111111)
    h.Draw("colz")
    c.Draw()
    c.SaveAs("p_dist.png")


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        '--input',
        default='root://eoslhcb.cern.ch/'
        '/eos/ship/data/Mbias/'
        'pythia8_Geant4-withCharm_onlyMuons_4magTarget.root')
    parser.add_argument('-o', '--output', default='test.root')
    args = parser.parse_args()
    main()
