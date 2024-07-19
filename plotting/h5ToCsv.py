import sys
import numpy as np
sys.path.append('..')
import h5py
from numpy import genfromtxt
import csv
import subprocess
from math import ceil
import os

eosls = 'eos root://cmseos.fnal.gov ls'
xrdfsls = "xrdfs root://cmseos.fnal.gov ls"

#Units are in pb (pb-1 for int lumi)
xsecs       = {"signal":0.005, 'TTToHadronic':377.96,'TTToSemiLeptonic':365.34,"QCD_HT700to1000":6440,"QCD_HT1000to1500":1127,"QCD_HT1500to2000":110,"QCD_HT2000toInf":21.98}
int_lumi    = {"2016":16800,"2016APV":19500,"2017":41500,"2018":59800}
pnet_tight  = {"2016APV":0.9883,"2016":0.9883,"2017":0.9870,"2018":0.9880}

def mjj_from_4vecs(j1, j2):
    #assume j1 and j2 in (pt,eta,phi,m) format
    px1 = j1[:,0] * np.cos(j1[:,2])  
    py1 = j1[:,0] * np.sin(j1[:,2])  
    pz1 = j1[:,0] * np.sinh(j1[:,1]) 
    px2 = j2[:,0] * np.cos(j2[:,2])  
    py2 = j2[:,0] * np.sin(j2[:,2])  
    pz2 = j2[:,0] * np.sinh(j2[:,1]) 
    E1 = np.sqrt(px1**2 + py1**2 + pz1**2 + j1[:,3]**2)
    E2 = np.sqrt(px2**2 + py2**2 + pz2**2 + j2[:,3]**2)
    mjj = np.sqrt((E1 + E2)**2 - (px1 + px2)**2 - (py1 + py2)**2 - (pz1 + pz2)**2)
    return mjj

#JME_vars array = [pt_JES_up, m_JES_up, pt_JES_down, m_JES_down, pt_JER_up, m_JER_up, pt_JER_down, m_JER_down, m_JMS_up, m_JMS_down, m_JMR_up, m_JMR_down]
#jec_code 0-8: nom,jes_up,jes_down,jer_up,jer_down,jms_up,jms_down,jmr_up,jmr_down
def get_jet_4_vecs(jet_kinematics,jet1_JME_vars,jet2_JME_vars,jec_code):
        j1 = jet_kinematics[:,2:6]#These are nominal values
        j2 = jet_kinematics[:,6:10]     
        #nominal
        if jec_code == 0:
            mjj = mjj_from_4vecs(j1, j2)
            return j1,j2,mjj
        #JES up
        elif jec_code == 1:
            pt_sys1 = jet1_JME_vars[:,0].reshape(-1)
            pt_sys2 = jet2_JME_vars[:,0].reshape(-1)
            mj1_corr = jet1_JME_vars[:,1].reshape(-1)
            mj2_corr = jet2_JME_vars[:,1].reshape(-1)
            j1[:, 0] = pt_sys1
            j2[:, 0] = pt_sys2
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JES down
        elif jec_code == 2:
            pt_sys1 = jet1_JME_vars[:,2].reshape(-1)
            pt_sys2 = jet2_JME_vars[:,2].reshape(-1)
            mj1_corr = jet1_JME_vars[:,3].reshape(-1)
            mj2_corr = jet2_JME_vars[:,3].reshape(-1)
            j1[:, 0] = pt_sys1
            j2[:, 0] = pt_sys2
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr

        #JER up
        elif jec_code == 3:
            pt_sys1 = jet1_JME_vars[:,4].reshape(-1)
            pt_sys2 = jet2_JME_vars[:,4].reshape(-1)
            mj1_corr = jet1_JME_vars[:,5].reshape(-1)
            mj2_corr = jet2_JME_vars[:,5].reshape(-1)
            j1[:, 0] = pt_sys1
            j2[:, 0] = pt_sys2
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JER down
        elif jec_code == 4:
            pt_sys1 = jet1_JME_vars[:,6].reshape(-1)
            pt_sys2 = jet2_JME_vars[:,6].reshape(-1)
            mj1_corr = jet1_JME_vars[:,7].reshape(-1)
            mj2_corr = jet2_JME_vars[:,7].reshape(-1)
            j1[:, 0] = pt_sys1
            j2[:, 0] = pt_sys2
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JMS up
        elif jec_code == 5:
            mj1_corr = jet1_JME_vars[:,8].reshape(-1)
            mj2_corr = jet2_JME_vars[:,8].reshape(-1)     
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JMS down
        elif jec_code == 6:
            mj1_corr = jet1_JME_vars[:,9].reshape(-1)
            mj2_corr = jet2_JME_vars[:,9].reshape(-1)      
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JMR up
        elif jec_code == 7:
            mj1_corr = jet1_JME_vars[:,10].reshape(-1)
            mj2_corr = jet2_JME_vars[:,10].reshape(-1)     
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        #JMR down
        elif jec_code == 8:
            mj1_corr = jet1_JME_vars[:,11].reshape(-1)
            mj2_corr = jet2_JME_vars[:,11].reshape(-1)    
            j1[:, 3] = mj1_corr
            j2[:, 3] = mj2_corr
        else:
            print("ERROR: Invalid jec code", jec_code)
            exit()

        mjj = mjj_from_4vecs(j1, j2)
        return j1,j2,mjj

