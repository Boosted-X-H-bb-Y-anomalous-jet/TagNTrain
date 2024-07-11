datasets_n_jobs = {
    "2016APV":{
        "JetHT_Run2016B_ver2_HIPM":60,
        "JetHT_Run2016C_HIPM":60,
        "JetHT_Run2016D_HIPM":60,
        "JetHT_Run2016E_HIPM":60,
        "JetHT_Run2016F":60,
        "TTToHadronic":1,
        "TTToSemiLeptonic":1,
        "QCD_HT700to1000":1,
        "QCD_HT1000to1500":1,
        "QCD_HT1500to2000":1,
        "QCD_HT2000toInf":1
    },
    "2016":{
        "JetHT_Run2016F_HIPM":60,
        "JetHT_Run2016G":60,
        "JetHT_Run2016G1":60,
        "JetHT_Run2016H":7,#Only has a few files
        "TTToHadronic":1,
        "TTToSemiLeptonic":1,
        "QCD_HT700to1000":1,
        "QCD_HT1000to1500":1,
        "QCD_HT1500to2000":1,
        "QCD_HT2000toInf":1
    },
    "2017":{
        "JetHT_Run2017B":60,
        "JetHT_Run2017C":60,
        "JetHT_Run2017D":60,
        "JetHT_Run2017E":60,
        "JetHT_Run2017F":60,
        "JetHT_Run2017F1":10,
        "TTToHadronic":1,
        "TTToSemiLeptonic":1,
        "QCD_HT700to1000":1,
        "QCD_HT1000to1500":1,
        "QCD_HT1500to2000":1,
        "QCD_HT2000toInf":1
        },
    "2018":{
        "JetHT_Run2018A":60,
        "JetHT_Run2018B":60,
        "JetHT_Run2018C":60,
        "JetHT_Run2018D":60,
        "TTToHadronic":1,
        "TTToSemiLeptonic":1,
        "QCD_HT700to1000":1,
        "QCD_HT1000to1500":1,
        "QCD_HT1500to2000":1,
        "QCD_HT2000toInf":1
        }
    }


signals = ["MX1200_MY90","MX1400_MY90","MX1600_MY90","MX1800_MY90","MX2000_MY90","MX2200_MY90","MX2400_MY90","MX2500_MY90","MX2600_MY90","MX2800_MY90","MX3000_MY90","MX3500_MY90","MX4000_MY90"]
for year,datasets_year in datasets_n_jobs.items():
    for signal in signals:
        datasets_year[signal] = 1
