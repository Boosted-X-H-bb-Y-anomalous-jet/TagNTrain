import os
import subprocess

from datasets import datasets_n_jobs

def merge_csvs(dataset,year,n_jobs,jec_tag=False):
    regions     = ["SR","CR","IR"]
    categories  =  ["Pass","Fail"]
    for region in regions:
        for category in categories:
            if jec_tag:
                cat_cmd = f"cat output/{dataset}_{year}_{region}_{category}_*_{n_jobs}_{jec_tag}.csv > merged_output/{dataset}_{year}_{region}_{category}_{jec_tag}.csv"
            else:
                cat_cmd = f"cat output/{dataset}_{year}_{region}_{category}_*_{n_jobs}.csv > merged_output/{dataset}_{year}_{region}_{category}.csv"
            subprocess.call(cat_cmd,shell=True)

def check_other_regions(filename):
    #Assumes that we pass SR_Pass file!
    replacers = ["SR_Fail","CR_Pass","CR_Fail","IR_Pass","IR_Fail"]
    for replacer in replacers:
        file_to_check = filename.replace("SR_Pass",replacer)
        if not os.path.exists(file_to_check):
            #This should not really happen
            print(f"Missing {file_to_check}, exiting")
            exit()

def move_individual_files(dataset,year):
    regions = ["SR_Pass","SR_Fail","CR_Pass","CR_Fail","IR_Pass","IR_Fail"]
    for region in regions:
        mv_cmd = f"mv {dataset}_{year}_{region}_*csv single_output/. 2>/dev/null"
        #2>/dev/null supresses mv errors if files have already been moved
        try:
            subprocess.call(mv_cmd,shell=True)
        except:
            continue

def write_arguments(args_to_write):
    if args_to_write:
        f = open("h5ToCsv_args.txt","w")
        for line in args_to_write:
            f.write(line)
        f.close()

        print("Creating tarball")
        #subprocess.call("tar cf tarball.tgz h5ToCsv.py jrand_autoencoder_m2500.h5 ../utils",shell=True)
        subprocess.call("tar cf tarball.tgz h5ToCsv.py ../utils",shell=True)
        print("condor_submit jdl.txt")
    else:
        print("All processed")

def merge_data(year):
    dir_list = os.listdir("merged_output")
    if not any(("JetHT" in name) and (year in name) for name in dir_list):
        print(f"Did not find data for {year} in merged_output")
        return
    regions = ["SR_Pass","SR_Fail","CR_Pass","CR_Fail","IR_Pass","IR_Fail"]
    for region in regions:
        cat_cmd = f"cat merged_output/JetHT*{year}_{region}.csv > merged_output/data_obs_{year}_{region}.csv"
        subprocess.call(cat_cmd,shell=True)

def merge_run2_data():
    regions = ["SR_Pass","SR_Fail","CR_Pass","CR_Fail","IR_Pass","IR_Fail"]
    years = ["2016APV","2016","2017","2018"]

    for year in years:
        for region in regions:
            file_name = f"merged_output/data_obs_{year}_{region}.csv"
            if not os.path.exists(file_name):
                print(f"{file_name} does not exist, not merging Run 2")
                return

    for region in regions:
        cat_cmd = f"cat merged_output/data_obs_20*_{region}.csv > merged_output/data_obs_run2_{region}.csv"
        subprocess.call(cat_cmd,shell=True)
    print("Merged run2 data")

def check_mc(dataset,year):
    #Returns a list of arguments to pass to condor submission
    #If all files have been processed - returns an empty list
    args_to_write   = []
    jec_map         = {0:"nom",1:"jes_up",2:"jes_down",3:"jer_up",4:"jer_down",5:"jms_up",6:"jms_down",7:"jmr_up",8:"jmr_down"}
    mc_no_sys = False
    if "qcd" in dataset.lower():
        mc_no_sys = True

    for jec_code in range(9):
        if mc_no_sys and jec_code>0:
            continue
        temp_args   = []
        jec         = jec_map[jec_code]
        final_file         = f"output/{dataset}_{year}_SR_Pass_{jec}.csv"
        final_merged_file  = f"merged_output/{dataset}_{year}_SR_Pass_{jec}.csv"

        if os.path.exists(final_merged_file):
            check_other_regions(final_merged_file)
            print(f"{dataset} {year} {jec} processed, continuing")
            continue


        #We assume that only 1 job (per jec) for MC so no merging is needed, we just move the files
        if os.path.exists(final_file):
            check_other_regions(final_file)
            mv_cmd = f"mv output/{dataset}_{year}*{jec}.csv merged_output/. 2>/dev/null"
            subprocess.call(mv_cmd,shell=True)
            print(f"{dataset} {year} {jec} processed, continuing")
            continue
        
        n_jobs = datasets_n_jobs[year][dataset]
        assert n_jobs==1, "n_jobs for MC is not 1"
        i = 0
        temp_args.append(f"{dataset} {year} {i} {n_jobs} {jec_code}\n") 
        
        if temp_args:
            args_to_write.extend(temp_args)
    
    if args_to_write:        
        print("{} jobs to send".format(len(args_to_write)))
    return args_to_write


def check_data(dataset,year):
    #Returns a list of arguments to pass to condor submission
    #If all files have been processed - returns an empty list
    final_file = f"merged_output/{dataset}_{year}_SR_Pass.csv"
    #Check for merged file
    temp_args = []
    if os.path.exists(final_file):
        check_other_regions(final_file)
        print(f"{dataset} {year} processed and merged, continuing")
        move_individual_files(dataset,year)
        return temp_args
    
    n_jobs = datasets_n_jobs[year][dataset]

    #Check for individual files
    for i in range(n_jobs):
        filename = f"output/{dataset}_{year}_SR_Pass_{i}_{n_jobs}.csv"
        if os.path.exists(filename):
            check_other_regions(filename)
        else:
            temp_args.append(f"{dataset} {year} {i} {n_jobs} 0\n")#0 is for nominal JEC 
    
    if temp_args:
        print("{} jobs to send".format(len(temp_args)))
    else:
        print("Merging csvs")
        merge_csvs(dataset,year,n_jobs)

    return temp_args

args_to_write = []
#for year in datasets_n_jobs:
for year in ["2016APV","2016","2017","2018",]:
    for dataset in datasets_n_jobs[year]:
        print("-----------")
        print(dataset, year)

        if "JetHT" in dataset:
            temp_args = check_data(dataset,year)
        else:
            temp_args = check_mc(dataset,year)

        if not temp_args:
            continue
        else:
            args_to_write.extend(temp_args)      

    merge_data(year)
merge_run2_data()
print(len(args_to_write))
write_arguments(args_to_write)