def run_single_process(process,year,job_id,n_jobs,jec_code):

    if "JetHT" in process and (year=="2017" or year=="2016"):
        h5_dir  = f"/store/user/shanning/H5_output/{year}/{process}/"
    #elif ("QCD" in process) or ("SemiLeptonic" in process):
    #    h5_dir  = f"/store/user/shanning/H5_output/{year}/{process}/"
    else:
        h5_dir  = f"/store/user/roguljic/H5_output/{year}/{process}/"
    if not "jetht" in process.lower():
        xrdcp_cmd = f"xrdcp root://cmseos.fnal.gov/{h5_dir}/merged.h5 merged.h5"
        fin =  "merged.h5"
        subprocess.call(xrdcp_cmd,shell=True)
        process_file(fin,process,year,"SR",jec_code=jec_code)
        process_file(fin,process,year,"CR",jec_code=jec_code)
        process_file(fin,process,year,"IR",jec_code=jec_code)#Inclusive region in VAE, i.e., no VAE cut
        subprocess.call("rm merged.h5",shell=True)
    else:
        fNames          = subprocess.check_output(['{} {}'.format(xrdfsls,h5_dir)],shell=True,text=True).split('\n')
        fNames.sort()#Sort files to have the same order across all condor jobs
        fNames_chunks   = [fNames[i::n_jobs] for i in range(n_jobs)]
        to_process      = fNames_chunks[job_id]
        n_tot_files     = len(fNames)
        n_files         = len(to_process)
        for i,fName in enumerate(to_process):
            print(f"{i}/{n_files} (out of {n_tot_files} total)")
            if not "nano" in fName:
                continue
            short_name = fName.split("/")[-1]
            xrdcp_cmd = f"xrdcp root://cmseos.fnal.gov/{h5_dir}/{short_name} {short_name}"
            print(xrdcp_cmd)
            subprocess.call(xrdcp_cmd,shell=True)
            process_file(short_name,process,year,"SR",job_id,n_jobs,jec_code=0)#No JEC variations to be applied to data
            process_file(short_name,process,year,"CR",job_id,n_jobs,jec_code=0)
            process_file(short_name,process,year,"IR",job_id,n_jobs,jec_code=0)
            subprocess.call(f"rm {short_name}",shell=True) 

