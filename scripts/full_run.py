import sys
import os
sys.path.append('..')
from utils.TrainingUtils import *
from create_model_ensemble import *
from classifier_selection import *
import subprocess
import h5py
import time

def check_all_models_there(model_dir, num_models):
    #TODO Fix it so there aren't Nan's...
    print("Checking %s" % model_dir)
    missing_models = []
    files = os.listdir(model_dir)
    for i in range(num_models):
        model_name = "model%i.h5" % i
        if(model_name not in files):
            print("Missing %s " % model_name)
            missing_models.append(i)

    if(len(missing_models) == num_models):
        print("Missing all models! Something wrong in training?? This is bad !!!")
        sys.exit(1)
    else:
        for i in missing_models:
            cpy_i = (i + 1) % num_models
            for idx in range(num_models):
                if(cpy_i not in missing_models): break
                else:
                    cpy_i = (cpy_i +1) % num_models

            cpy_name = "model%i.h5" % cpy_i
            dest_name = "model%i.h5" % i
            cpy_cmd = "cp %s %s" % (model_dir + cpy_name, model_dir + dest_name)
            print("Copying : " + cpy_cmd)
            os.system(cpy_cmd)








def full_run(options):

    if(options.output[-1] != '/'):
        options.output += '/'

    if(not os.path.exists(options.output)):
        subprocess.call("mkdir %s" % options.output, shell = True)

    if(options.reload):
        if(not os.path.exists(options.output + "run_opts.pkl")):
            print("Reload options specified but file %s doesn't exist. Exiting" % (options.output+"run_opts.pkl"))
            sys.exit(1)
        else:
            rel_opts = get_options_from_pkl(options.output + "run_opts.pkl")
            rel_opts.step = options.step
            if(len(options.effs) >0): rel_opts.effs = options.effs
            if(options.sig_per_batch >= 0): rel_opts.sig_per_batch = options.sig_per_batch
            if(options.counting_fit): rel_opts.counting_fit = True
            else: rel_opts.counting_fit = False
            rel_opts.condor = options.condor
            rel_opts.keep_LSF = options.keep_LSF #quick fix
            rel_opts.redo_roc = options.redo_roc #quick fix
            rel_opts.output = options.output #allows renaming / moving directories
            options = rel_opts
    else:
        #save options
        options_dict = options.__dict__
        write_options_to_pkl(options_dict, options.output + "run_opts.pkl", write_mode = "xb" )


 
    print("Condor %i" % options.condor)


    if(options.numBatches % options.kfolds != 0):
        print("Number of batches (%i) must be multiple of number of kfolds (%i)" % (options.numBatches, options.kfolds))
        sys.exit(1)

    ksize = options.numBatches // options.kfolds

    batches_per_kfold = (options.kfolds -1 ) * ksize
    if(batches_per_kfold % options.lfolds !=0):
        print("Number of batches per kfold(%i) must be multiple of number of lfolds (%i)" % (batches_per_kfold, options.lfolds))
        sys.exit(1)

    if(options.step not in ["train", "get", "select", "merge", "fit", "roc", "all"]):
        print("Invalid option %s" % options.step)
        sys.exit(1)

    #parse what to do 
    get_condor = do_train = do_merge = do_selection = do_fit = False
    do_train = options.step == "train"
    get_condor = options.step == "get"
    do_selection = options.step == "select"
    do_merge = options.step == "merge"
    do_fit = options.step == "fit"
    do_roc = options.step == "roc"
    if(options.step == "all"):
        do_train = do_selection = do_fit = do_roc = True
    if(options.step == "roc" and options.condor):
        do_merge = True

    get_condor = get_condor or (do_selection and options.condor)
    do_merge = do_merge or do_fit


    options.num_val_batch = batches_per_kfold // options.lfolds

    total_batch_list = list(range(options.numBatches))

    base_path = os.path.abspath(".") + "/"

    start_time = time.time()
    kfold_options = []

    for k in range(options.kfolds):

        k_options = copy.deepcopy(options)
        k_list = copy.copy(total_batch_list)

        k_options.holdouts = list(range(k* ksize, (k+1) * ksize))

        for to_remove in k_options.holdouts:
            k_list.remove(to_remove)


        k_options.data_batch_list = k_list

        kfold_options += [k_options]

    #Do trainings
    if(do_train):
        for k,k_options in enumerate(kfold_options):
            if(not options.randsort):
                k_options.label = options.label + "_j1_kfold%i" % k
                k_options.output = options.output + "j1_kfold%i/" % k
                k_options.training_j = 1
                create_model_ensemble(k_options)

                k_options.label = options.label + "_j2_kfold%i" % k
                k_options.output = options.output + "j2_kfold%i/" % k
                k_options.training_j = 2
                create_model_ensemble(k_options)
            else:
                k_options.label = options.label + "_jrand_kfold%i" % k
                k_options.output = options.output + "jrand_kfold%i/" % k
                k_options.training_j = 1
                create_model_ensemble(k_options)




    #get all the condor models
    if(get_condor and options.condor):
        for k,k_options in enumerate(kfold_options):

                c_opts = condor_options().parse_args([])
                c_opts.getEOS = True

                if(not options.randsort):
                    #c_opts.name = "j1_kfold%i" % k
                    c_opts.name = options.label + "_j1_kfold%i" % k
                    c_opts.outdir = options.output + "j1_kfold%i/" % k
                    if( not os.path.exists(c_opts.outdir)): os.system("mkdir %s" % c_opts.outdir)
                    doCondor(c_opts)
                    #c_opts.name = "j2_kfold%i" % k
                    c_opts.name = options.label + "_j2_kfold%i" % k
                    c_opts.outdir = options.output + "j2_kfold%i/" % k
                    if( not os.path.exists(c_opts.outdir)): os.system("mkdir %s" % c_opts.outdir)
                    doCondor(c_opts)
                else:
                    c_opts.name = options.label + "_jrand_kfold%i" % k
                    c_opts.outdir = options.output + "jrand_kfold%i/" % k
                    if( not os.path.exists(c_opts.outdir)): os.system("mkdir %s" % c_opts.outdir)
                    doCondor(c_opts)

                

    #select events
    if(do_selection):
        for k,k_options in enumerate(kfold_options):
            selection_options = copy.deepcopy(k_options)
            selection_options.data_batch_list = k_options.holdouts
            selection_options.val_batch_list = None
            selection_options.num_models = options.lfolds

            if(not options.randsort): 
                selection_options.labeler_name = k_options.output + "{j_label}_kfold%i/" % k
                check_all_models_there(selection_options.labeler_name.format(j_label = "j1"), selection_options.num_models)
                check_all_models_there(selection_options.labeler_name.format(j_label = "j2"), selection_options.num_models)
            else: 
                selection_options.labeler_name = k_options.output + "jrand_kfold%i/" % k
                check_all_models_there(selection_options.labeler_name, selection_options.num_models)

            selection_options.output = k_options.output + "fit_inputs_kfold%i_eff{eff}.h5" % k
            selection_options.do_roc = True

            if((not options.condor)): #run selection locally
                classifier_selection(selection_options)

            else: #submit to condor
                selection_options.output = "fit_inputs_kfold%i_eff{eff}.h5" % k
                selection_options.local_storage = True
                selection_options.fin = "../data/BB/"
                selection_options_dict = selection_options.__dict__
                selection_opts_fname  = options.output + "select_opts_%i.pkl" % k
                write_options_to_pkl(selection_options_dict,  selection_opts_fname)


                condor_dir = options.output + "selection_condor_jobs/"
                if( not os.path.exists(condor_dir)): os.system("mkdir %s" % condor_dir)
                c_opts = condor_options().parse_args([])
                c_opts.nJobs = 1
                c_opts.outdir = condor_dir

                base_script = "../condor/scripts/select_from_pkl.sh"
                select_script = condor_dir + "select%i_script.sh" % k 

                os.system("cp %s %s" % (base_script, select_script))
                os.system("sed -i s/BSTART/%i/g %s" % (selection_options.data_batch_list[0], select_script))
                os.system("sed -i s/BSTOP/%i/g %s" % (selection_options.data_batch_list[-1] + 1, select_script))
                f_select_script = open(select_script, "a")

                for eff in options.effs:
                    f_select_script.write("xrdcp -f %s ${1}" % selection_options.output.format(eff=eff))

                f_select_script.write("xrdcp -f %s ${1}" % selection_options.output.format(eff=options.effs[0]).replace(".h5", "_eff.npz"))


                os.system("sed -i s/KFOLDNUM/%i/g %s" % (k, select_script))
                c_opts.script = select_script

                c_opts.name = options.label + "_select_kfold%i" % k 
                c_opts.sub = True
                #c_opts.sub = False

                #tar models together
                tarname = options.output + "models.tar"
                print(tarname)
                os.system("tar -cf %s %s --exclude=*/condor_jobs/*" %(tarname, options.output + "j*/"))

                inputs_list = [selection_opts_fname, tarname]
                c_opts.input = inputs_list


                doCondor(c_opts)



    if(do_merge):

        if(options.condor):
            for k,k_options in enumerate(kfold_options):

                c_opts = condor_options().parse_args([])
                c_opts.getEOS = True
                c_opts.outdir = options.output
                c_opts.name = options.label + "_select_kfold%i" % k 
                doCondor(c_opts)

        #merge selections
        for eff in effs:
            fit_inputs = options.output + "fit_inputs_eff{eff}.h5".format(eff = eff)
            merge_cmd = "python ../../CASEUtils/H5_maker/H5_merge.py %s "  % fit_inputs
            for k,k_options in enumerate(kfold_options):
                merge_cmd += k_options.output + "fit_inputs_kfold{k}_eff{eff}.h5 ".format(k = k, eff = eff)

        print("Merge cmd: " + merge_cmd)
        subprocess.call(merge_cmd ,shell = True)


    if(do_fit):




        #Do fit
        counting_str = ""
        if(options.counting_fit):
            counting_str = "_counting"
        for eff in effs:
            fit_inputs = options.output + "fit_inputs_eff{eff}.h5".format(eff = eff)
            fit_cmd = ("cd ../fitting; source deactivate;" 
                      "eval `scramv1 runtime -sh`; python dijetfit%s.py -i %s -p %s; cd -;"
                      "source deactivate; source activate mlenv0" % 
                      ( counting_str, base_path + fit_inputs, base_path + options.output))
            print(fit_cmd)
            subprocess.call(fit_cmd,  shell = True, executable = '/bin/bash')

    stop_time = time.time()
    print("Total time taken was %s" % ( stop_time - start_time))


    #merge different selections

    if(do_roc):
        sig_effs = []
        bkg_effs = []
        labels = [ "kfold %i" % k for  k in range(options.kfolds)]
        colors = ["g", "b", "r", "gray", "purple", "pink", "orange", "m", "skyblue", "yellow"]
        for k,k_options in enumerate(kfold_options):
            np_fname = options.output + "fit_inputs_kfold{k}_eff{eff}_effs.npz".format(k=k, eff = options.effs[0])
            np_file = np.load(np_fname)
            sig_eff = np.clip(np_file["sig_eff"], 1e-6, 1.)
            bkg_eff = np.clip(np_file["bkg_eff"], 1e-6, 1.)
            roc_label = ""
            if(options.redo_roc):
                print("Recomputing roc")
                j1_qs = np_file['j1_quantiles']
                j2_qs = np_file['j2_quantiles']
                Y = np_file['Y']
                sig_eff = []
                bkg_eff = []
                n_points = 200.
                roc_label = "_max"
                qcd_only = Y > -0.1
                #scores = np.minimum(j1_qs,j2_qs)
                scores = np.maximum(j1_qs,j2_qs)
                #scores = j1_qs*j2_qs
                bkg_eff, sig_eff, thresholds = roc_curve(Y[qcd_only], scores[qcd_only], drop_intermediate = True)
                print(sig_eff.shape)

                #for perc in np.arange(0., 1., 1./n_points):
                #    mask = (j1_qs > perc) & (j2_qs > perc)
                #    sig_eff_ = np.mean(mask & (Y ==1)) / np.mean(Y == 1)
                #    bkg_eff_ = np.mean(mask & (Y ==0)) / np.mean(Y == 0)

                #    sig_eff.append(sig_eff_)
                #    bkg_eff.append(bkg_eff_)

                sig_eff = np.clip(sig_eff, 1e-6, 1.)
                bkg_eff = np.clip(bkg_eff, 1e-6, 1.)

            
            sig_effs.append(sig_eff)
            bkg_effs.append(bkg_eff)

        sic_fname = options.output + options.label + roc_label + "_sic.png"
        roc_fname = options.output + options.label + roc_label + "_roc.png"
        make_sic_plot(sig_effs, bkg_effs, colors = colors, labels = labels, fname = sic_fname)
        make_roc_plot(sig_effs, bkg_effs, colors = colors, labels = labels, fname = roc_fname)


if(__name__ == "__main__"):
    parser = input_options()
    parser.add_argument("--effs", nargs="+", default = [], type = float)
    parser.add_argument("--kfolds", default = 5, type = int)
    parser.add_argument("--lfolds", default = 4, type = int)
    parser.add_argument("--numBatches", default = 40, type = int)
    parser.add_argument("--do_TNT",  default=False, action = 'store_true',  help="Use TNT (default cwola)")
    parser.add_argument("--condor", dest = 'condor', action = 'store_true')
    parser.add_argument("--no-condor", dest = 'condor', action = 'store_false')
    parser.set_defaults(condor=False)
    parser.add_argument("--step", default = "train",  help = 'Which step to perform (train, get, select, fit, roc, all)')
    parser.add_argument("--counting_fit", default = False,  action = 'store_true', help = 'Do counting version of dijet fit')
    parser.add_argument("--redo_roc", default = False,  action = 'store_true', help = 'Remake roc')
    parser.add_argument("--reload", action = 'store_true', help = "Reload based on previously saved options")
    parser.add_argument("--new", dest='reload', action = 'store_false', help = "Reload based on previously saved options")
    parser.set_defaults(reload=True)
    options = parser.parse_args()
    full_run(options)
