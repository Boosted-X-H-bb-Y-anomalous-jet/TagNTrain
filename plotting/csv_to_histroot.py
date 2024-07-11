import numpy as np
import ROOT as r
import csv


from datasets import datasets_n_jobs as datasets
datasets["run2"]={"data_obs":1}
datasets["2016"]["data_obs"]=1
datasets["2016APV"]["data_obs"]=1
datasets["2017"]["data_obs"]=1
datasets["2018"]["data_obs"]=1

def make_templates(csvreader, process, year, region, weights):
    histos = {}
    seen = set()# Set to store seen rows
    total_rows = 0
    skipped_rows = 0

    for weight in weights:
        name = f"{process}_{year}_{region}_{weight}"
        h2 = r.TH2F(f"mjj_my_{name}", "", 40, 1000, 3000, 100, 0, 1000)
        histos[weight] = h2

    for i, row in enumerate(csvreader):
        total_rows += 1
        # Create a key based on the first two entries of the row: evtnumber and mjj
        row_key = tuple(row[:2])
        if row_key in seen:
            skipped_rows += 1
            continue
        seen.add(row_key)

        mjj = float(row[1])
        my = float(row[3])
        
        for weight in weights:
            if process == "data_obs":
                w = 1.
            else:
                w = float(row[column_names[weight]])
            histos[weight].Fill(mjj, my, w)
    
    if total_rows > 0:
        fraction_skipped = skipped_rows / total_rows
    else:
        fraction_skipped = 0.0

    if(region=="CR_Pass" and (len(weights)>1 or process=="data_obs")):#Reduce the output
        print(f"Skipped over {skipped_rows} events, fraction: {fraction_skipped:.3f}")

    return histos



def vae_hist(csvreader,process,year,region):
    name = f"{process}_{year}_{region}"
    h = r.TH2F(f"vae_loss_{name}","",100,0,0.0001)
    for i,row in enumerate(csvreader):
        vae_loss = float(row[4])
        if process=="data_obs":
            w = 1.
        else:
            w = float(row[5])#nominal weight
            h.Fill(vae_loss,w)
    return h

def convert_region_nom(process,year,region):
    data_flag = False
    mc_no_sys = False
    if process=="data_obs" or "JetHT" in process:
        data_flag   = True
    if "qcd" in process.lower() or "semileptonic" in process.lower():
        mc_no_sys = True

    if data_flag:
        csvfile    = open(f"merged_output/{process}_{year}_{region}.csv")
    else:
        csvfile    = open(f"merged_output/{process}_{year}_{region}_nom.csv")
    csvreader  = csv.reader(csvfile,delimiter=",")
    variations = ["nom"]
    for variation in ["pdf","prefire","pileup","PS_ISR","PS_FSR","F","R","RF","top_ptrw","pnet"]:
        if data_flag:
            break
        if mc_no_sys:
            break
        variations.append(f"{variation}_up")
        variations.append(f"{variation}_down")
    histos  = make_templates(csvreader,process,year,region,variations)
    return histos


def convert_region_jecs(process,year,region,jec):
    csvfile    = open(f"merged_output/{process}_{year}_{region}_{jec}.csv")
    csvreader  = csv.reader(csvfile,delimiter=",")
    histos     = make_templates(csvreader,process,year,region,[jec])
    return histos

column_names = {
    'mjj': 1,
    'mh': 2,
    'my': 3,
    'vae_loss': 4,
    'nom': 5,
    'pdf_up': 6,
    'pdf_down': 7,
    'prefire_up': 8,
    'prefire_down': 9,
    'pileup_up': 10,
    'pileup_down': 11,
    'btag_up': 12,
    'btag_down': 13,
    'PS_ISR_up': 14,
    'PS_ISR_down': 15,
    'PS_FSR_up': 16,
    'PS_FSR_down': 17,
    'F_up': 18,
    'F_down': 19,
    'R_up': 20,
    'R_down': 21,
    'RF_up': 22,
    'RF_down': 23,
    'top_ptrw_up': 24,
    'top_ptrw_down': 25,
    'pnet_up': 26,
    'pnet_down': 27,
    'jes_up': 5,
    'jes_down': 5,
    'jer_up': 5,
    'jer_down': 5,
    'jms_up': 5,
    'jms_down': 5,
    'jmr_up': 5,
    'jmr_down': 5
}

jecs = ["jes_up","jes_down","jer_up","jer_down","jms_up","jms_down","jmr_up","jmr_down"]

for year,_ in datasets.items():
#for year in ["2017"]:
    print(year)
    for process,_ in datasets[year].items():
        histos = []
        if "JetHT" in process:#We will jointly process data under "data_obs" name
            continue
        print(process)
        for region in ["SR_Pass","SR_Fail","CR_Pass","CR_Fail"]:
            histos.extend(convert_region_nom(process,year,region).values())
            if not ("TTToHadronic" in process or "MX" in process):#Only run systematics on these two
                continue
            for jec in jecs:
                histos.extend(convert_region_jecs(process,year,region,jec).values())
        
        f = r.TFile.Open(f"templates_{process}_{year}.root","RECREATE")
        f.cd()
        for histo in histos:
            histo.Write()
        f.Close()