def process_file(fin,process,year,region,job_id=0,n_jobs=1,jec_code=0):
    f = h5py.File(fin, "r")
    
    if "jetht" in process.lower():
        weights = []
        data_flag = True
        mc_no_sys = False
    elif "semileptonic" in process.lower() or "qcd" in process.lower():
        data_flag = False
        mc_no_sys = True
    else:
        data_flag = False
        mc_no_sys = False


    n_presel     = len(f['event_info']) #event_info[i]: [eventNum, MET, MET_phi, genWeight, leptonic_decay, run, self.year, num_jets]
    presel_eff   = f['preselection_eff'][0]
    n_gen        = n_presel/presel_eff
    #Weights are rescaled so that the nominal average weight is 1.0
    #To compensate for that, resel efficiency is also scaled by average nominal weight, which is why number of generated events is not an int.
    #print(f"Number of preselected events: {n_presel}")
    #print(f"Preselection efficiency {presel_eff:.4f}")
    #print(f"Number of generated events: {n_gen}")

    batch_size = 50000 #Gets rid of "exceedes 10% of memory" earning
    n_batches  = ceil(float(n_presel)/batch_size)
    for n_batch in range(n_batches):
        print(f"Batch {n_batch}/{n_batches}")
        start_evt = n_batch*batch_size
        stop_evt  = start_evt+batch_size
        if(stop_evt>n_presel):
            stop_evt=-1

        hbb_signal_1 = f['jet1_extraInfo'][start_evt:stop_evt,-2]
        hbb_signal_2 = f['jet2_extraInfo'][start_evt:stop_evt,-2]
        evt_num = f['event_info'][start_evt:stop_evt,0]
        delta_eta = f['jet_kinematics'][start_evt:stop_evt,1]#Saved as |eta1-eta2|

        if data_flag or mc_no_sys:
            j1,j2,mjj  = get_jet_4_vecs(f['jet_kinematics'][start_evt:stop_evt],False,False,jec_code)#Data has no jet1/2_JME_vars
        else:
            j1,j2,mjj  = get_jet_4_vecs(f['jet_kinematics'][start_evt:stop_evt],f['jet1_JME_vars'][start_evt:stop_evt],f['jet2_JME_vars'][start_evt:stop_evt],jec_code)

        #mj1_higgscut = np.array(f['jet_kinematics'][start_evt:stop_evt,5]).reshape(-1)
        #mj2_higgscut = np.array(f['jet_kinematics'][start_evt:stop_evt,-5]).reshape(-1)
        mj1_higgscut = np.array(j1[:,3]).reshape(-1)
        mj2_higgscut = np.array(j2[:,3]).reshape(-1)
        ptj1_cut = np.array(j1[:,0]).reshape(-1)
        ptj2_cut = np.array(j2[:,0]).reshape(-1)
        vae_loss      = f["Y_vae_loss"][start_evt:stop_evt]

        #Now to Decide if the higgs in the kept events are passing or failing the Higgs cut, and keep events we care about
        #The next two lines can actually be read from the input .h5 file
        is_j1_moreHiggs = hbb_signal_1>hbb_signal_2
        is_j2_moreHiggs = hbb_signal_1<hbb_signal_2
        does_j1_pass_hbb = hbb_signal_1 > pnet_tight[year]
        does_j2_pass_hbb = hbb_signal_2 > pnet_tight[year]


        does_j1_fail_hbb = hbb_signal_1 < pnet_tight[year]
        does_j2_fail_hbb = hbb_signal_2 < pnet_tight[year]

        if region=="SR":
            vaecuts = (vae_loss>0.00005)
        elif region=="CR":
            vaecuts = np.logical_and((vae_loss>0.000025),(vae_loss<0.00004))
        else:
            vaecuts = np.ones(np.shape(vae_loss))
        ####
        keepevent = vaecuts #Keep event if Y-cand passes VAE cut for that region
        ###
        higgs1cut = np.logical_and(mj1_higgscut>100, mj1_higgscut<150)
        higgs2cut = np.logical_and(mj2_higgscut>100, mj2_higgscut<150)
        keephiggs1 = np.logical_and(is_j1_moreHiggs,    higgs1cut)
        keephiggs2 = np.logical_and(is_j2_moreHiggs,    higgs2cut)
        keephiggs = np.logical_or(keephiggs1,keephiggs2)
        keepevent = np.logical_and(keepevent, keephiggs)

        ###pt cut (only really needed in case of jec changing pt)
        ptcut   = np.logical_and(ptj1_cut>300, ptj2_cut>300)
        delta_eta_cut = delta_eta<1.3
        keepevent = np.logical_and(keepevent,ptcut)
        keepevent = np.logical_and(keepevent,delta_eta_cut)

        ###
        is_j1_higgs = np.logical_and(is_j1_moreHiggs, does_j1_pass_hbb)
        is_j2_higgs = np.logical_and(is_j2_moreHiggs, does_j2_pass_hbb)

        is_j1_fail = np.logical_and(is_j1_moreHiggs, does_j1_fail_hbb)
        is_j2_fail = np.logical_and(is_j2_moreHiggs, does_j2_fail_hbb)

        pass_boolean = np.logical_and(keepevent,np.logical_or(is_j1_higgs, is_j2_higgs))
        fail_boolean = np.logical_and(keepevent,np.logical_or(is_j1_fail, is_j2_fail))

        # tot_mjj = np.array(h5py.File(fin, "r")['jet_kinematics'][start_evt:stop_evt,0]).reshape(-1)
        # tot_mj1 = np.array(h5py.File(fin, "r")['jet_kinematics'][start_evt:stop_evt,5]).reshape(-1)
        # tot_mj2 = np.array(h5py.File(fin, "r")['jet_kinematics'][start_evt:stop_evt,-5]).reshape(-1)

        tot_mjj = np.array(mjj[:]).reshape(-1)
        tot_mj1 = np.array(j1[:,3]).reshape(-1)
        tot_mj2 = np.array(j2[:,3]).reshape(-1)


        if not data_flag:
            if("MX" in process):
                lumi_scaling = xsecs["signal"]*int_lumi[year]/n_gen
                weights = f['sys_weights'][start_evt:stop_evt]
            else:
                lumi_scaling = xsecs[process]*int_lumi[year]/n_gen
                if mc_no_sys:
                    weights=[]
                    for i in range(len(tot_mjj)):
                        weights.append(np.ones(1))
                    weights=np.array(weights)
                else:
                    weights = f['sys_weights'][start_evt:stop_evt]
            print(f"Lumi scale for {process} {year}: {lumi_scaling:.4f}")
            for i in range(len(weights)):
                weights[i][0] *= lumi_scaling
            


        tot_mh = (np.where(is_j2_moreHiggs == True, tot_mj2, tot_mj1))
        tot_my = (np.where(is_j2_moreHiggs == True, tot_mj1, tot_mj2)) 

        tagging_dict = {"Pass":pass_boolean,"Fail":fail_boolean}
        for tag_region in tagging_dict:
            file_name  = f"output/{process}_{year}_{region}_{tag_region}.csv"
            if data_flag:
                file_name = file_name.replace(".csv","_{0}_{1}.csv".format(job_id,n_jobs))
            else:
                file_name = jec_tag(file_name,jec_code)
            store_csv(tot_mjj,tot_mh,tot_my,vae_loss,evt_num,weights,tagging_dict[tag_region],file_name,data_flag)

