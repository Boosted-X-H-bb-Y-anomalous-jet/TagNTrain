import ROOT as r
import os
import numpy as np
import math


base_path='/uscms_data/d3/roguljic/el8_anomalous/el9_fitting/templates_v3/templates_'

def significance(signal_yield,background_yield,a):
    S=signal_yield
    B=background_yield
    print(S, B)
    return S / ((a/2) + np.sqrt(B))

def getYield(process,year,lowX,highX,lowY,highY,vae_cut):
    filepath=base_path+process+'_'+year+'.root'
    if not os.path.exists(filepath):
        print('File does not exist: ',filepath)
        return
    file=r.TFile.Open(filepath)

    keyname='mjj_my_vaeloss_'+process+'_'+year+'_IR_Pass_nom'

    h=file.Get(keyname)

    Yield=h.Integral(lowX,highX,lowY,highY,vae_cut,-1)

    return Yield

def OptimizeCuts(process,vae_cut,lowX,highX,lowY,highY,years):
    a=3

    SignalYield=0
    for year in years:
        SignalYield+=getYield(process,year,lowX,highX,lowY,highY,vae_cut)
    BackgroundYield=getYield('data_obs','run2',lowX,highX,lowY,highY,vae_cut)
    sig=significance(SignalYield,BackgroundYield,a)
    return sig

    

if __name__=='__main__':
    processes=['MX2400_MY90']
    years=['2016','2016APV','2017','2018']

    lowX,highX,lowY,highY=16,27,5,16 #For MX2000_MY90
    lowX,highX,lowY,highY=1,-1,1,-1 #Inclusive

    for process in processes:
        optimal_vae_cut=-1
        sig_optimal=-1
        for vae_cut in range(100): # 100 vae bins
            P_Sig=OptimizeCuts(process,vae_cut,lowX,highX,lowY,highY,years)
            print('vae bin index: ',vae_cut,', significance: ',P_Sig)
            if P_Sig>sig_optimal:
                optimal_vae_cut=vae_cut
                sig_optimal=P_Sig

        filepath=base_path+process+'_2016.root'
        file=r.TFile.Open(filepath)
        keyname='mjj_my_vaeloss_'+process+'_2016_IR_Pass_nom'
        h=file.Get(keyname)
        opt_vae_cut_val=h.GetZaxis().GetBinLowEdge(optimal_vae_cut)

        print("For ",process," optimal vae cut at vae =",opt_vae_cut_val,'with a significance of ',sig_optimal)