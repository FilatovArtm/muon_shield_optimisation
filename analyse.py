#!/usr/bin/env python2
import argparse
import numpy as np
import ROOT as r
import shipunit as u
import rootUtils as ut
from common import get_geo, FCN


def analyse(tree, outputfile):
    """Analyse tree to find hit positions and create histograms.

    Parameters
    ----------
    tree
        Tree or Chain of trees with the usual `cbmsim` format
    outputfile : str
        Filename for the file in which the histograms are saved,
        will be overwritten

    Returns
    -------
    std::vector<double>
        Vector of hit x-positions [cm]

    """
    h = {}
    ut.bookHist(h, 'mu_pos', '#mu- hits;x[cm];y[cm]', 100, -1000, +1000, 100,
                -800, 1000)
    ut.bookHist(h, 'anti-mu_pos', '#mu+ hits;x[cm];y[cm]', 100, -1000, +1000,
                100, -800, 1000)
    ut.bookHist(h, 'mu_w_pos', '#mu- hits;x[cm];y[cm]', 100, -1000, +1000, 100,
                -800, 1000)
    ut.bookHist(h, 'anti-mu_w_pos', '#mu+ hits;x[cm];y[cm]', 100, -1000, +1000,
                100, -800, 1000)
    ut.bookHist(h, 'mu_p', '#mu+-;p[GeV];', 100, 0, 350)
    ut.bookHist(h, 'mu_p_original', '#mu+-;p[GeV];', 100, 0, 350)
    ut.bookHist(h, 'mu_pt_original', '#mu+-;p_t[GeV];', 100, 0, 6)
    ut.bookHist(h, 'mu_ppt_original', '#mu+-;p[GeV];p_t[GeV];', 100, 0, 350,
                100, 0, 6)
    ut.bookHist(h, 'smear', '#mu+- initial vertex;x[cm];y[cm]', 100, -100,
                +100, 100, -100, 100)
    xs = r.std.vector('double')()
    i, n = 0, tree.GetEntries()
    print '0/{}\r'.format(n),
    mom = r.TVector3()
    for event in tree:
        i += 1
        if i % 1000 == 0:
            print '{}/{}\r'.format(i, n),
        original_muon = event.MCTrack[1]
        h['smear'].Fill(original_muon.GetStartX(), original_muon.GetStartY())
        for hit in event.vetoPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                pid = hit.PdgCode()
                if hit.GetZ() > 2597 and hit.GetZ() < 2599 and abs(pid) == 13:
                    hit.Momentum(mom)
                    P = mom.Mag() / u.GeV
                    y = hit.GetY()
                    x = hit.GetX()
                    if pid == 13:
                        h['mu_pos'].Fill(x, y)
                    else:
                        h['anti-mu_pos'].Fill(x, y)
                    x *= pid / 13.
                    if (P > 1 and abs(y) < 5 * u.m and
                            (x < 2.6 * u.m and x > -3 * u.m)):
                        xs.push_back(x)
                        w = np.sqrt((560. - (x + 300.)) / 560.)
                        h['mu_p'].Fill(P)
                        original_muon = event.MCTrack[1]
                        h['mu_p_original'].Fill(original_muon.GetP())
                        h['mu_pt_original'].Fill(original_muon.GetPt())
                        h['mu_ppt_original'].Fill(original_muon.GetP(),
                                                  original_muon.GetPt())
                        if pid == 13:
                            h['mu_w_pos'].Fill(x, y, w)
                        else:
                            h['anti-mu_w_pos'].Fill(-x, y, w)
    ut.writeHists(h, outputfile)
    return xs


def main():
    f = r.TFile.Open(args.input, 'read')
    tree = f.cbmsim
    xs = analyse(tree, args.output)
    L, W = get_geo(args.geofile)
    fcn = FCN(W, np.array(xs), L)
    print fcn, len(xs)


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    r.gSystem.Load('libpythia8')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--input', required=True)
    parser.add_argument('-g', '--geofile', required=True)
    parser.add_argument('-o', '--output', default='test.root')
    args = parser.parse_args()
    main()