def jec_tag(file_name,jec_code):
    jec_map = {0:"nom",1:"jes_up",2:"jes_down",3:"jer_up",4:"jer_down",5:"jms_up",6:"jms_down",7:"jmr_up",8:"jmr_down"}
    jec     = jec_map[jec_code]
    file_name = file_name.replace(".csv",f"_{jec}.csv")
    return file_name


def store_csv(mjj,mh,my,vae_loss,evt_num,weights,mask,file_name,data_flag):
    region_mjj = mjj[mask]
    region_mh  = mh[mask]
    region_my  = my[mask]
    region_vae_loss  = vae_loss[mask]
    region_evt_num = evt_num[mask]
    if not data_flag:
        weights    = weights[mask]

    evts_in_region = len(region_mjj)
    assert evts_in_region==len(region_mh)
    assert evts_in_region==len(region_my)

    print(f"Writing {evts_in_region} events to {file_name}")

    with open(file_name, "a+", newline='') as f:
        writer = csv.writer(f)
        for i in range(len(region_mjj)):
            content = [region_evt_num[i],region_mjj[i], region_mh[i], region_my[i], region_vae_loss[i]]
            if not data_flag:
                content.extend(weights[i])
            writer.writerow(content)

#python3 h5ToCsv.py TTToHadronic 2018 0 1 0
process = sys.argv[1]
year    = sys.argv[2]
job_id  = int(sys.argv[3])
n_jobs  = int(sys.argv[4])
jec_code= int(sys.argv[5])
run_single_process(process,year,job_id,n_jobs,jec_code)